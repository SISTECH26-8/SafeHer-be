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

        skip_paths = {"/health", "/docs", "/redoc", "/openapi.json", "/api/v1/openapi.json"}
        if request.url.path not in skip_paths:
            import json
            import http
            
            request_body_json = None
            query_params_dict = dict(request.query_params)
            
            try:
                message = http.HTTPStatus(response.status_code).phrase
            except Exception:
                message = "Unknown Status"

            asyncio.create_task(
                self._log_request(
                    request, 
                    response.status_code, 
                    latency_ms,
                    request_body_json,
                    query_params_dict,
                    message
                )
            )

        return response

    async def _log_request(self, request: Request, status_code: int, latency_ms: float, body: dict, query: dict, message: str):
        db: Session = SessionLocal()
        try:
            user_id = None
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                from app.core.security import decode_access_token
                try:
                    user_id = decode_access_token(token)
                except Exception:
                    pass
                    
            log = APIRequestLog(
                request_id=uuid.uuid4(),
                method=request.method,
                path=request.url.path,
                query_params=query if query else None,
                request_body=body,
                status_code=status_code,
                latency_ms=latency_ms,
                message=message,
                user_id=user_id,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Logging Error: {e}")
        finally:
            db.close()
