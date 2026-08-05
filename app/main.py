from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.lifespan import lifespan
from app.middlewares.logging_middleware import LoggingMiddleware
from app.users.router import auth_router, users_router
from app.trips.router import router as trips_router
from app.safe_points.router import router as safe_points_router
from app.emergency.router import router as emergency_router
from app.reports.router import router as reports_router
from app.system.router import router as system_router

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
    from app.db.redis_client import get_redis_client
    from app.db.session import SessionLocal
    from sqlalchemy import text
    
    db_status = "error"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass
    finally:
        db.close()
        
    redis_status = "error"
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        redis_status = "connected"
    except Exception:
        pass
        
    return {
        "status": "ok" if db_status == "connected" and redis_status == "connected" else "degraded",
        "model_loaded": app.state.model is not None,
        "db": db_status,
        "redis": redis_status
    }

# Register Routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX + "/auth")
app.include_router(users_router, prefix=settings.API_V1_PREFIX + "/users")
app.include_router(trips_router, prefix=settings.API_V1_PREFIX)
app.include_router(safe_points_router, prefix=settings.API_V1_PREFIX)
app.include_router(emergency_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(system_router)