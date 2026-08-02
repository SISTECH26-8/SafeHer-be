from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db, get_current_user_id
from app.safe_points import schemas, services
from app.core.config import settings

router = APIRouter(prefix="/safe-points", tags=["Safe Points"])

@router.get("", response_model=List[schemas.SafePointResponse])
def get_safe_points(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(settings.SAFE_POINT_DEFAULT_RADIUS_KM, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id)
):
    """
    Mengambil daftar titik aman di sekitar lokasi (radius_km).
    """
    return services.get_safe_points_in_radius(
        db=db,
        lat=lat,
        lon=lon,
        radius_km=radius_km
    )
