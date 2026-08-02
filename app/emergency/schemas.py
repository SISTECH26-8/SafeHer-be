from pydantic import BaseModel,  field_validator, Field
from uuid import UUID
from typing import Optional
from datetime import datetime

class EmergencyContactCreate(BaseModel):
    contact_name: str = Field(..., min_length=1, example="Budi Santoso")
    phone_number: str = Field(..., example="081234567890")
    relation: Optional[str] = Field(None, example="Ayah")

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        cleaned = re.sub(r'[^\d+]', '', v)
        if not cleaned or (cleaned == '+'):
            raise ValueError("Nomor telepon tidak valid")
        return cleaned

class EmergencyContactCreateResponse(BaseModel):
    contact_id: UUID
    message: str
    
class EmergencyContactResponse(BaseModel):
    contact_id: UUID
    contact_name: str
    phone_number: str
    relation: Optional[str]

class EmergencyContactListResponse(BaseModel):
    contacts: list[EmergencyContactResponse]

class EmergencyContactUpdateResponse(BaseModel):
    status: str
    message: str
    contact: EmergencyContactResponse
    
class EmergencyContactDeleteResponse(BaseModel):
    status: str
    message: str

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