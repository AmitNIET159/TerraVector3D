"""
Pydantic v2 models for the bhudrishti_identity_rights module.

Every JSON-facing field uses snake_case.  The canonical holder field is
``holder_name_masked`` — no other holder field name is used anywhere in
this module.

These models are a **prototype extension** and do NOT replace or
constitute an officially approved ULPIN format.
"""

from __future__ import annotations

import enum
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class RightType(str, enum.Enum):
    """Supported property-right types."""

    ownership = "ownership"
    lease = "lease"
    parking_right = "parking_right"
    utility_easement = "utility_easement"


class ValidationStatus(str, enum.Enum):
    """Outcome status for rights-record validation."""

    valid = "valid"
    needs_review = "needs_review"
    invalid = "invalid"


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class VerticalId(BaseModel):
    """Parsed components of a prototype vertical property ID."""

    parent_ulpin: str = Field(
        ...,
        description="Exactly 14 uppercase alphanumeric characters.",
    )
    level: str = Field(
        ...,
        description="Floor level: G, B1-B9, or 01-99.",
    )
    unit_code: str = Field(
        ...,
        description="1-16 uppercase alphanumeric characters.",
    )
    revision: int = Field(
        ...,
        ge=1,
        le=99,
        description="Revision number between 1 and 99.",
    )

    # -- validators --------------------------------------------------------

    @field_validator("parent_ulpin")
    @classmethod
    def check_parent_ulpin(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Z0-9]{14}", v):
            raise ValueError(
                "parent_ulpin must be exactly 14 uppercase alphanumeric "
                f"characters, got: '{v}'"
            )
        return v

    @field_validator("level")
    @classmethod
    def check_level(cls, v: str) -> str:
        if not re.fullmatch(r"G|B[1-9]|[0-9]{2}", v):
            raise ValueError(
                f"level must be G, B1-B9, or 01-99, got: '{v}'"
            )
        if re.fullmatch(r"[0-9]{2}", v) and int(v) == 0:
            raise ValueError("Numeric level must be 01-99, not 00")
        return v

    @field_validator("unit_code")
    @classmethod
    def check_unit_code(cls, v: str) -> str:
        if not re.fullmatch(r"[A-Z0-9]{1,16}", v):
            raise ValueError(
                "unit_code must be 1-16 uppercase alphanumeric characters, "
                f"got: '{v}'"
            )
        return v


class RightsRecord(BaseModel):
    """
    A single property-right record attached to a vertical ID.

    The holder field is always ``holder_name_masked`` and must contain
    at least one ``*`` character to prove masking.
    """

    vertical_id: str
    right_type: RightType
    holder_name_masked: str = Field(
        ...,
        description="Masked holder name, e.g. 'R***A'.",
    )
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Result / output models
# ---------------------------------------------------------------------------

class ValidationResult(BaseModel):
    """Result of validating a vertical ID string."""

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RightsValidationResult(BaseModel):
    """Result of validating a rights record, with transparent audit trail."""

    status: ValidationStatus
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    audit_explanation: list[str] = Field(default_factory=list)


class PropertyIdentitySummary(BaseModel):
    """
    Aggregated identity + rights summary for a single vertical property
    unit, suitable for evidence-report integration.
    """

    vertical_id: str
    parent_ulpin: str
    level_display: str
    unit_code: str
    revision: int
    human_readable_label: str
    rights_records: list[RightsRecord] = Field(default_factory=list)
    rights_validation_results: list[RightsValidationResult] = Field(
        default_factory=list,
    )
    overall_status: ValidationStatus = ValidationStatus.valid
