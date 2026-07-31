from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, computed_field, field_validator
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "SafeHer API"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: str | List[str] = ["*"]
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    DATABASE_URL: str
    
    @field_validator("DATABASE_URL")
    @classmethod
    def strip_pgbouncer(cls, v: str) -> str:
        from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
        parsed = urlparse(v)
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_query = [(k, val) for k, val in query_params if k != 'pgbouncer']
        parsed = parsed._replace(query=urlencode(filtered_query))
        return urlunparse(parsed)
    
    REDIS_URL: str
    REDIS_SOS_TTL_SECONDS: int = 3600
    
    MODEL_VERSION: str = "v1.0"
    MODEL_PATH: str = "app/ml/model_v1.joblib"
    
    OSRM_BASE_URL: str = "http://router.project-osrm.org"
    OSRM_TIMEOUT_SECONDS: int = 5
    WHATSAPP_API_KEY: str = "your-wa-api-key"
    WHATSAPP_API_BASE_URL: str = "https://graph.facebook.com/v19.0"
    
    SAFE_POINT_DEFAULT_RADIUS_KM: float = 2.0
    SOS_TRUSTED_CONTACT_LIMIT: int = 3
    TRIP_TRACK_POLL_MIN_INTERVAL_SECONDS: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

settings = Settings()
