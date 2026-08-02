from sqlalchemy.orm import Session
from sqlalchemy import func
from geoalchemy2 import Geography
from typing import List

from app.safe_points import schemas
from app.safe_points.models import SafePoint

def get_safe_points_in_radius(db: Session, lat: float, lon: float, radius_km: float) -> List[schemas.SafePointResponse]:
    if radius_km <= 0:
        return []
        
    radius_m = radius_km * 1000
    point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
    
    # Use Geography cast to calculate distance in meters
    query_results = db.query(
        SafePoint, 
        func.ST_X(SafePoint.geom).label("lon"), 
        func.ST_Y(SafePoint.geom).label("lat")
    ).filter(
        func.ST_DWithin(
            func.cast(SafePoint.geom, Geography),
            func.cast(point, Geography),
            radius_m
        )
    ).all()
    
    response = []
    for sp, sp_lon, sp_lat in query_results:
        response.append(schemas.SafePointResponse(
            safe_id=sp.id,
            name=sp.name,
            type=sp.type,
            lat=sp_lat,
            lon=sp_lon,
            status_lokasi=sp.status_lokasi,
            contact_number=sp.contact_number
        ))
        
    return response
