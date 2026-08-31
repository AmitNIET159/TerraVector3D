"""Pydantic schemas for levels."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator
from app.schemas.common import validate_z_range

class LevelBase(BaseModel):
    building_id: str
    level_code: str
    level_number: int
    z_min_m: float
    z_max_m: float
    floor_area_sqm: Optional[float] = None
    level_type: str = "above_ground"

    @model_validator(mode="after")
    def check_z_range(self) -> "LevelBase":
        validate_z_range(self.z_min_m, self.z_max_m)
        return self

class LevelCreate(LevelBase):
    pass

class LevelResponse(LevelBase):
    level_id: str
    model_config = ConfigDict(from_attributes=True)
