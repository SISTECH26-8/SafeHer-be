import httpx
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Any, List, Dict
import json
import uuid

from app.core.config import settings
from app.core import exceptions as exc
from app.trips import schemas
from app.ml.predictor import predict_risk_score, predict_batch, score_to_level
from app.ml.geo_mock import mock_route_to_chicago
from geoalchemy2 import Geography
from app.system.models import MLPredictionLog
from app.trips.models import Trip
from app.reports.models import Report
from app.db.redis_client import get_redis_client
from sqlalchemy import func
from datetime import datetime
import math
from fastapi import BackgroundTasks

def _create_ml_log(db: Session, source: str, inputs: dict, predicted_score: float):
    log = MLPredictionLog(
        request_id=uuid.uuid4(),
        model_version=settings.MODEL_VERSION,
        source=source,
        inputs=inputs,
        predicted_score=predicted_score
    )
    db.add(log)
    db.commit()

def get_destination_risk(db: Session, background_tasks: BackgroundTasks, model: Any, req: schemas.DestinationRiskRequest) -> schemas.DestinationRiskResponse:
    score = predict_risk_score(model, req.lat, req.lon, req.datetime)
    level, color = score_to_level(score)
    
    mocked = mock_route_to_chicago([(req.lat, req.lon)])
    mock_lat, mock_lon = mocked[0] if mocked else (None, None)
    
    background_tasks.add_task(
        _create_ml_log,
        db=db,
        source="live_destination",
        inputs={
            "original_lat": req.lat,
            "original_lon": req.lon,
            "mock_lat": mock_lat,
            "mock_lon": mock_lon,
            "datetime": req.datetime.isoformat()
        },
        predicted_score=score
    )
    
    return schemas.DestinationRiskResponse(
        risk_score=score,
        level=level,
        color_indicator=color
    )

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=4))
async def _fetch_mapbox_routes(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> dict:
    url = f"{settings.MAPBOX_BASE_URL}/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "true",
        "access_token": settings.MAPBOX_API_KEY
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=settings.MAPBOX_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise exc.external_api_error(f"Gagal menghubungi Mapbox: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise exc.external_api_error(f"Mapbox error status {e.response.status_code}")

def _sample_waypoints(coordinates: List[List[float]], step: int = 5) -> List[Dict[str, float]]:
    # Mapbox returns coordinates as [lon, lat] (GeoJSON format)
    # We sample every 'step' points to reduce prediction overhead, but keep the first and last
    if not coordinates:
        return []
    
    sampled = []
    for i in range(0, len(coordinates), step):
        lon, lat = coordinates[i]
        sampled.append({"lat": lat, "lon": lon})
        
    # Ensure destination is always included
    last_lon, last_lat = coordinates[-1]
    if sampled[-1]["lat"] != last_lat or sampled[-1]["lon"] != last_lon:
        sampled.append({"lat": last_lat, "lon": last_lon})
        
    return sampled

async def recommend_safe_routes(db: Session, background_tasks: BackgroundTasks, model: Any, req: schemas.RouteRecommendRequest) -> schemas.RecommendResponse:
    if req.origin_lat == req.destination_lat and req.origin_lon == req.destination_lon:
        raise exc.validation_error("Origin dan destination tidak boleh sama")
        
    mapbox_data = await _fetch_mapbox_routes(req.origin_lat, req.origin_lon, req.destination_lat, req.destination_lon)
    
    routes = mapbox_data.get("routes", [])
    if not routes:
        raise exc.external_api_error("Mapbox tidak mengembalikan rute yang valid")
        
    evaluations = []
    
    for idx, route in enumerate(routes):
        geometry = route.get("geometry", {})
        coords = geometry.get("coordinates", [])
        duration = route.get("duration", 0)
        
        if not coords:
            continue
            
        sampled = _sample_waypoints(coords, step=10) # Adjust step as needed
        waypoints_tuples = [(pt["lat"], pt["lon"]) for pt in sampled]
        
        # Batch Predict
        scores = predict_batch(model, waypoints_tuples, req.datetime)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        level, color = score_to_level(avg_score)
        
        status = "Aman dilalui" if color == "GREEN" else "Berhati-hati" if color == "YELLOW" else "Berisiko Tinggi"
        route_id = f"route_{idx+1}"
        
        # Log to DB
        mocked_coords = mock_route_to_chicago(waypoints_tuples)
        background_tasks.add_task(
            _create_ml_log,
            db=db,
            source="route_recommend",
            inputs={
                "route_id": route_id,
                "original_waypoints": waypoints_tuples,
                "mock_waypoints": mocked_coords,
                "datetime": req.datetime.isoformat()
            },
            predicted_score=avg_score
        )
        
        # We must return FULL waypoints to frontend (not sampled), as per API contract?
        # The contract says: "waypoints: [{lat, lon}] - koordinat ASLI dari Mapbox"
        # It's better to return the full geometry or sampled? 
        # Usually frontend needs full coordinates to draw the polyline.
        full_waypoints = [{"lat": lat, "lon": lon} for lon, lat in coords]
        
        evaluations.append({
            "route_id": route_id,
            "average_risk_score": avg_score,
            "color_indicator": color,
            "status": status,
            "waypoints": full_waypoints,
            "_duration": duration # hidden tie-breaker
        })
        
    if not evaluations:
        raise exc.external_api_error("Gagal mengevaluasi rute dari Mapbox")
        
    # Tie-breaker logic: sort by (average_risk_score ASC, _duration ASC)
    evaluations.sort(key=lambda x: (x["average_risk_score"], x["_duration"]))
    
    recommended_route_id = evaluations[0]["route_id"]
    
    # Remove _duration from final output to match schema
    final_evals = []
    for ev in evaluations:
        ev_copy = ev.copy()
        del ev_copy["_duration"]
        final_evals.append(schemas.RouteEvaluation(**ev_copy))
        
    return schemas.RecommendResponse(
        recommended_route_id=recommended_route_id,
        evaluations=final_evals
    )

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000 # Radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def start_trip(db: Session, user_id: str, req: schemas.TripStartRequest) -> schemas.TripStartResponse:
    trip = Trip(
        user_id=user_id,
        route_id=req.route_id,
        start_geom=f"SRID=4326;POINT({req.start_lon} {req.start_lat})",
        destination_geom=f"SRID=4326;POINT({req.destination_lon} {req.destination_lat})",
        status="ACTIVE"
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    return schemas.TripStartResponse(trip_id=str(trip.id), status=trip.status)

async def track_trip(db: Session, user_id: str, trip_id: str, req: schemas.TripTrackRequest, model: Any) -> schemas.TripTrackResponse:
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise exc.trip_not_found()
    if trip.status == "COMPLETED":
        raise exc.trip_not_found()
    if str(trip.user_id) != user_id:
        raise exc.access_denied()
        
    redis = get_redis_client()
    pos_key = f"trip:{trip_id}:last_position"
    now_ts = datetime.utcnow().timestamp()
    
    last_pos_str = redis.get(pos_key)
    if last_pos_str:
        last_pos = json.loads(last_pos_str)
        dist = _haversine(last_pos["lat"], last_pos["lon"], req.current_lat, req.current_lon)
        time_diff = now_ts - last_pos["ts"]
        
        # GPS Jump anomaly check (>2km in <10s)
        if dist > 2000 and time_diff < 10:
            return schemas.TripTrackResponse(
                is_safe=True, 
                show_popup_alert=False, 
                alert_message="Abaikan: Anomali GPS (Lonjakan terdeteksi)"
            )
            
    redis.setex(pos_key, settings.REDIS_SOS_TTL_SECONDS, json.dumps({
        "lat": req.current_lat, 
        "lon": req.current_lon, 
        "ts": now_ts
    }))
    
    # Convert to geography to use exact meters for distance (300 meters)
    reports_count = db.query(Report).filter(
        Report.created_at > trip.created_at,
        func.ST_DWithin(
            func.cast(Report.geom, type_=Geography),
            func.cast(func.ST_SetSRID(func.ST_MakePoint(req.current_lon, req.current_lat), 4326), type_=Geography),
            300
        )
    ).count()
    
    # Reroute hanya di-trigger jika ada anonymous reporting (user report)
    if reports_count > 0:
        alert_key = f"last_alert_at:{trip_id}"
        if not redis.get(alert_key):
            redis.setex(alert_key, 60, "1")
            
            # Fetch Mapbox alternatives to destination
            dest_pt = db.query(func.ST_Y(trip.destination_geom), func.ST_X(trip.destination_geom)).first()
            if dest_pt and dest_pt[0] and dest_pt[1]:
                dest_lat, dest_lon = dest_pt[0], dest_pt[1]
                mapbox_data = await _fetch_mapbox_routes(req.current_lat, req.current_lon, dest_lat, dest_lon)
                routes = mapbox_data.get("routes", [])
                
                evaluations = []
                for idx, route in enumerate(routes):
                    coords = route.get("geometry", {}).get("coordinates", [])
                    if not coords: continue
                    sampled = _sample_waypoints(coords, step=10)
                    scores = predict_batch(model, [(pt["lat"], pt["lon"]) for pt in sampled], datetime.utcnow())
                    avg = sum(scores)/len(scores) if scores else 0
                    lvl, col = score_to_level(avg)
                    evaluations.append({
                        "route_id": f"reroute_{idx+1}",
                        "average_risk_score": avg,
                        "color_indicator": col,
                        "status": "Aman dilalui" if col == "GREEN" else "Berhati-hati",
                        "waypoints": [{"lat": c[1], "lon": c[0]} for c in coords]
                    })
                
                safe_routes = [e for e in evaluations if e["color_indicator"] in ["GREEN", "YELLOW"]]
                if safe_routes:
                    safe_routes.sort(key=lambda x: x["average_risk_score"])
                    best_route = schemas.RouteEvaluation(**safe_routes[0])
                    return schemas.TripTrackResponse(
                        is_safe=False,
                        show_popup_alert=True,
                        alert_message="Bahaya terdeteksi di depan! Mengalihkan ke rute yang lebih aman.",
                        new_safe_route=best_route
                    )
            
            return schemas.TripTrackResponse(
                is_safe=False,
                show_popup_alert=True,
                alert_message="Bahaya terdeteksi, namun tidak ada rute alternatif aman. Segera cari Safe Point terdekat!"
            )
            
    return schemas.TripTrackResponse(is_safe=True, show_popup_alert=False)

def end_trip(db: Session, user_id: str, trip_id: str):
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise exc.trip_not_found()
    if str(trip.user_id) != user_id:
        raise exc.access_denied()
        
    trip.status = "COMPLETED"
    trip.ended_at = func.now()
    db.commit()
    
    redis = get_redis_client()
    redis.delete(f"trip:{trip_id}:last_position")
    redis.delete(f"last_alert_at:{trip_id}")
    return {"message": "Trip berhasil diakhiri"}
