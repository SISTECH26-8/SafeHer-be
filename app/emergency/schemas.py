from pydantic import BaseModel,  field_validator, Field
from uuid import UUID
from typing import Optional

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

class EmergencyContactResponse(BaseModel):
    contact_id: UUID
    contact_name: str
    phone_number: str
    relation: Optional[str]

class EmergencyContactListResponse(BaseModel):
    contacts: list[EmergencyContactResponse]