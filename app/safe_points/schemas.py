from pydantic import BaseModel
from typing import Optional
import uuid

class SafePointResponse(BaseModel):
    safe_id: uuid.UUID
    name: str
    type: str
    lat: float
    lon: float
    status_lokasi: Optional[str] = None
    contact_number: Optional[str] = None
