from pydantic import BaseModel, Field
from typing import Any, Dict

class MLPredictionLogCreate(BaseModel):
    model_version: str = Field(..., description="Versi model ML yang digunakan, misal v1.0")
    source: str = Field(..., description="Sumber pemanggilan: 'live' atau 'batch'")
    inputs: Dict[str, Any] = Field(..., description="Payload input berisi koordinat asli, fitur waktu, dan koordinat mock")
    predicted_score: float = Field(..., description="Skor prediksi risiko yang dihasilkan (0-100)")
    latency_ms: float = Field(..., description="Waktu eksekusi inferensi model dalam milidetik")
