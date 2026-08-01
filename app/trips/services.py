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
from app.system.models import MLPredictionLog

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
    score, confidence = predict_risk_score(model, req.lat, req.lon, req.datetime)
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
        color_indicator=color,
        confidence=confidence
    )

@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=4))
async def _fetch_osrm_routes(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> dict:
    url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "alternatives": "true"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params, timeout=settings.OSRM_TIMEOUT_SECONDS)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise exc.external_api_error(f"Gagal menghubungi OSRM: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise exc.external_api_error(f"OSRM error status {e.response.status_code}")

def _sample_waypoints(coordinates: List[List[float]], step: int = 5) -> List[Dict[str, float]]:
    # OSRM returns coordinates as [lon, lat]
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
        
    osrm_data = await _fetch_osrm_routes(req.origin_lat, req.origin_lon, req.destination_lat, req.destination_lon)
    
    routes = osrm_data.get("routes", [])
    if not routes:
        raise exc.external_api_error("OSRM tidak mengembalikan rute yang valid")
        
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
        scores, confidences = predict_batch(model, waypoints_tuples, req.datetime)
        
        avg_score = sum(scores) / len(scores) if scores else 0
        level, color = score_to_level(avg_score)
        
        route_confidence = "High"
        if "Low" in confidences:
            route_confidence = "Low"
        elif "Medium" in confidences:
            route_confidence = "Medium"
        
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
        # The contract says: "waypoints: [{lat, lon}] - koordinat ASLI dari OSRM"
        # It's better to return the full geometry or sampled? 
        # Usually frontend needs full coordinates to draw the polyline.
        full_waypoints = [{"lat": lat, "lon": lon} for lon, lat in coords]
        
        evaluations.append({
            "route_id": route_id,
            "average_risk_score": avg_score,
            "color_indicator": color,
            "status": status,
            "confidence": route_confidence,
            "waypoints": full_waypoints,
            "_duration": duration # hidden tie-breaker
        })
        
    if not evaluations:
        raise exc.external_api_error("Gagal mengevaluasi rute dari OSRM")
        
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
