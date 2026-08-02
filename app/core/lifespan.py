from contextlib import asynccontextmanager
from fastapi import FastAPI
import joblib
from app.core.config import settings
import logging
from app.ml.predictor import load_ml_resources

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    try:
        app.state.model = joblib.load(settings.MODEL_PATH)
        app.state.model_version = settings.MODEL_VERSION
        logger.info(f"Successfully loaded ML model version {settings.MODEL_VERSION} from {settings.MODEL_PATH}")
    except Exception as e:
        logger.warning(f"Could not load ML model from {settings.MODEL_PATH}. Prediction endpoints may fail. Error: {e}")
        app.state.model = None
        app.state.model_version = "unknown"
        
    # Load ML static features (Parquet/JSON)
    try:
        load_ml_resources()
        logger.info("Successfully loaded ML feature lookup resources (Parquet/JSON).")
    except Exception as e:
        logger.error(f"Error loading ML feature lookup resources: {e}")
    
    yield
    # Clean up on shutdown if necessary
    app.state.model = None
