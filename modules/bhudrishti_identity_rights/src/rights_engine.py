"""
Rights engine — validate property-right records, check unit
compatibility, and build property-identity summaries.

The canonical holder field is ``holder_name_masked`` everywhere.

This is a **prototype extension** only.  It does NOT replace or
constitute an officially approved ULPIN format.
"""

from __future__ import annotations

from datetime import date

from .exceptions import ParsingError
from .models import (
    PropertyIdentitySummary,
    RightsRecord,
    RightsValidationResult,
    RightType,
    ValidationResult,
    ValidationStatus,
)
from .vertical_id_engine import (
    build_human_readable_label,
    parse_vertical_id,
    validate_vertical_id,
)


# ------------------------------------------------------------------
# 6. validate_unit_against_parent
# ------------------------------------------------------------------

def validate_unit_against_parent(
    vertical_id_str: str,
    parent_ulpin: str,
) -> ValidationResult:
    """
    Confirm that the ULPIN embedded inside *vertical_id_str* matches the
    separately provided *parent_ulpin*.
    """
    errors: list[str] = []
    warnings: list[str] = []

    try:
        vid = parse_vertical_id(vertical_id_str)
    except ParsingError as exc:
        return ValidationResult(is_valid=False, errors=[str(exc)])

    if vid.parent_ulpin != parent_ulpin:
        errors.append(
            f"Parent ULPIN mismatch: ID contains '{vid.parent_ulpin}' "
            f"but expected '{parent_ulpin}'"
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ------------------------------------------------------------------
# 7. validate_rights_record
# ------------------------------------------------------------------

def validate_rights_record(record: dict) -> RightsValidationResult:
    """
    Validate a rights-record dict and return a status plus a transparent
    audit trail explaining every decision.

    Expected dict keys (cross-module compatible with BhuDrishti
    evidence-report)::

        vertical_id, right_type, holder_name_masked,
        start_date, end_date, notes

    Returns
    -------
    RightsValidationResult
        ``status`` is one of ``valid``, ``needs_review``, ``invalid``.
    """
    errors: list[str] = []
    warnings: list[str] = []
    audit: list[str] = []

    # ---- required fields -------------------------------------------------
    required = ["vertical_id", "right_type", "holder_name_masked", "start_date"]
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: '{field}'")
            audit.append(f"FAIL: Required field '{field}' is missing.")

    if errors:
        return RightsValidationResult(
            status=ValidationStatus.invalid,
            errors=errors,
            warnings=warnings,
            audit_explanation=audit,
        )

    # ---- vertical_id -----------------------------------------------------
    vertical_id_str: str = record["vertical_id"]
    id_result = validate_vertical_id(vertical_id_str)
    if not id_result.is_valid:
        for err in id_result.errors:
            errors.append(f"Invalid vertical_id: {err}")
            audit.append(f"FAIL: Vertical ID validation — {err}")
    else:
        audit.append(f"PASS: Vertical ID '{vertical_id_str}' is well-formed.")

    # ---- right_type ------------------------------------------------------
    right_type_str: str = record["right_type"]
    right_type: RightType | None = None
    try:
        right_type = RightType(right_type_str)
        audit.append(f"PASS: Right type '{right_type.value}' is recognized.")
    except ValueError:
        valid_names = [rt.value for rt in RightType]
        errors.append(
            f"Invalid right_type: '{right_type_str}'. "
            f"Must be one of: {valid_names}"
        )
        audit.append(f"FAIL: Right type '{right_type_str}' is not recognized.")

    # ---- holder masking --------------------------------------------------
    holder: str = record["holder_name_masked"]
    if _is_holder_masked(holder):
        audit.append(f"PASS: Holder name '{holder}' is properly masked.")
    else:
        errors.append(
            f"Holder name must be masked (contain '*'): got '{holder}'"
        )
        audit.append(
            f"FAIL: Holder name '{holder}' is not masked — "
            f"must contain at least one '*'."
        )

    # ---- dates -----------------------------------------------------------
    start_date = _coerce_date(record["start_date"], "start_date", errors, audit)
    end_date = _coerce_date(
        record.get("end_date"), "end_date", errors, audit,
    ) if record.get("end_date") is not None else None

    if start_date and end_date and end_date <= start_date:
        errors.append(
            f"end_date ({end_date}) must be after start_date ({start_date})"
        )
        audit.append(
            f"FAIL: End date {end_date} is not after start date {start_date}."
        )

    # ---- parking / utility compatibility ---------------------------------
    if right_type and id_result.is_valid:
        _check_unit_right_compatibility(
            vertical_id_str, right_type, errors, audit,
        )

    # ---- determine status ------------------------------------------------
    status = ValidationStatus.invalid if errors else ValidationStatus.valid

    return RightsValidationResult(
        status=status,
        errors=errors,
        warnings=warnings,
        audit_explanation=audit,
    )


# ------------------------------------------------------------------
# 8. build_property_identity_summary
# ------------------------------------------------------------------

def build_property_identity_summary(
    vertical_id_str: str,
    rights_records: list[dict],
) -> PropertyIdentitySummary:
    """
    Build a comprehensive property-identity summary combining parsed ID
    data, human-readable labels, and validated rights records.
    """
    vid = parse_vertical_id(vertical_id_str)
    label = build_human_readable_label(vertical_id_str)
    level_display = _level_to_display(vid.level)

    validated_records: list[RightsRecord] = []
    validation_results: list[RightsValidationResult] = []
    statuses: list[ValidationStatus] = []

    # Track right-type counts for duplicate detection
    seen_types: dict[str, int] = {}

    for record in rights_records:
        rt = record.get("right_type", "")
        result = validate_rights_record(record)

        # Duplicate detection
        seen_types[rt] = seen_types.get(rt, 0) + 1
        if seen_types[rt] > 1:
            result.warnings.append(
                f"Duplicate right_type '{rt}' detected — review required."
            )
            result.audit_explanation.append(
                f"WARNING: Duplicate right_type '{rt}' found. "
                f"Flagging for review."
            )
            if result.status == ValidationStatus.valid:
                result.status = ValidationStatus.needs_review

        # Try to materialise a RightsRecord model for the summary
        try:
            rr = RightsRecord(
                vertical_id=record.get("vertical_id", ""),
                right_type=record.get("right_type", "ownership"),
                holder_name_masked=record.get("holder_name_masked", ""),
                start_date=record.get("start_date", "2025-01-01"),
                end_date=record.get("end_date"),
                notes=record.get("notes"),
            )
            validated_records.append(rr)
        except Exception:
            pass  # validation result already captures the errors

        validation_results.append(result)
        statuses.append(result.status)

    # Overall status — worst wins
    if ValidationStatus.invalid in statuses:
        overall = ValidationStatus.invalid
    elif ValidationStatus.needs_review in statuses:
        overall = ValidationStatus.needs_review
    else:
        overall = ValidationStatus.valid

    return PropertyIdentitySummary(
        vertical_id=vertical_id_str,
        parent_ulpin=vid.parent_ulpin,
        level_display=level_display,
        unit_code=vid.unit_code,
        revision=vid.revision,
        human_readable_label=label,
        rights_records=validated_records,
        rights_validation_results=validation_results,
        overall_status=overall,
    )


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _is_holder_masked(holder: str) -> bool:
    """Return ``True`` if *holder* contains at least one ``*``."""
    return bool(holder) and isinstance(holder, str) and "*" in holder


def _coerce_date(
    value: str | date | None,
    field_name: str,
    errors: list[str],
    audit: list[str],
) -> date | None:
    """Convert an ISO-format string to ``date``, appending errors."""
    if value is None:
        return None
    if isinstance(value, date):
        audit.append(f"PASS: {field_name} '{value}' is valid.")
        return value
    try:
        parsed = date.fromisoformat(value)
        audit.append(f"PASS: {field_name} '{parsed}' is valid.")
        return parsed
    except (ValueError, TypeError):
        errors.append(
            f"Invalid {field_name} format: '{value}'. "
            f"Use ISO format (YYYY-MM-DD)."
        )
        audit.append(
            f"FAIL: {field_name} '{value}' is not valid ISO format."
        )
        return None


def _check_unit_right_compatibility(
    vertical_id_str: str,
    right_type: RightType,
    errors: list[str],
    audit: list[str],
) -> None:
    """Enforce parking / utility unit-code constraints."""
    try:
        vid = parse_vertical_id(vertical_id_str)
    except ParsingError:
        return  # already handled upstream

    unit_upper = vid.unit_code.upper()

    if right_type == RightType.parking_right:
        if "PARK" not in unit_upper:
            errors.append(
                f"parking_right is only valid for parking units "
                f"(unit_code must contain 'PARK'). "
                f"Got unit_code: '{vid.unit_code}'"
            )
            audit.append(
                f"FAIL: parking_right assigned to non-parking unit "
                f"'{vid.unit_code}'. Unit code must contain 'PARK'."
            )
        else:
            audit.append(
                f"PASS: parking_right is compatible with parking unit "
                f"'{vid.unit_code}'."
            )

    if right_type == RightType.utility_easement:
        if "UTIL" not in unit_upper:
            errors.append(
                f"utility_easement is only valid for utility corridor "
                f"units (unit_code must contain 'UTIL'). "
                f"Got unit_code: '{vid.unit_code}'"
            )
            audit.append(
                f"FAIL: utility_easement assigned to non-utility unit "
                f"'{vid.unit_code}'. Unit code must contain 'UTIL'."
            )
        else:
            audit.append(
                f"PASS: utility_easement is compatible with utility unit "
                f"'{vid.unit_code}'."
            )


def _level_to_display(level: str) -> str:
    """Convert a level code to a human-readable string."""
    if level == "G":
        return "Ground Floor"
    if level.startswith("B"):
        return f"Basement {level[1:]}"
    return f"Floor {int(level)}"
