from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Any

from app.api.dependencies import get_db, get_current_user_id
from app.trips import schemas, services

router = APIRouter(prefix="/trips", tags=["Trips"])

def get_model(request: Request) -> Any:
    return request.app.state.model

@router.get("/destination-risk", response_model=schemas.DestinationRiskResponse)
def evaluate_destination_risk(
    request: Request,
    background_tasks: BackgroundTasks,
    req: schemas.DestinationRiskRequest = Depends(),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    model: Any = Depends(get_model)
):
    """
    Mengecek tingkat bahaya di titik tujuan yang diinput user sebelum merencanakan rute.
    """
    return services.get_destination_risk(
        db=db,
        background_tasks=background_tasks,
        model=model,
        req=req
    )

@router.post("/routes/recommend", response_model=schemas.RecommendResponse)
async def recommend_safe_routes(
    req: schemas.RouteRecommendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    model: Any = Depends(get_model)
):
    """
    Menerima titik awal dan tujuan, memanggil OSRM, dan mengevaluasi skor keamanan dengan ML.
    """
    return await services.recommend_safe_routes(
        db=db,
        background_tasks=background_tasks,
        model=model,
        req=req
    )

@router.post("/start", response_model=schemas.TripStartResponse, status_code=201)
def start_trip(
    req: schemas.TripStartRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Memulai navigasi rute aktif.
    """
    return services.start_trip(db=db, user_id=user_id, req=req)

@router.patch("/{trip_id}/track", response_model=schemas.TripTrackResponse)
async def track_trip(
    trip_id: str,
    req: schemas.TripTrackRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    model: Any = Depends(get_model)
):
    """
    Melacak posisi pengguna secara real-time dan mengevaluasi risiko ulang.
    """
    return await services.track_trip(db=db, background_tasks=background_tasks, user_id=user_id, trip_id=trip_id, req=req, model=model)

@router.post("/{trip_id}/end")
def end_trip(
    trip_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Mengakhiri navigasi trip.
    """
    return services.end_trip(db=db, user_id=user_id, trip_id=trip_id)
