"""Pydantic models for BhuDrishti 3D demo cadastre data.

All field names use snake_case.  Geometry coordinates are local Cartesian
metres (never lat/lon).  The parent ULPIN is always exactly 14 uppercase
alphanumeric characters.
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
PARENT_ULPIN_RE = re.compile(r"^[A-Z0-9]{14}$")
VERTICAL_ID_RE = re.compile(
    r"^[A-Z0-9]{14}-F[A-Z0-9]+-U[A-Z0-9]+-R\d{2}$"
)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
class PolygonGeometry(BaseModel):
    """A GeoJSON-style Polygon with coordinates in local Cartesian metres."""

    type: str = "Polygon"
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def ring_must_be_closed(
        cls, v: list[list[list[float]]]
    ) -> list[list[list[float]]]:
        for ring in v:
            if len(ring) < 4:
                raise ValueError("A polygon ring must have >= 4 positions")
            if ring[0] != ring[-1]:
                raise ValueError("Polygon ring is not closed")
        return v


# ---------------------------------------------------------------------------
# Parcel (GeoJSON Feature)
# ---------------------------------------------------------------------------
class ParcelProperties(BaseModel):
    parent_ulpin: str
    parcel_id: str
    address: str
    total_area_sqm: float = Field(gt=0)

    @field_validator("parent_ulpin")
    @classmethod
    def validate_ulpin(cls, v: str) -> str:
        if not PARENT_ULPIN_RE.match(v):
            raise ValueError(
                f"parent_ulpin must be 14 uppercase-alphanumeric chars, got {v!r}"
            )
        return v


class ParcelFeature(BaseModel):
    type: str = "Feature"
    properties: ParcelProperties
    geometry: PolygonGeometry


class ParcelGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: list[ParcelFeature]


# ---------------------------------------------------------------------------
# Building
# ---------------------------------------------------------------------------
class Building(BaseModel):
    building_id: str
    parcel_id: str
    parent_ulpin: str
    building_name: str
    footprint: PolygonGeometry
    total_height_m: float = Field(gt=0)
    num_levels: int = Field(gt=0)
    source_confidence_score: float = Field(ge=0.0, le=1.0)
    source_type: str

    @field_validator("parent_ulpin")
    @classmethod
    def validate_ulpin(cls, v: str) -> str:
        if not PARENT_ULPIN_RE.match(v):
            raise ValueError(f"Invalid parent_ulpin: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Level
# ---------------------------------------------------------------------------
class Level(BaseModel):
    level_code: str
    building_id: str
    level_type: str  # basement | ground | residential
    z_min_m: float
    z_max_m: float
    elevation_label: str

    @field_validator("z_max_m")
    @classmethod
    def z_max_above_z_min(cls, v: float, info) -> float:
        z_min = info.data.get("z_min_m")
        if z_min is not None and v <= z_min:
            raise ValueError("z_max_m must be greater than z_min_m")
        return v


# ---------------------------------------------------------------------------
# Spatial Unit
# ---------------------------------------------------------------------------
class SpatialUnit(BaseModel):
    unit_id: str
    vertical_id: str
    parent_ulpin: str
    building_id: str
    level_code: str
    unit_type: str  # apartment | parking | utility_corridor | common_area
    footprint: PolygonGeometry
    z_min_m: float
    z_max_m: float
    area_sqm: float = Field(gt=0)
    usage_type: str
    status: str  # registered | needs_review
    model_object_name: str

    @field_validator("parent_ulpin")
    @classmethod
    def validate_ulpin(cls, v: str) -> str:
        if not PARENT_ULPIN_RE.match(v):
            raise ValueError(f"Invalid parent_ulpin: {v!r}")
        return v

    @field_validator("vertical_id")
    @classmethod
    def validate_vertical_id(cls, v: str) -> str:
        if not VERTICAL_ID_RE.match(v):
            raise ValueError(f"Invalid vertical_id: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Rights Record
# ---------------------------------------------------------------------------
class RightsRecord(BaseModel):
    right_id: str
    unit_id: str
    vertical_id: str
    right_type: str  # ownership | lease | parking_right | utility_easement
    holder_name_masked: str
    record_status: str  # active | pending | under_review
    document_reference: str
    effective_date: str


# ---------------------------------------------------------------------------
# Source Metadata
# ---------------------------------------------------------------------------
class SourceMetadata(BaseModel):
    source_id: str
    source_type: str
    description: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    coordinate_system: str
    unit_of_measure: str
    generation_timestamp: str
    data_disclaimer: str


# ---------------------------------------------------------------------------
# Conflict Scenario
# ---------------------------------------------------------------------------
class ConflictScenario(BaseModel):
    conflict_id: str
    conflict_type: str
    description: str
    affected_unit_ids: list[str]
    affected_vertical_ids: list[str]
    overlap_area_sqm: Optional[float] = None
    severity: str  # low | medium | high
    recommended_action: str
