import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Tuple, Any

from app.core import exceptions as exc
from app.ml import geo_config
from app.ml.geo_mock import mock_route_to_chicago

FEATURE_COLS = [
    "lat_r", "lon_r",
    "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    "is_weekend", "is_night",
    "crime_count", "mean_severity", "arrest_rate", "domestic_ratio",
    "mean_crowd_level", "mean_lighting_level", "distance_to_cbd_km",
    "cell_target_enc", "cell_freq_enc",
    "loc_cat_COMMERCIAL", "loc_cat_OTHER", "loc_cat_RESIDENTIAL",
    "loc_cat_STREET_PUBLIC", "loc_cat_TRANSIT", "loc_cat_VEHICLE",
]

# Global Data Store
_cell_stats: pd.DataFrame = None
_cell_fallback: pd.DataFrame = None
_global_fallback: dict = None

def load_ml_resources():
    """Memuat file statistik parquet & JSON secara global di memori."""
    global _cell_stats, _cell_fallback, _global_fallback
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base_dir, "artifacts", "ml", "datasets")
    
    f_stats = os.path.join(data_dir, "cell_stats.parquet")
    f_cell_fb = os.path.join(data_dir, "cell_stats_fallback_cell.parquet")
    f_global_fb = os.path.join(data_dir, "cell_stats_fallback_global.json")
    
    # Hanya muat jika file ada, untuk menghindari error fatal jika belum di-generate
    if os.path.exists(f_stats):
        _cell_stats = pd.read_parquet(f_stats)
        if 'lat_r' in _cell_stats.columns:
            _cell_stats.set_index(['lat_r', 'lon_r', 'period', 'dow'], inplace=True)
    
    if os.path.exists(f_cell_fb):
        _cell_fallback = pd.read_parquet(f_cell_fb)
        if 'lat_r' in _cell_fallback.columns:
            _cell_fallback.set_index(['lat_r', 'lon_r'], inplace=True)
            
    if os.path.exists(f_global_fb):
        with open(f_global_fb, 'r') as f:
            _global_fallback = json.load(f)
    else:
        # Hardcode fallback aman jika JSON tidak ada
        _global_fallback = {c: 0.0 for c in FEATURE_COLS if c not in ["lat_r", "lon_r", "hour_sin", "hour_cos", "dow_sin", "dow_cos", "is_weekend", "is_night"]}
        _global_fallback["dominant_location_category"] = "OTHER"

def _get_hour_cat(hour: int) -> str:
    if 0 <= hour <= 5: return 'Night'
    elif 6 <= hour <= 11: return 'Morning'
    elif 12 <= hour <= 17: return 'Afternoon'
    else: return 'Evening'

def _build_features(lat: float, lon: float, dt: datetime) -> Tuple[pd.DataFrame, str]:
    # Pembulatan 2 desimal
    lat_r = float(np.round(lat, 2))
    lon_r = float(np.round(lon, 2))
    
    # Ekstraksi waktu
    hour = dt.hour
    dow = dt.weekday()
    
    hour_sin = np.sin(2 * np.pi * hour / 24.0)
    hour_cos = np.cos(2 * np.pi * hour / 24.0)
    dow_sin = np.sin(2 * np.pi * dow / 7.0)
    dow_cos = np.cos(2 * np.pi * dow / 7.0)
    
    is_weekend = 1 if dow >= 5 else 0
    is_night = 1 if (hour < 6 or hour >= 18) else 0
    hour_cat = _get_hour_cat(hour)
    
    # Fitur Kelompok A (Dinamis)
    features = {
        "lat_r": lat_r,
        "lon_r": lon_r,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "dow_sin": dow_sin,
        "dow_cos": dow_cos,
        "is_weekend": is_weekend,
        "is_night": is_night
    }
    
    # Fitur Kelompok B (Lookup Berjenjang)
    stats = None
    
    # 1. Primary Exact Match
    if _cell_stats is not None:
        try:
            stats = _cell_stats.loc[(lat_r, lon_r, hour_cat, dow)]
            if isinstance(stats, pd.DataFrame):
                stats = stats.iloc[0]
        except KeyError:
            pass
            
    # 2. Cell Fallback
    if stats is None and _cell_fallback is not None:
        try:
            stats = _cell_fallback.loc[(lat_r, lon_r)]
            if isinstance(stats, pd.DataFrame):
                stats = stats.iloc[0]
        except KeyError:
            pass
            
    # 3. Global Fallback
    if stats is None:
        stats = _global_fallback
        
    hist_cols = [
        "crime_count", "mean_severity", "arrest_rate", "domestic_ratio",
        "mean_crowd_level", "mean_lighting_level", "distance_to_cbd_km",
        "cell_target_enc", "cell_freq_enc"
    ]
    for c in hist_cols:
        features[c] = stats.get(c, 0.0)
        
    # Konversi Kategori Dominan ke One-Hot
    dom_cat = stats.get("dominant_location_category", "OTHER")
    loc_cats = ["COMMERCIAL", "OTHER", "RESIDENTIAL", "STREET_PUBLIC", "TRANSIT", "VEHICLE"]
    
    for lc in loc_cats:
        col_name = f"loc_cat_{lc}"
        features[col_name] = 1.0 if dom_cat == lc else 0.0
        
    return features

def score_to_level(score: float) -> Tuple[str, str]:
    if score <= geo_config.RISK_THRESHOLD_LOW_MAX:
        return "LOW", "GREEN"
    elif score <= geo_config.RISK_THRESHOLD_MEDIUM_MAX:
        return "MEDIUM", "YELLOW"
    else:
        return "HIGH", "RED"

def predict_risk_score(model: Any, lat: float, lon: float, dt: datetime) -> Tuple[float, str]:
    """Mengembalikan score untuk satu titik."""
    if model is None:
        raise exc.ml_prediction_failed("Model ML tidak tersedia untuk inferensi.")
        
    mocked_coords = mock_route_to_chicago([(lat, lon)])
    if not mocked_coords:
        raise exc.ml_prediction_failed("Gagal melakukan konversi koordinat mock.")
        
    mock_lat, mock_lon = mocked_coords[0]
    
    feat_dict = _build_features(mock_lat, mock_lon, dt)
    df = pd.DataFrame([feat_dict], columns=FEATURE_COLS)
    
    try:
        prediction = model.predict(df)[0]
        return float(prediction)
    except Exception as e:
        raise exc.ml_prediction_failed(f"Kesalahan saat inferensi model: {str(e)}")

def predict_batch(model: Any, waypoints: List[Tuple[float, float]], dt: datetime) -> List[float]:
    """Mengembalikan [scores] untuk batch titik."""
    if model is None:
        raise exc.ml_prediction_failed("Model ML tidak tersedia untuk inferensi batch.")
        
    if not waypoints:
        return []
        
    mocked_coords = mock_route_to_chicago(waypoints)
    
    features_list = []
    
    for mock_lat, mock_lon in mocked_coords:
        feat_dict = _build_features(mock_lat, mock_lon, dt)
        features_list.append(feat_dict)
        
    df_batch = pd.DataFrame(features_list, columns=FEATURE_COLS)
    
    try:
        predictions = model.predict(df_batch)
        return [float(p) for p in predictions]
    except Exception as e:
        raise exc.ml_prediction_failed(f"Kesalahan saat inferensi batch: {str(e)}")

