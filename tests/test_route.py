import httpx
import json
from app.core.security import create_access_token

token = create_access_token('test-user-id')
headers = {'Authorization': f'Bearer {token}'}

payload = {
    'origin_lat': -6.1754,       # Monas
    'origin_lon': 106.8272,
    'destination_lat': -6.3606,  # Universitas Indonesia
    'destination_lon': 106.8285,
    'datetime': '2026-08-02T08:00:00Z'
}

print("Testing route..")
resp = httpx.post('http://localhost:8000/api/v1/trips/routes/recommend', headers=headers, json=payload, timeout=30.0)
print('Status:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print('Recommended Route:', data['recommended_route_id'])
    for eval in data['evaluations']:
        print(f"- {eval['route_id']}: Score={eval['average_risk_score']:.2f}, Indicator={eval['color_indicator']}, Status={eval['status']}")
else:
    print('Response:', resp.text)
