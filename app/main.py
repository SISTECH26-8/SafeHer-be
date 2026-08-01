from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.lifespan import lifespan
from app.middlewares.logging_middleware import LoggingMiddleware
from app.users.router import router as users_router
from app.trips.router import router as trips_router
from app.safe_points.router import router as safe_points_router

# Import all models to ensure SQLAlchemy mappers initialize correctly
import app.users.models
import app.safe_points.models
import app.reports.models
import app.trips.models
import app.emergency.models
import app.system.models

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json"
)

# Set up CORS
if settings.CORS_ORIGINS:
    allow_all = "*" in settings.CORS_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else [str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=False if allow_all else True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(LoggingMiddleware)

@app.get("/", tags=["System"])
def root():
    """Welcome message and documentation link."""
    return {
        "message": "Selamat datang di SafeHer API. Silakan kunjungi /docs untuk melihat dokumentasi API."
    }

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": app.state.model is not None
    }

# Register Routers
app.include_router(users_router, prefix=settings.API_V1_PREFIX + "/auth")
app.include_router(trips_router, prefix=settings.API_V1_PREFIX)
app.include_router(safe_points_router, prefix=settings.API_V1_PREFIX)
