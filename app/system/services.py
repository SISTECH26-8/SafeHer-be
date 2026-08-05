from sqlalchemy.orm import Session
from sqlalchemy import func
from app.system.models import MLPredictionLog, APIRequestLog

def get_monitoring_metrics(db: Session) -> dict:
    # Prediction Distribution
    pred_stats = db.query(
        func.count(MLPredictionLog.request_id).label("total"),
        func.avg(MLPredictionLog.predicted_score).label("avg_score"),
        func.min(MLPredictionLog.predicted_score).label("min_score"),
        func.max(MLPredictionLog.predicted_score).label("max_score")
    ).first()
    
    # Model Usage
    model_usage = db.query(
        MLPredictionLog.model_version,
        func.count(MLPredictionLog.request_id).label("count")
    ).group_by(MLPredictionLog.model_version).all()
    
    model_usage_dict = {m.model_version: m.count for m in model_usage} if model_usage else {}
    
    # Latency
    avg_pred_latency = db.query(func.avg(MLPredictionLog.latency_ms)).scalar() or 0.0
    avg_api_latency = db.query(func.avg(APIRequestLog.latency_ms)).scalar() or 0.0
    
    # Data Freshness
    last_pred = db.query(func.max(MLPredictionLog.timestamp)).scalar()
    
    return {
        "prediction_distribution": {
            "total_predictions": pred_stats.total if pred_stats else 0,
            "average_risk_score": round(pred_stats.avg_score, 2) if pred_stats and pred_stats.avg_score else 0.0,
            "min_risk_score": round(pred_stats.min_score, 2) if pred_stats and pred_stats.min_score else 0.0,
            "max_risk_score": round(pred_stats.max_score, 2) if pred_stats and pred_stats.max_score else 0.0,
        },
        "model_usage": model_usage_dict,
        "latency": {
            "average_prediction_latency_ms": round(avg_pred_latency, 2),
            "average_api_latency_ms": round(avg_api_latency, 2)
        },
        "data_freshness": {
            "latest_prediction_timestamp": last_pred.isoformat() if last_pred else None
        }
    }
