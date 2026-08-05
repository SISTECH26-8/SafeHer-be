import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import func
from app.db.session import SessionLocal
from app.system.models import MLPredictionLog, APIRequestLog

def export_mlops_output(full_name: str = "Keisha"):
    db = SessionLocal()
    try:
        # 1. Total Predictions
        total_preds = db.query(func.count(MLPredictionLog.request_id)).scalar() or 0
        
        # 2. Latest Model Version Usage
        latest_version_usage = db.query(func.count(MLPredictionLog.request_id))\
                                 .filter(MLPredictionLog.model_version == "v1.0.0").scalar() or 0
                                 
        # 3. Average Risk Score
        avg_score = db.query(func.avg(MLPredictionLog.predicted_score)).scalar() or 0.0
        
        # 4. Latency
        avg_pred_latency = db.query(func.avg(MLPredictionLog.latency_ms)).scalar() or 0.0
        
        # 5. Prediction History (limit to latest 100 for compactness)
        logs = db.query(MLPredictionLog).order_by(MLPredictionLog.timestamp.desc()).limit(100).all()
        
        history = []
        for log in logs:
            history.append({
                "request_id": str(log.request_id),
                "timestamp": log.timestamp.isoformat(),
                "model_version": log.model_version,
                "source": log.source,
                "inputs": log.inputs,
                "predicted_score": log.predicted_score,
                "latency_ms": log.latency_ms
            })

        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "project": "SISTECH 2026 - MLOps SafeHer"
            },
            "metrics": {
                "total_predictions": total_preds,
                "latest_model_usage_count": latest_version_usage,
                "average_risk_score": round(avg_score, 4),
                "average_prediction_latency_ms": round(avg_pred_latency, 4)
            },
            "prediction_history": history
        }
        
        filename = f"ML_Predictions_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=4)
            
        print(f"Successfully generated {filename}")
        
    finally:
        db.close()

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Keisha"
    export_mlops_output(name)
