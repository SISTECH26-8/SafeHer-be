"""
Full audit test against API Contract v1.1.
Hits every endpoint real, prints [OK]/[FAIL] per endpoint.
"""
import httpx, json, os, sys, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.users.models import User, EmergencyContact
from app.trips.models import Trip
from app.emergency.models import SOSSession
from app.reports.models import Report

BASE = "http://localhost:8000/api/v1"
db = SessionLocal()
user = db.query(User).first()
db.close()

if not user:
    print("No user in DB. Exiting.")
    sys.exit(1)

token = create_access_token(str(user.id))
auth = {"Authorization": f"Bearer {token}"}
results = {}

def req(method, path, body=None, params=None, headers=None, public=False, timeout=60):
    url = BASE + path
    h = headers if headers is not None else ({} if public else auth)
    kw = {"headers": h, "params": params, "timeout": timeout}
    if body is not None:
        kw["json"] = body
    return getattr(httpx, method)(url, **kw)

def check(label, r, expected):
    ok = r.status_code == expected
    print(f"  [{'OK  ' if ok else 'FAIL'}] {label} -> HTTP {r.status_code} (exp {expected})")
    if not ok:
        try:
            print(f"         {r.json()}")
        except Exception:
            print(f"         {r.text[:300]}")
    results[label] = ok
    return r

# ── 1. Register ──────────────────────────────────────────────────────────────
print("\n=== 1. POST /auth/register ===")
ts = int(time.time())
check("Register", req("post", "/auth/register", public=True, body={
    "full_name": "Audit Tester",
    "email": f"audit_{ts}@test.com",
    "password": "audit123",
    "phone_number": "08111222333"
}), 201)

# ── 2. Login (invalid creds) ─────────────────────────────────────────────────
print("\n=== 2. POST /auth/login ===")
check("Login (wrong pw)", req("post", "/auth/login", public=True, body={
    "email": user.email, "password": "wrongpassword"
}), 401)

# We use the JWT we already have from create_access_token (skip actual login test
# since we don't know the real password in test context)
print("  [SKIP] Login (valid) - skipped; using pre-generated JWT")

# ── 3. Add Emergency Contact ─────────────────────────────────────────────────
print("\n=== 3. POST /users/emergency-contacts ===")
r = check("Add Emergency Contact", req("post", "/users/emergency-contacts", body={
    "contact_name": "Audit Kontak",
    "phone_number": "08100000099",
    "relation": "Teman"
}), 201)
contact_id = r.json().get("contact_id") if r.status_code == 201 else None

# ── 4. Destination Risk ───────────────────────────────────────────────────────
print("\n=== 4. GET /trips/destination-risk ===")
r = check("Destination Risk", req("get", "/trips/destination-risk", params={
    "lat": -6.3606, "lon": 106.8285, "datetime": "2026-08-02T08:00:00Z"
}), 200)
if r.status_code == 200:
    d = r.json()
    print(f"         risk_score={d.get('risk_score')}, level={d.get('level')}, color={d.get('color_indicator')}")

# ── 5. Route Recommend ────────────────────────────────────────────────────────
print("\n=== 5. POST /trips/routes/recommend ===")
r = check("Route Recommend", req("post", "/trips/routes/recommend", body={
    "origin_lat": -6.1754, "origin_lon": 106.8272,
    "destination_lat": -6.3606, "destination_lon": 106.8285,
    "datetime": "2026-08-02T08:00:00Z"
}), 200)
route_id = None
if r.status_code == 200:
    route_id = r.json().get("recommended_route_id")
    print(f"         recommended_route_id={route_id}")

# ── 6. Safe Points ────────────────────────────────────────────────────────────
print("\n=== 6. GET /safe-points ===")
r = check("Safe Points", req("get", "/safe-points", params={
    "lat": -6.3606, "lon": 106.8285, "radius_km": 2
}), 200)
if r.status_code == 200:
    pts = r.json()
    print(f"         {len(pts)} safe points found")
    if pts:
        sp = pts[0]
        print(f"         Sample: id={sp.get('safe_id')}, name={sp.get('name')}, type={sp.get('type')}")

# ── 7. Start Trip ─────────────────────────────────────────────────────────────
print("\n=== 7. POST /trips/start ===")
r = check("Trip Start", req("post", "/trips/start", body={
    "route_id": route_id or "route_1",
    "start_lat": -6.1754, "start_lon": 106.8272,
    "destination_lat": -6.3606, "destination_lon": 106.8285
}), 201)
trip_id = r.json().get("trip_id") if r.status_code == 201 else None
if trip_id:
    print(f"         trip_id={trip_id}")

# ── 8. Track Trip ─────────────────────────────────────────────────────────────
print("\n=== 8. PATCH /trips/{id}/track ===")
if trip_id:
    r = check("Track Trip", req("patch", f"/trips/{trip_id}/track", body={
        "current_lat": -6.1764, "current_lon": 106.8275
    }), 200)
    if r.status_code == 200:
        d = r.json()
        print(f"         is_safe={d.get('is_safe')}, show_popup_alert={d.get('show_popup_alert')}")
else:
    print("  [SKIP] No trip_id")

# ── 9. Anonymous Report ───────────────────────────────────────────────────────
print("\n=== 9. POST /reports ===")
check("Anonymous Report", req("post", "/reports", body={
    "category": "TINDAK_KRIMINAL",
    "description": "Audit test report",
    "lat": -6.1764, "lon": 106.8275
}), 201)

# ── 10. SOS Trigger ───────────────────────────────────────────────────────────
print("\n=== 10. POST /emergency/sos ===")
r = check("SOS Trigger", req("post", "/emergency/sos", body={
    "current_lat": -6.3644, "current_lon": 106.8286
}), 201)
sos_id = None
if r.status_code == 201:
    d = r.json()
    sos_id = d.get("sos_session_id")
    print(f"         sos_session_id={sos_id}")
    print(f"         live_tracking_url={d.get('live_tracking_url')}")

# ── 11. SOS Location Update ───────────────────────────────────────────────────
print("\n=== 11. PATCH /emergency/sos/{id}/location ===")
if sos_id:
    r = check("SOS Location Update", req("patch", f"/emergency/sos/{sos_id}/location", body={
        "lat": -6.3650, "lon": 106.8290
    }), 200)
    if r.status_code == 200:
        print(f"         status={r.json().get('status')}")
else:
    print("  [SKIP] No sos_id")

# ── 12. SOS Track (PUBLIC) ────────────────────────────────────────────────────
print("\n=== 12. GET /emergency/sos/{id}/track (PUBLIC) ===")
if sos_id:
    r = check("SOS Track (public)", req("get", f"/emergency/sos/{sos_id}/track", public=True), 200)
    if r.status_code == 200:
        d = r.json()
        print(f"         user_name={d.get('user_name')}, status={d.get('status')}")
        print(f"         location={d.get('current_location')}")
else:
    print("  [SKIP] No sos_id")

# ── 13. End Trip ──────────────────────────────────────────────────────────────
print("\n=== 13. POST /trips/{id}/end ===")
if trip_id:
    r = check("Trip End", req("post", f"/trips/{trip_id}/end"), 200)
    if r.status_code == 200:
        print(f"         {r.json()}")
else:
    print("  [SKIP] No trip_id")

# ── 14. SOS End ───────────────────────────────────────────────────────────────
print("\n=== 14. POST /emergency/sos/{id}/end ===")
if sos_id:
    r = check("SOS End", req("post", f"/emergency/sos/{sos_id}/end"), 200)
    if r.status_code == 200:
        print(f"         {r.json()}")
else:
    print("  [SKIP] No sos_id")

# ── 15. List Emergency Contacts ───────────────────────────────────────────────
print("\n=== 15. GET /users/emergency-contacts ===")
r = check("List Emergency Contacts", req("get", "/users/emergency-contacts"), 200)
if r.status_code == 200:
    d = r.json()
    print(f"         {len(d.get('contacts', []))} contacts")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n\n========== AUDIT SUMMARY ==========")
total = len(results)
passed = sum(1 for v in results.values() if v)
for label, ok in results.items():
    print(f"  {'[OK]' if ok else '[X] '} {label}")
print(f"\n  RESULT: {passed}/{total} PASSED  |  {total - passed} FAILED")
