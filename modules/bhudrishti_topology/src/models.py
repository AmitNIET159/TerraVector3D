"""Pydantic models for BhuDrishti 3D topology validation.

All models use snake_case field names.  Geometry coordinates are in
local Cartesian metres — never latitude / longitude.
"""

from __future__ import annotations

import re
import uuid
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Constants & regex patterns
# ---------------------------------------------------------------------------

#: Parent ULPIN is always exactly 14 uppercase alphanumeric characters.
PARENT_ULPIN_PATTERN = re.compile(r"^[A-Z0-9]{14}$")

#: Vertical ID format: <ULPIN>-F<level>-U<unit_code>-R<revision>
VERTICAL_ID_PATTERN = re.compile(
    r"^[A-Z0-9]{14}-F[A-Z0-9]+-U[A-Z0-9]+-R[0-9]+$"
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConflictType(str, Enum):
    """Types of spatial conflicts detected by the topology validator."""

    VOLUME_OVERLAP = "VOLUME_OVERLAP"
    DUPLICATE_VERTICAL_ID = "DUPLICATE_VERTICAL_ID"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    INVALID_Z_RANGE = "INVALID_Z_RANGE"
    UNIT_OUTSIDE_BUILDING = "UNIT_OUTSIDE_BUILDING"
    LEVEL_ASSIGNMENT_ERROR = "LEVEL_ASSIGNMENT_ERROR"
    PARKING_APARTMENT_OVERLAP = "PARKING_APARTMENT_OVERLAP"
    UTILITY_EASEMENT_REVIEW = "UTILITY_EASEMENT_REVIEW"
    FLOATING_UNIT_WARNING = "FLOATING_UNIT_WARNING"


class Severity(str, Enum):
    """Severity levels for detected conflicts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class LevelInfo(BaseModel):
    """Describes one building level / floor."""

    level_code: str = Field(..., description="Level code, e.g. '01', 'B1'")
    z_min_m: float = Field(..., description="Floor slab bottom in metres")
    z_max_m: float = Field(..., description="Floor slab top in metres")

    @model_validator(mode="after")
    def _check_z_range(self) -> "LevelInfo":
        if self.z_min_m >= self.z_max_m:
            raise ValueError(
                f"z_min_m ({self.z_min_m}) must be strictly less than "
                f"z_max_m ({self.z_max_m})"
            )
        return self


class SpatialUnit(BaseModel):
    """A 2.5-D cadastral spatial unit.

    Each unit has a 2-D footprint polygon (local-metre coordinates),
    ``z_min_m``, and ``z_max_m``.
    """

    unit_id: str
    vertical_id: str
    parent_ulpin: str
    building_id: str
    level_code: str
    unit_type: str = Field(
        ...,
        description=(
            "One of: apartment, parking, utility, easement, "
            "commercial, common_area"
        ),
    )
    footprint: List[List[float]] = Field(
        ...,
        description="Closed ring of [x, y] in local Cartesian metres",
    )
    z_min_m: float
    z_max_m: float
    area_sqm: float
    usage_type: str = Field(
        ...,
        description=(
            "One of: residential, commercial, parking, utility, "
            "easement, common_area"
        ),
    )
    status: str = Field(
        ...,
        description="One of: active, proposed, under_construction, demolished",
    )

    # -- validators --------------------------------------------------------

    @field_validator("parent_ulpin")
    @classmethod
    def _validate_parent_ulpin(cls, v: str) -> str:
        if not PARENT_ULPIN_PATTERN.match(v):
            raise ValueError(
                "parent_ulpin must be exactly 14 uppercase "
                "alphanumeric characters"
            )
        return v

    @field_validator("vertical_id")
    @classmethod
    def _validate_vertical_id(cls, v: str) -> str:
        if not VERTICAL_ID_PATTERN.match(v):
            raise ValueError(
                "vertical_id must match "
                "<ULPIN>-F<level>-U<unit_code>-R<revision>"
            )
        return v


class BuildingInput(BaseModel):
    """Top-level input representing a building and its spatial units."""

    building_id: str
    parent_ulpin: str
    footprint: List[List[float]] = Field(
        ...,
        description="Building outline polygon in local Cartesian metres",
    )
    levels: List[LevelInfo]
    total_height_m: float = Field(
        ..., description="Maximum height of the building in metres"
    )
    spatial_units: List[SpatialUnit]

    @field_validator("parent_ulpin")
    @classmethod
    def _validate_parent_ulpin(cls, v: str) -> str:
        if not PARENT_ULPIN_PATTERN.match(v):
            raise ValueError(
                "parent_ulpin must be exactly 14 uppercase "
                "alphanumeric characters"
            )
        return v


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class ConflictResult(BaseModel):
    """A single conflict / validation issue detected by the engine."""

    conflict_id: str = Field(
        default_factory=lambda: f"CONFLICT-{uuid.uuid4().hex[:8].upper()}"
    )
    conflict_type: ConflictType
    severity: Severity
    affected_unit_ids: List[str]
    affected_vertical_ids: List[str]
    horizontal_overlap_area_sqm: float = 0.0
    overlapping_z_min_m: float = 0.0
    overlapping_z_max_m: float = 0.0
    estimated_overlap_volume_cum: float = Field(
        default=0.0,
        description="Estimated volumetric overlap in cubic metres",
    )
    recommended_action: str
    human_readable_explanation: str


class ValidationSummary(BaseModel):
    """Aggregated validation result for a building."""

    building_id: str
    parent_ulpin: str
    total_units: int
    total_conflicts: int
    conflicts_by_severity: Dict[str, int]
    conflicts_by_type: Dict[str, int]
    conflicts: List[ConflictResult]
    is_valid: bool
