import httpx
import asyncio
import uuid
import sys
import os
import csv
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import SessionLocal
from app.safe_points.models import SafePoint

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUADRANTS = [
    "-6.8000, 106.3000, -6.3500, 106.8000",
    "-6.8000, 106.8000, -6.3500, 107.3000",
    "-6.3500, 106.3000, -5.9000, 106.8000",
    "-6.3500, 106.8000, -5.9000, 107.3000"
]

def get_overpass_query(bbox):
    return f"""
    [out:json][timeout:60];
    (
      node["amenity"="police"]({bbox});
      way["amenity"="police"]({bbox});
      node["amenity"="hospital"]({bbox});
      way["amenity"="hospital"]({bbox});
      node["amenity"="fuel"]({bbox});
      way["amenity"="fuel"]({bbox});
      node["shop"="convenience"]({bbox});
    );
    out center;
    """

async def fetch_osm_data_for_bbox(client, bbox, retries=3):
    print(f"Fetching data for BBOX: {bbox}...")
    for attempt in range(retries):
        try:
            response = await client.post(OVERPASS_URL, data={"data": get_overpass_query(bbox)})
            response.raise_for_status()
            return response.json().get("elements", [])
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 or e.response.status_code >= 500:
                print(f"  Attempt {attempt+1} failed ({e.response.status_code}). Retrying in 5s...")
                await asyncio.sleep(5)
            else:
                raise e
        except Exception as e:
            print(f"  Attempt {attempt+1} error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)
    return []

def map_osm_type_to_safe_type(element_tags: dict) -> str:
    amenity = element_tags.get("amenity")
    shop = element_tags.get("shop")
    if amenity == "police": return "POLICE_STATION"
    if amenity == "hospital": return "HOSPITAL"
    if amenity == "fuel": return "GAS_STATION"
    if shop == "convenience": return "MINIMARKET"
    return "UNKNOWN"

def parse_and_seed(db: Session, all_elements: list):
    print(f"\nTotal akumulasi {len(all_elements)} data mentah dari OSM.")
    
    safe_points_data = []
    seen_ids = set()
    
    for el in all_elements:
        el_id = el.get("id")
        if el_id in seen_ids:
            continue
        seen_ids.add(el_id)
        
        tags = el.get("tags", {})
        lat = el.get("lat") or (el.get("center", {}).get("lat"))
        lon = el.get("lon") or (el.get("center", {}).get("lon"))
        
        if not lat or not lon:
            continue
            
        sp_type = map_osm_type_to_safe_type(tags)
        if sp_type == "UNKNOWN":
            continue
            
        # FILTER KETAT MINIMARKET 24 JAM
        if sp_type == "MINIMARKET":
            if tags.get("opening_hours") != "24/7":
                continue
            
        name = tags.get("name", "Unknown Name")
        if name == "Unknown Name":
            name = f"{sp_type.replace('_', ' ').title()} Terdekat"
            
        phone = tags.get("phone") or tags.get("contact:phone", "")
        
        status = "Buka 24 Jam" if sp_type in ["POLICE_STATION", "HOSPITAL", "MINIMARKET"] else "Buka"
        if tags.get("opening_hours") == "24/7":
            status = "Buka 24 Jam"
            
        safe_points_data.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "type": sp_type,
            "lat": lat,
            "lon": lon,
            "status_lokasi": status,
            "contact_number": phone
        })
        
    print(f"Tersaring {len(safe_points_data)} Safe Points valid (tanpa duplikat, + filter 24 Jam).")
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "safe_points.csv")
    
    with open(csv_path, mode="w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "type", "lat", "lon", "status_lokasi", "contact_number"])
        writer.writeheader()
        writer.writerows(safe_points_data)
        
    print(f"Data diekspor ke CSV: {csv_path}")
    
    safe_points_to_insert = []
    for row in safe_points_data:
        geom = f"SRID=4326;POINT({row['lon']} {row['lat']})"
        safe_points_to_insert.append(SafePoint(
            id=row["id"], name=row["name"], type=row["type"],
            status_lokasi=row["status_lokasi"], contact_number=row["contact_number"], geom=geom
        ))
        
    db.query(SafePoint).delete()
    db.add_all(safe_points_to_insert)
    db.commit()
    print("Data berhasil di-seed ke Database PostGIS!")

async def main():
    all_elements = []
    headers = {"User-Agent": "SafeHer-App-Bot/1.0 (contact@safeher.app)"}
    async with httpx.AsyncClient(timeout=180.0, headers=headers) as client:
        for idx, bbox in enumerate(QUADRANTS):
            print(f"--- Processing Quadrant {idx+1}/4 ---")
            elements = await fetch_osm_data_for_bbox(client, bbox)
            all_elements.extend(elements)
            await asyncio.sleep(2) # be nice to overpass api
            
    db = SessionLocal()
    parse_and_seed(db, all_elements)
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
