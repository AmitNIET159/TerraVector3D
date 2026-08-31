"""Pydantic data models for BhuDrishti Geospatial AI.

Canonical cross-module data contract — all field names use snake_case.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


DEMO_PARENT_ULPIN = "7A4B9C2D8E1F6G"
ULPIN_PATTERN = re.compile(r"^[A-Z0-9]{14}$")


def validate_ulpin(ulpin: str) -> str:
    """Validate that a ULPIN is exactly 14 uppercase alphanumeric characters."""
    if not ULPIN_PATTERN.match(ulpin):
        raise ValueError(
            f"parent_ulpin must be exactly 14 uppercase alphanumeric characters, got '{ulpin}'"
        )
    return ulpin


# ---------------------------------------------------------------------------
# GeoJSON Normaliser output
# ---------------------------------------------------------------------------

class NormalizedParcelResult(BaseModel):
    """Output of normalize_geojson()."""
    parent_ulpin: str
    footprint: list  # list of [x, y] pairs or list-of-lists for MultiPolygon
    area_sqm: float
    bounding_box: dict  # {min_x, min_y, max_x, max_y}
    coordinate_reference: str = "LOCAL_METERS"
    source_type: str = "geojson_local_prototype"
    confidence_score: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    human_verification_required: bool = True
    disclaimer: str = (
        "Input GeoJSON is used as a local prototype geometry source "
        "and is not an official cadastral coordinate record. "
        "All outputs require authorised human verification."
    )

    @field_validator("parent_ulpin")
    @classmethod
    def _check_ulpin(cls, v: str) -> str:
        return validate_ulpin(v)


# ---------------------------------------------------------------------------
# Floor-plan Analyser output
# ---------------------------------------------------------------------------

class ProposedUnit(BaseModel):
    """A single proposed room/unit candidate from floor-plan analysis."""
    proposed_unit_code: str
    proposed_boundary: list  # [[x, y], ...]
    area_px: float
    area_sqm: Optional[float] = None
    metric_area_available: bool = False
    confidence_score: float = Field(ge=0.0, le=1.0)
    label_suggestion: str
    warnings: list[str] = Field(default_factory=list)
    human_verification_required: bool = True


class FloorPlanResult(BaseModel):
    """Output of analyze_floor_plan()."""
    parent_ulpin: str
    coordinate_reference: str = "LOCAL_METERS"
    image_path: str
    metres_per_pixel: Optional[float] = None
    proposed_units: list[ProposedUnit] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    human_verification_required: bool = True
    disclaimer: str = (
        "Detected boundaries are preliminary proposals from image processing. "
        "They are not legally valid apartment, flat, or property boundaries. "
        "All results require authorised human confirmation before use in any "
        "cadastral or ownership workflow."
    )

    @field_validator("parent_ulpin")
    @classmethod
    def _check_ulpin(cls, v: str) -> str:
        return validate_ulpin(v)


# ---------------------------------------------------------------------------
# Point-cloud Floor Detector output
# ---------------------------------------------------------------------------

class SuggestedLevel(BaseModel):
    """A single suggested building level from point-cloud analysis."""
    level_code: str  # B1, G, F01, F02, ..., ROOF
    level_type: str = "floor"  # "basement", "ground", "floor", "roof_slab"
    is_cadastral_unit_level: bool = True
    slab_z_m: float
    z_min_m: float
    z_max_m: float
    point_count: int = 0
    confidence_score: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    human_verification_required: bool = True


class PointcloudFloorResult(BaseModel):
    """Output of detect_floor_levels()."""
    parent_ulpin: str
    coordinate_reference: str = "LOCAL_METERS"
    method_used: list[str] = Field(default_factory=list)
    methods_attempted: list[str] = Field(default_factory=list)
    methods_agreed: list[str] = Field(default_factory=list)
    method_agreement_score: float = 0.0
    detected_slab_elevations_m: list[float] = Field(default_factory=list)
    estimated_floor_height_m: float = 0.0
    roof_slab_z_m: Optional[float] = None
    suggested_levels: list[SuggestedLevel] = Field(default_factory=list)
    suggested_cadastral_levels: list[SuggestedLevel] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    human_verification_required: bool = True

    @field_validator("parent_ulpin")
    @classmethod
    def _check_ulpin(cls, v: str) -> str:
        return validate_ulpin(v)


# ---------------------------------------------------------------------------
# Confidence Engine output
# ---------------------------------------------------------------------------

class ConfidenceFactorBreakdown(BaseModel):
    """Breakdown of a single confidence factor."""
    factor: str
    weight: float
    score: Optional[float] = None
    status: str  # "available" or "not_available"


class ConfidenceResult(BaseModel):
    """Output of calculate_confidence()."""
    overall_score: float = Field(ge=0.0, le=1.0)
    confidence_level: str  # "high", "medium", "low"
    factor_breakdown: list[ConfidenceFactorBreakdown] = Field(default_factory=list)
    available_sources: list[str] = Field(default_factory=list)
    missing_sources: list[str] = Field(default_factory=list)
    explanation: str = ""
    warnings: list[str] = Field(default_factory=list)
    human_verification_required: bool = True
