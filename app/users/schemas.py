from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from typing import Dict, Any

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
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
