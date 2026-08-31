"""
Pydantic data models for BhuDrishti 3D Vertical Property Validation Reports.

All geometry coordinates use local Cartesian metres (never lat/lon).
Parent ULPIN is always exactly 14 uppercase alphanumeric characters.
Vertical ID format: <parent_ulpin>-F<level>-U<unit_code>-R<revision>

Canonical field aliases supported via Pydantic AliasChoices:
  level_code → level_id,  status → validation_status,
  footprint → footprint_coordinates / boundary_coordinates,
  holder_name_masked (preferred over holder_name).
"""

from __future__ import annotations

import re
from typing import Optional

from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    field_validator,
    model_validator,
)


# ---------------------------------------------------------------------------
# Constants & patterns
# ---------------------------------------------------------------------------

ULPIN_PATTERN = re.compile(r"^[A-Z0-9]{14}$")
VERTICAL_ID_PATTERN = re.compile(
    r"^[A-Z0-9]{14}-F[A-Z0-9]+-U[A-Z0-9]+-R\d+$"
)
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def mask_holder_name(name: str) -> str:
    """Mask a holder name for privacy.

    ``'Rajesh Kumar'`` → ``'Ra***h Ku**r'``
    """
    parts = name.split()
    masked: list[str] = []
    for part in parts:
        if len(part) <= 2:
            masked.append(part[0] + "*")
        elif len(part) == 3:
            masked.append(part[0] + "*" + part[-1])
        else:
            masked.append(part[:2] + "*" * (len(part) - 3) + part[-1])
    return " ".join(masked)


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ParcelData(BaseModel):
    """Land parcel information."""

    parcel_id: str
    area_sqm: float = Field(gt=0, description="Parcel area in square metres")
    boundary_coordinates: list[list[float]] = Field(
        description="Polygon vertices in local Cartesian metres [x, y]"
    )
    land_use: str
    survey_number: str


class BuildingData(BaseModel):
    """Building-level information."""

    building_id: str
    building_name: str
    footprint_coordinates: list[list[float]] = Field(
        description="Building footprint in local Cartesian metres [x, y]",
        validation_alias=AliasChoices("footprint_coordinates", "footprint"),
    )
    height_m: float = Field(gt=0, description="Total building height in metres")
    num_floors: int = Field(gt=0, description="Number of floors including basements")
    construction_year: Optional[int] = None


class Level(BaseModel):
    """Individual building level / storey."""

    level_id: str = Field(
        validation_alias=AliasChoices("level_id", "level_code"),
    )
    level_number: int = Field(description="Storey number (negative for basements)")
    height_m: float = Field(gt=0, description="Floor-to-ceiling height in metres")
    floor_area_sqm: float = Field(gt=0, description="Gross floor area in sq m")
    level_type: str = Field(
        description="E.g. 'basement', 'ground', 'upper', 'terrace'"
    )
    z_min_m: Optional[float] = Field(
        default=None, description="Bottom Z in local Cartesian metres"
    )
    z_max_m: Optional[float] = Field(
        default=None, description="Top Z in local Cartesian metres"
    )


class SpatialUnit(BaseModel):
    """A single 3-D spatial unit within the building."""

    vertical_id: str = Field(
        description="Prototype vertical ID: <ULPIN>-F<level>-U<unit>-R<rev>"
    )
    unit_id: Optional[str] = Field(
        default=None, description="Optional short unit identifier"
    )
    level_id: str = Field(
        validation_alias=AliasChoices("level_id", "level_code"),
    )
    unit_type: str = Field(
        description="E.g. 'residential', 'commercial', 'parking', 'utility'"
    )
    area_sqm: float = Field(gt=0, description="Unit area in square metres")
    volume_cbm: Optional[float] = Field(
        default=None, description="Unit volume in cubic metres"
    )
    usage_type: str = Field(
        description="Intended usage, e.g. 'dwelling', 'retail', 'storage'"
    )
    boundary_coordinates: list[list[float]] = Field(
        description="Unit boundary vertices in local Cartesian metres",
        validation_alias=AliasChoices("boundary_coordinates", "footprint"),
    )
    validation_status: str = Field(
        description="'valid', 'conflict', or 'pending'",
        validation_alias=AliasChoices("validation_status", "status"),
    )
    z_min_m: Optional[float] = Field(
        default=None, description="Bottom Z in local Cartesian metres"
    )
    z_max_m: Optional[float] = Field(
        default=None, description="Top Z in local Cartesian metres"
    )

    @field_validator("vertical_id")
    @classmethod
    def validate_vertical_id(cls, v: str) -> str:
        if not VERTICAL_ID_PATTERN.match(v):
            raise ValueError(
                f"Invalid vertical ID format: {v!r}.  "
                f"Expected <ULPIN(14)>-F<level>-U<unit>-R<revision>."
            )
        return v

    @field_validator("validation_status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"valid", "conflict", "pending"}
        if v not in allowed:
            raise ValueError(
                f"validation_status must be one of {allowed}, got {v!r}"
            )
        return v


class PropertyRight(BaseModel):
    """Property-right record linked to a spatial unit.

    Accepts either ``holder_name_masked`` (preferred) or ``holder_name``
    (auto-masked).  Raw ``holder_name`` is never required.
    """

    right_id: str
    vertical_id: str
    rights_type: str = Field(
        description="E.g. 'ownership', 'lease', 'mortgage', 'easement'"
    )
    holder_name: Optional[str] = Field(
        default=None,
        description="Raw holder name (optional — auto-masked if provided)",
    )
    holder_name_masked: Optional[str] = Field(
        default=None,
        description="Pre-masked holder name for display",
    )
    registration_date: Optional[str] = None
    valid: bool = True

    @model_validator(mode="after")
    def ensure_masked_name(self) -> "PropertyRight":
        """Derive holder_name_masked from holder_name when not provided."""
        if not self.holder_name_masked:
            if self.holder_name:
                self.holder_name_masked = mask_holder_name(self.holder_name)
            else:
                self.holder_name_masked = "N/A"
        return self


class TopologyConflict(BaseModel):
    """A detected topology conflict between spatial units."""

    conflict_id: str
    severity: str = Field(description="'high', 'medium', or 'low'")
    conflict_type: Optional[str] = Field(
        default=None,
        description="E.g. 'boundary_overlap', 'encroachment', 'area_discrepancy'",
    )
    conflicting_unit_ids: list[str]
    conflicting_vertical_ids: list[str]
    overlap_area_sqm: float = Field(ge=0, description="Overlap area in sq m")
    overlap_volume_cbm: Optional[float] = Field(
        default=None, ge=0, description="Overlap volume in cubic metres"
    )
    overlapping_z_min_m: Optional[float] = Field(
        default=None, description="Bottom Z of overlap region"
    )
    overlapping_z_max_m: Optional[float] = Field(
        default=None, description="Top Z of overlap region"
    )
    estimated_overlap_volume_cum: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated overlap volume (canonical alias)",
    )
    recommended_action: str
    explanation: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        if v not in allowed:
            raise ValueError(
                f"severity must be one of {allowed}, got {v!r}"
            )
        return v

    @model_validator(mode="after")
    def sync_overlap_volume(self) -> "TopologyConflict":
        """Sync estimated_overlap_volume_cum ↔ overlap_volume_cbm."""
        if self.overlap_volume_cbm is None and self.estimated_overlap_volume_cum is not None:
            self.overlap_volume_cbm = self.estimated_overlap_volume_cum
        elif self.estimated_overlap_volume_cum is None and self.overlap_volume_cbm is not None:
            self.estimated_overlap_volume_cum = self.overlap_volume_cbm
        return self


class SourceMetadata(BaseModel):
    """Provenance record for an evidence source."""

    source_id: str
    file_name: str
    source_type: str = Field(
        description="E.g. 'BIM_IFC', 'CAD_DXF', 'drone_survey', 'satellite'"
    )
    timestamp: str
    confidence: float = Field(ge=0.0, le=1.0)
    sha256_hash: str = Field(min_length=64, max_length=64)

    @field_validator("sha256_hash")
    @classmethod
    def validate_sha256_hex(cls, v: str) -> str:
        """Ensure sha256_hash is exactly 64 hexadecimal characters."""
        if not SHA256_HEX_PATTERN.match(v):
            raise ValueError(
                f"sha256_hash must be exactly 64 hexadecimal characters, "
                f"got {v!r}"
            )
        return v


# ---------------------------------------------------------------------------
# Top-level input model
# ---------------------------------------------------------------------------

class ValidationInput(BaseModel):
    """
    Canonical input schema for BhuDrishti 3D validation report generation.

    Accepts all data required to produce the full evidence-based report:
    parcel, building, levels, spatial units, property rights, conflicts,
    source metadata, confidence scores, and audit information.

    Cross-record validation ensures referential integrity between records.
    """

    parent_ulpin: str = Field(
        min_length=14, max_length=14,
        description="14-character uppercase alphanumeric ULPIN",
    )
    parcel: ParcelData
    building: BuildingData
    levels: list[Level]
    spatial_units: list[SpatialUnit]
    property_rights: list[PropertyRight]
    topology_conflicts: list[TopologyConflict]
    source_metadata: list[SourceMetadata]
    confidence_scores: dict[str, float] = Field(
        description="Named confidence scores, must include 'overall'"
    )
    timestamp: str
    generated_by: str

    @field_validator("parent_ulpin")
    @classmethod
    def validate_ulpin(cls, v: str) -> str:
        if not ULPIN_PATTERN.match(v):
            raise ValueError(
                f"parent_ulpin must be exactly 14 uppercase alphanumeric "
                f"characters, got {v!r}"
            )
        return v

    @field_validator("confidence_scores")
    @classmethod
    def validate_confidence_scores(cls, v: dict[str, float]) -> dict[str, float]:
        if "overall" not in v:
            raise ValueError("confidence_scores must include 'overall' key")
        for key, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"Confidence score '{key}' must be 0.0–1.0, got {score}"
                )
        return v

    @model_validator(mode="after")
    def cross_record_validation(self) -> "ValidationInput":
        """Validate referential integrity across all records."""
        errors: list[str] = []

        prefix = self.parent_ulpin + "-"
        unit_vids = {u.vertical_id for u in self.spatial_units}

        # 1. Every spatial-unit vertical_id must start with parent_ulpin-
        for unit in self.spatial_units:
            if not unit.vertical_id.startswith(prefix):
                errors.append(
                    f"Spatial unit vertical_id '{unit.vertical_id}' "
                    f"does not start with '{prefix}'"
                )

        # 2. Every property-right vertical_id must reference an existing unit
        for right in self.property_rights:
            if right.vertical_id not in unit_vids:
                errors.append(
                    f"Property right '{right.right_id}' references unknown "
                    f"vertical_id '{right.vertical_id}'"
                )

        # 3. Every conflict vertical_id must reference an existing unit
        for conflict in self.topology_conflicts:
            for vid in conflict.conflicting_vertical_ids:
                if vid not in unit_vids:
                    errors.append(
                        f"Conflict '{conflict.conflict_id}' references unknown "
                        f"vertical_id '{vid}'"
                    )

        # 4. Building height consistent with level heights / z ranges
        if self.levels:
            z_levels = [
                lv for lv in self.levels
                if lv.z_min_m is not None and lv.z_max_m is not None
            ]
            if z_levels:
                z_min = min(lv.z_min_m for lv in z_levels)
                z_max = max(lv.z_max_m for lv in z_levels)
                total_z_range = z_max - z_min
                if total_z_range > self.building.height_m * 1.1:
                    errors.append(
                        f"Level z-range ({total_z_range:.1f} m) exceeds "
                        f"building height ({self.building.height_m} m) "
                        f"by more than 10%"
                    )
            else:
                total_height = sum(lv.height_m for lv in self.levels)
                if total_height > self.building.height_m * 1.1:
                    errors.append(
                        f"Sum of level heights ({total_height:.1f} m) exceeds "
                        f"building height ({self.building.height_m} m) "
                        f"by more than 10%"
                    )

        if errors:
            raise ValueError(
                "Cross-record validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        return self
