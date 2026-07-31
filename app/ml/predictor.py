from datetime import datetime
import pandas as pd
from typing import List, Tuple, Any

from app.core import exceptions as exc
from app.ml import geo_config
from app.ml.geo_mock import mock_route_to_chicago

def score_to_level(score: float) -> Tuple[str, str]:
    """
    Mengonversi skor numerik menjadi level keamanan dan warna.
    Mengembalikan tuple (Level, Color).
    """
    if score <= geo_config.RISK_THRESHOLD_LOW_MAX:
        return "LOW", "GREEN"
    elif score <= geo_config.RISK_THRESHOLD_MEDIUM_MAX:
        return "MEDIUM", "YELLOW"
    else:
        return "HIGH", "RED"

def _extract_time_features(dt: datetime) -> Tuple[int, int]:
    """
    Mengekstrak fitur Hour dan DayOfWeek dari datetime.
    DayOfWeek: 0 = Senin, 6 = Minggu (berdasarkan datetime.weekday())
    """
    return dt.hour, dt.weekday()

def predict_risk_score(model: Any, lat: float, lon: float, dt: datetime) -> float:
    """
    Memprediksi skor risiko untuk satu titik koordinat.
    """
    if model is None:
        raise exc.ml_prediction_failed("Model ML tidak tersedia untuk inferensi.")

    # Convert coordinates to Chicago bounding box
    mocked_coords = mock_route_to_chicago([(lat, lon)])
    if not mocked_coords:
        raise exc.ml_prediction_failed("Gagal melakukan konversi koordinat mock.")
        
    mock_lat, mock_lon = mocked_coords[0]
    
    # Extract time features
    hour, day_of_week = _extract_time_features(dt)
    
    # Build DataFrame matching model features
    df = pd.DataFrame([{
        "Latitude": mock_lat,
        "Longitude": mock_lon,
        "Hour": hour,
        "DayOfWeek": day_of_week
    }])
    
    try:
        prediction = model.predict(df)[0]
        return float(prediction)
    except Exception as e:
        raise exc.ml_prediction_failed(f"Kesalahan saat inferensi model: {str(e)}")

def predict_batch(model: Any, waypoints: List[Tuple[float, float]], dt: datetime) -> List[float]:
    """
    Memprediksi skor risiko untuk list titik koordinat (batch).
    """
    if model is None:
        raise exc.ml_prediction_failed("Model ML tidak tersedia untuk inferensi batch.")
        
    if not waypoints:
        return []

    # Convert all coordinates to Chicago bounding box
    mocked_coords = mock_route_to_chicago(waypoints)
    
    # Extract time features
    hour, day_of_week = _extract_time_features(dt)
    
    # Build DataFrame
    data = []
    for mock_lat, mock_lon in mocked_coords:
        data.append({
            "Latitude": mock_lat,
            "Longitude": mock_lon,
            "Hour": hour,
            "DayOfWeek": day_of_week
        })
        
    df = pd.DataFrame(data)
    
    try:
        predictions = model.predict(df)
        return [float(p) for p in predictions]
    except Exception as e:
        raise exc.ml_prediction_failed(f"Kesalahan saat inferensi batch: {str(e)}")
