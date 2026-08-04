from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from typing import Dict, Any

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: str

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        if not re.match(r'^(0|62)\d+$', v):
            raise ValueError("Nomor telepon tidak valid. Harus diawali 0 atau 62 dan hanya berisi angka.")
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

class UserProfileResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: EmailStr
    phone_number: str
    created_at: Any

class UserProfileUpdate(BaseModel):
    full_name: str
    phone_number: str

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        if not re.match(r'^(0|62)\d+$', v):
            raise ValueError("Nomor telepon tidak valid. Harus diawali 0 atau 62 dan hanya berisi angka.")
        return v

class UserProfileUpdateResponse(BaseModel):
    status: str
    message: str
    user: UserProfileResponse

from pydantic import BaseModel, EmailStr, field_validator, Field

class UserPreferenceSchema(BaseModel):
    priority_main_road: bool
    auto_share_sos_to_contacts: bool
    alert_radius_km: float = Field(ge=0.0)

class UserPreferenceUpdateResponse(BaseModel):
    status: str
    message: str