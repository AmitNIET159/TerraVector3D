"""Pydantic schemas for parcels."""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.common import validate_parent_ulpin

class ParcelBase(BaseModel):
    parent_ulpin: str
    area_sqm: Optional[float] = None
    land_use: Optional[str] = None
    survey_number: Optional[str] = None

    @field_validator("parent_ulpin")
    @classmethod
    def check_ulpin(cls, v: str) -> str:
        return validate_parent_ulpin(v)

class ParcelCreate(ParcelBase):
    boundary_coordinates: Optional[List[List[float]]] = None

class ParcelResponse(ParcelBase):
    parcel_id: str
    model_config = ConfigDict(from_attributes=True)
