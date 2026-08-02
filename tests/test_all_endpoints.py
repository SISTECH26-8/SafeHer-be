import httpx
import json
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.users.models import User
from app.trips.models import Trip
from app.emergency.models import SOSSession

# Get a valid user from DB
db = SessionLocal()
user = db.query(User).first()
db.close()

if not user:
    print("No user found in DB to test. Exiting.")
    exit(1)

token = create_access_token(str(user.id))
headers = {'Authorization': f'Bearer {token}'}

def print_separator(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

# 1. Recommendation
print_separator("1. GET ROUTE RECOMMENDATION")
payload_rec = {
    'origin_lat': -6.1754,       # Monas
    'origin_lon': 106.8272,
    'destination_lat': -6.3606,  # Universitas Indonesia
    'destination_lon': 106.8285,
    'datetime': '2026-08-02T20:00:00Z'
}
resp_rec = httpx.post('http://localhost:8000/api/v1/trips/routes/recommend', headers=headers, json=payload_rec, timeout=30.0)
print(f"Status: {resp_rec.status_code}")
route_id = ""
if resp_rec.status_code == 200:
    data_rec = resp_rec.json()
    route_id = data_rec['recommended_route_id']
    print(f"Recommended Route ID: {route_id}")
    for ev in data_rec['evaluations']:
        print(f"Route {ev['route_id']} -> Score: {ev['average_risk_score']:.2f}, Color: {ev['color_indicator']}")
else:
    print(resp_rec.text)

if not route_id:
    print("Cannot proceed without route_id. Exiting.")
    exit(1)

# 2. Start Trip
print_separator("2. START TRIP")
payload_start = {
    "route_id": route_id,
    "start_lat": -6.1754,
    "start_lon": 106.8272,
    "destination_lat": -6.3606,
    "destination_lon": 106.8285
}
resp_start = httpx.post('http://localhost:8000/api/v1/trips/start', headers=headers, json=payload_start, timeout=30.0)
print(f"Status: {resp_start.status_code}")
trip_id = ""
if resp_start.status_code in [200, 201]:
    data_start = resp_start.json()
    trip_id = data_start.get('trip_id')
    print(f"Trip ID: {trip_id}, Status: {data_start.get('status')}")
else:
    print(resp_start.text)

if not trip_id:
    print("Cannot proceed without trip_id. Exiting.")
    exit(1)

# 3. Track Trip (Normal)
print_separator("3. TRACK TRIP (NORMAL MOVEMENT)")
payload_track = {
    "current_lat": -6.1764,
    "current_lon": 106.8275
}
resp_track = httpx.patch(f'http://localhost:8000/api/v1/trips/{trip_id}/track', headers=headers, json=payload_track, timeout=30.0)
print(f"Status: {resp_track.status_code}")
if resp_track.status_code == 200:
    data_track = resp_track.json()
    print(f"Is Safe: {data_track.get('is_safe')}")
    print(f"Popup Alert: {data_track.get('show_popup_alert')}")
    print(f"Message: {data_track.get('alert_message')}")
else:
    print(resp_track.text)

# 4. Track Trip (GPS JUMP)
print_separator("4. TRACK TRIP (GPS JUMP TRIGGER)")
# Sleep to ensure >1s timestamp difference
time.sleep(2)
payload_jump = {
    "current_lat": -6.3606,  # Instantly jumped 20km!
    "current_lon": 106.8285
}
resp_jump = httpx.patch(f'http://localhost:8000/api/v1/trips/{trip_id}/track', headers=headers, json=payload_jump, timeout=30.0)
print(f"Status: {resp_jump.status_code}")
if resp_jump.status_code == 200:
    data_jump = resp_jump.json()
    print(f"Is Safe: {data_jump.get('is_safe')}")
    print(f"Popup Alert: {data_jump.get('show_popup_alert')}")
    print(f"Message: {data_jump.get('alert_message')}")
else:
    print(resp_jump.text)

# 5. End Trip
print_separator("5. END TRIP")
resp_end = httpx.post(f'http://localhost:8000/api/v1/trips/{trip_id}/end', headers=headers, timeout=30.0)
print(f"Status: {resp_end.status_code}")
if resp_end.status_code == 200:
    print(f"Response: {resp_end.json()}")
else:
    print(resp_end.text)
