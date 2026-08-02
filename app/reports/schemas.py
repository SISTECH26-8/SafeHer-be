from pydantic import BaseModel, Field, field_validator
from typing import Literal
from app.core import exceptions as exc

class ReportCreate(BaseModel):
    category: Literal["TINDAK_KRIMINAL", "PELECEHAN_SEKSUAL", "ORANG_MENCURIGAKAN"] = Field(..., example="TINDAK_KRIMINAL")
    description: str = Field(..., min_length=1, example="Terdapat tindak pencurian di jalan ini.")
    lat: float = Field(..., example=-6.3650)
    lon: float = Field(..., example=106.8280)

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise exc.invalid_coordinates()
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise exc.invalid_coordinates()
        return v

class ReportResponse(BaseModel):
    status: str
    message: str