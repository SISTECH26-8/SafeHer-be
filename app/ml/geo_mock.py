from app.ml.geo_config import (
    ANCHOR_LAT, ANCHOR_LON, 
    BBOX_MIN_LAT, BBOX_MAX_LAT, 
    BBOX_MIN_LON, BBOX_MAX_LON
)

def _clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))

def _scale_if_out_of_bbox(delta_lat: float, delta_lon: float) -> tuple[float, float]:
    """
    Scales down the deltas proportionally if adding them to the anchor 
    would result in a coordinate outside the trained bounding box.
    """
    # Calculate the max allowed deltas in each direction from the anchor
    max_dlat_pos = BBOX_MAX_LAT - ANCHOR_LAT
    max_dlat_neg = ANCHOR_LAT - BBOX_MIN_LAT
    max_dlon_pos = BBOX_MAX_LON - ANCHOR_LON
    max_dlon_neg = ANCHOR_LON - BBOX_MIN_LON

    # Find the scaling factor needed to keep the point inside the bbox
    scale = 1.0
    
    if delta_lat > 0 and delta_lat > max_dlat_pos:
        scale = min(scale, max_dlat_pos / delta_lat)
    elif delta_lat < 0 and abs(delta_lat) > max_dlat_neg:
        scale = min(scale, max_dlat_neg / abs(delta_lat))
        
    if delta_lon > 0 and delta_lon > max_dlon_pos:
        scale = min(scale, max_dlon_pos / delta_lon)
    elif delta_lon < 0 and abs(delta_lon) > max_dlon_neg:
        scale = min(scale, max_dlon_neg / abs(delta_lon))
        
    return delta_lat * scale, delta_lon * scale

def mock_route_to_chicago(waypoints: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    Translates real user coordinates to the Chicago bounding box using a relative offset mapping.
    This ensures that the model (trained on Chicago data) receives valid inputs without 
    collapsing all points in a route into a single static coordinate.
    """
    if not waypoints:
        return []
        
    ref_lat, ref_lon = waypoints[0]
    mocked = []
    
    for lat, lon in waypoints:
        delta_lat = lat - ref_lat
        delta_lon = lon - ref_lon
        
        delta_lat, delta_lon = _scale_if_out_of_bbox(delta_lat, delta_lon)
        
        mock_lat = _clamp(ANCHOR_LAT + delta_lat, BBOX_MIN_LAT, BBOX_MAX_LAT)
        mock_lon = _clamp(ANCHOR_LON + delta_lon, BBOX_MIN_LON, BBOX_MAX_LON)
        
        mocked.append((mock_lat, mock_lon))
        
    return mocked
