"""Pydantic schemas for property rights."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator
from app.schemas.common import validate_holder_masked

class PropertyRightBase(BaseModel):
    right_id: str
    unit_id: str
    right_type: str
    holder_name_masked: str
    record_status: str = "active"
    document_reference: Optional[str] = None

    @field_validator("holder_name_masked")
    @classmethod
    def check_holder_masked(cls, v: str) -> str:
        return validate_holder_masked(v)

class PropertyRightCreate(PropertyRightBase):
    pass

class PropertyRightResponse(PropertyRightBase):
    model_config = ConfigDict(from_attributes=True)
