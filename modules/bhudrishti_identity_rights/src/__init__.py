"""
bhudrishti_identity_rights.src
==============================

Prototype vertical-property-ID and rights-validation engine for
BhuDrishti 3D.

This module is a **prototype extension** only.  It does NOT replace
or constitute an officially approved ULPIN format.
"""

from .exceptions import (
    ParsingError,
    RightsValidationError,
    VerticalIdError,
    VerticalIdValidationError,
)
from .models import (
    PropertyIdentitySummary,
    RightsRecord,
    RightsValidationResult,
    RightType,
    ValidationResult,
    ValidationStatus,
    VerticalId,
)
from .rights_engine import (
    build_property_identity_summary,
    validate_rights_record,
    validate_unit_against_parent,
)
from .vertical_id_engine import (
    build_human_readable_label,
    generate_vertical_id,
    increment_revision,
    parse_vertical_id,
    validate_vertical_id,
)

__all__ = [
    # engines
    "generate_vertical_id",
    "parse_vertical_id",
    "validate_vertical_id",
    "increment_revision",
    "build_human_readable_label",
    "validate_unit_against_parent",
    "validate_rights_record",
    "build_property_identity_summary",
    # models
    "VerticalId",
    "RightsRecord",
    "ValidationResult",
    "RightsValidationResult",
    "PropertyIdentitySummary",
    "RightType",
    "ValidationStatus",
    # exceptions
    "VerticalIdError",
    "VerticalIdValidationError",
    "ParsingError",
    "RightsValidationError",
]
