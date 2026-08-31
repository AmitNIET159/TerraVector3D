"""Pydantic schemas for spatial units."""
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.schemas.common import validate_parent_ulpin, validate_vertical_id, validate_z_range

class SpatialUnitBase(BaseModel):
    unit_id: str
    vertical_id: str
    parent_ulpin: str
    building_id: str
    level_code: str
    unit_type: str
    z_min_m: float
    z_max_m: float
    area_sqm: float
    usage_type: str
    status: str = "pending"
    model_object_name: Optional[str] = None

    @field_validator("parent_ulpin")
    @classmethod
    def check_ulpin(cls, v: str) -> str:
        return validate_parent_ulpin(v)

    @field_validator("vertical_id")
    @classmethod
    def check_vertical_id(cls, v: str) -> str:
        return validate_vertical_id(v)

    @model_validator(mode="after")
    def check_z_range(self) -> "SpatialUnitBase":
        validate_z_range(self.z_min_m, self.z_max_m)
        return self

class SpatialUnitCreate(SpatialUnitBase):
    footprint_coordinates: Optional[List[List[float]]] = None

class SpatialUnitResponse(SpatialUnitBase):
    model_config = ConfigDict(from_attributes=True)
