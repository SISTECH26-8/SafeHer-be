from sqlalchemy import Column, String, DateTime, func, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.db.session import Base

class MLPredictionLog(Base):
    __tablename__ = "ml_prediction_logs"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String, nullable=False)
    source = Column(String, nullable=False) # e.g., 'live' or 'batch'
    inputs = Column(JSONB, nullable=False) # Store original and mock coords, features
    predicted_score = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=True)

class APIRequestLog(Base):
    __tablename__ = "api_request_logs"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    query_params = Column(JSONB, nullable=True)
    request_body = Column(JSONB, nullable=True)
    status_code = Column(Integer, nullable=False)
    latency_ms = Column(Float, nullable=False)
    message = Column(String, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True) # Nullable for unauthenticated endpoints
