import time
import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.system.models import APIRequestLog
import uuid


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.monotonic()
        response = await call_next(request)
        latency_ms = (time.monotonic() - start_time) * 1000

        # Skip logging for health check and docs
        skip_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
        if request.url.path not in skip_paths:
            asyncio.create_task(
                self._log_request(request, response.status_code, latency_ms)
            )

        return response

    async def _log_request(self, request: Request, status_code: int, latency_ms: float):
        db: Session = SessionLocal()
        try:
            # Extract user_id from request state if set by auth dependency
            user_id = getattr(request.state, "user_id", None)
            log = APIRequestLog(
                request_id=uuid.uuid4(),
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                latency_ms=latency_ms,
                user_id=user_id,
            )
            db.add(log)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
