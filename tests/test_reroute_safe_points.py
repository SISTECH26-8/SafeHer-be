import httpx
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.users.models import User
from app.reports.models import Report
from app.trips.models import Trip
from app.emergency.models import SOSSession

# Get valid user
db = SessionLocal()
user = db.query(User).first()
if not user:
    print("No user found in DB. Exiting.")
    exit(1)

token = create_access_token(str(user.id))
headers = {'Authorization': f'Bearer {token}'}

def print_separator(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

# 1. Test Safe Points
print_separator("1. TEST SAFE POINTS")
safe_points_url = "http://localhost:8000/api/v1/safe-points?lat=-6.3606&lon=106.8285&radius_km=5"
resp_sp = httpx.get(safe_points_url, headers=headers, timeout=60.0)
print(f"Status: {resp_sp.status_code}")
if resp_sp.status_code == 200:
    data_sp = resp_sp.json()
    print(f"Found {len(data_sp)} safe points within 5km of Universitas Indonesia.")
    if len(data_sp) > 0:
        print(f"Sample: {data_sp[0]['name']} ({data_sp[0]['type']}) at {data_sp[0]['lat']}, {data_sp[0]['lon']}")
else:
    print(resp_sp.text)

# 2. Test Reroute (by creating a mock report)
print_separator("2. TEST REROUTE")

# a. Start Trip
payload_start = {
    "route_id": "route_1",
    "start_lat": -6.1754,
    "start_lon": 106.8272,
    "destination_lat": -6.3606,
    "destination_lon": 106.8285
}
resp_start = httpx.post('http://localhost:8000/api/v1/trips/start', headers=headers, json=payload_start, timeout=30.0)
if resp_start.status_code not in [200, 201]:
    print("Failed to start trip.")
    print(resp_start.text)
    exit(1)

trip_id = resp_start.json().get('trip_id')
print(f"Started Trip ID: {trip_id}")

# Wait a bit to ensure Postgres time > Trip.created_at
import time
time.sleep(2)

# b. Insert anonymous report at current track location
track_lat = -6.1764
track_lon = 106.8275

from datetime import datetime, timedelta

print(f"Mocking a recent Report at {track_lat}, {track_lon}...")
future_time = datetime.utcnow() + timedelta(minutes=5)
mock_report = Report(
    category="TINDAK_KRIMINAL",
    description="Mock report for testing reroute",
    geom=f"SRID=4326;POINT({track_lon} {track_lat})",
    created_at=future_time
)
db.add(mock_report)
db.commit()

# c. Track trip exactly near the report!
payload_track = {
    "current_lat": track_lat,
    "current_lon": track_lon
}
resp_track = httpx.patch(f'http://localhost:8000/api/v1/trips/{trip_id}/track', headers=headers, json=payload_track, timeout=60.0)
print(f"Track Status: {resp_track.status_code}")
if resp_track.status_code == 200:
    data_track = resp_track.json()
    print(f"Is Safe: {data_track.get('is_safe')}")
    print(f"Popup Alert: {data_track.get('show_popup_alert')}")
    print(f"Alert Message: {data_track.get('alert_message')}")
    
    new_route = data_track.get('new_safe_route')
    if new_route:
        print(f"REROUTE TRIGGERED! New Route ID: {new_route['route_id']}, Score: {new_route['average_risk_score']}")
    else:
        print("NO REROUTE TRIGGERED.")
else:
    print(resp_track.text)

# d. Cleanup mock report and trip
db.delete(mock_report)
trip = db.query(Trip).filter(Trip.id == trip_id).first()
if trip:
    db.delete(trip)
db.commit()
db.close()
print("\nCleanup complete.")
