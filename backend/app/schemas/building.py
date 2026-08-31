"""Pydantic schemas for buildings."""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.common import validate_parent_ulpin

class BuildingBase(BaseModel):
    building_id: str
    parent_ulpin: str
    building_name: Optional[str] = None
    total_height_m: float
    num_floors: int
    construction_year: Optional[int] = None

    @field_validator("parent_ulpin")
    @classmethod
    def check_ulpin(cls, v: str) -> str:
        return validate_parent_ulpin(v)

class BuildingCreate(BuildingBase):
    footprint_coordinates: Optional[List[List[float]]] = None

class BuildingResponse(BuildingBase):
    model_config = ConfigDict(from_attributes=True)
