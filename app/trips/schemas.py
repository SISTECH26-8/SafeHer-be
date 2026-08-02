from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any

class DestinationRiskRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    datetime: datetime

class DestinationRiskResponse(BaseModel):
    risk_score: float
    level: str
    color_indicator: str

class RouteRecommendRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lon: float = Field(..., ge=-180, le=180)
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lon: float = Field(..., ge=-180, le=180)
    datetime: datetime

class RouteEvaluation(BaseModel):
    route_id: str
    average_risk_score: float
    color_indicator: str
    status: str
    waypoints: List[Dict[str, float]]

class RecommendResponse(BaseModel):
    recommended_route_id: str
    evaluations: List[RouteEvaluation]

class TripStartRequest(BaseModel):
    route_id: str
    destination_lat: float = Field(..., ge=-90, le=90)
    destination_lon: float = Field(..., ge=-180, le=180)
    start_lat: float = Field(..., ge=-90, le=90)
    start_lon: float = Field(..., ge=-180, le=180)

class TripStartResponse(BaseModel):
    trip_id: str
    status: str

class TripTrackRequest(BaseModel):
    current_lat: float = Field(..., ge=-90, le=90)
    current_lon: float = Field(..., ge=-180, le=180)

class TripTrackResponse(BaseModel):
    is_safe: bool
    show_popup_alert: bool
    alert_message: str | None = None
    new_safe_route: RouteEvaluation | None = None
