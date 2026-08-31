"""Pydantic schemas for topology conflicts."""
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

class TopologyConflictBase(BaseModel):
    conflict_id: str
    conflict_type: str
    severity: str
    affected_unit_ids: List[str] = []
    affected_vertical_ids: List[str] = []
    horizontal_overlap_area_sqm: float = 0.0
    overlapping_z_min_m: float = 0.0
    overlapping_z_max_m: float = 0.0
    estimated_overlap_volume_cum: float = 0.0
    recommended_action: str
    human_readable_explanation: str

    @field_validator("severity")
    @classmethod
    def check_severity(cls, v: str) -> str:
        if v not in ("low", "medium", "high"):
            raise ValueError("severity must be 'low', 'medium', or 'high'")
        return v

class TopologyConflictResponse(TopologyConflictBase):
    model_config = ConfigDict(from_attributes=True)
