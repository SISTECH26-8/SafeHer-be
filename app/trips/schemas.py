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
    confidence: str

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
    confidence: str
    waypoints: List[Dict[str, float]]

class RecommendResponse(BaseModel):
    recommended_route_id: str
    evaluations: List[RouteEvaluation]
