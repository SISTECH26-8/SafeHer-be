from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from typing import Dict, Any
from datetime import datetime

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: str

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        cleaned = re.sub(r'[^\d+]', '', v)
        if not cleaned or (cleaned == '+'):
            raise ValueError("Nomor telepon tidak valid")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        if len(v) > 72:
            raise ValueError("Password maksimal 72 karakter")
        return v

class RegisterResponse(BaseModel):
    user_id: UUID
    message: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user: Dict[str, Any]

class SOSCreateRequest(BaseModel):
    current_lat: float = Field(..., example=-6.3644)
    current_lon: float = Field(..., example=106.8286)

    @field_validator("current_lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            from app.core import exceptions as exc
            raise exc.invalid_coordinates()
        return v

    @field_validator("current_lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            from app.core import exceptions as exc
            raise exc.invalid_coordinates()
        return v

class SOSCreateResponse(BaseModel):
    sos_session_id: UUID
    message: str
    live_tracking_url: str

class SOSLocationUpdate(BaseModel):
    lat: float = Field(..., example=-6.3650)
    lon: float = Field(..., example=106.8290)

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            from app.core import exceptions as exc
            raise exc.invalid_coordinates()
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            from app.core import exceptions as exc
            raise exc.invalid_coordinates()
        return v

class SOSLocationUpdateResponse(BaseModel):
    status: str

class SOSTrackLocation(BaseModel):
    lat: float
    lon: float

class SOSTrackResponse(BaseModel):
    user_name: str
    status: str
    last_updated: datetime
    current_location: SOSTrackLocation

class SOSEndResponse(BaseModel):
    status: str
    message: str