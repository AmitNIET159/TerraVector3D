"""
Vertical-ID engine — generate, parse, validate, revise, and label
prototype vertical property IDs for BhuDrishti 3D.

ID format
---------
    <parent_ulpin>-F<level>-U<unit_code>-R<revision>

This is a **prototype extension** only.  It does NOT replace or
constitute an officially approved ULPIN format.
"""

from __future__ import annotations

import re

from .exceptions import ParsingError, VerticalIdValidationError
from .models import ValidationResult, VerticalId

# Canonical regex — kept as a module constant so other modules can
# reference the same compiled pattern.
VERTICAL_ID_PATTERN = re.compile(
    r"^([A-Z0-9]{14})-F(G|B[1-9]|[0-9]{2})-U([A-Z0-9]{1,16})-R([0-9]{2})$"
)


# ------------------------------------------------------------------
# 1. generate_vertical_id
# ------------------------------------------------------------------

def generate_vertical_id(
    parent_ulpin: str,
    level: str,
    unit_code: str,
    revision: int = 1,
) -> str:
    """
    Build a deterministic vertical-ID string from its components.

    Parameters
    ----------
    parent_ulpin : str
        Exactly 14 uppercase alphanumeric characters.
    level : str
        ``G``, ``B1``–``B9``, or ``01``–``99``.
    unit_code : str
        1-16 uppercase alphanumeric characters.
    revision : int, optional
        Revision number 1-99 (default ``1``).

    Returns
    -------
    str
        Formatted vertical-ID string.

    Raises
    ------
    pydantic.ValidationError
        If any component violates format rules.
    """
    vid = VerticalId(
        parent_ulpin=parent_ulpin,
        level=level,
        unit_code=unit_code,
        revision=revision,
    )
    return f"{vid.parent_ulpin}-F{vid.level}-U{vid.unit_code}-R{vid.revision:02d}"


# ------------------------------------------------------------------
# 2. parse_vertical_id
# ------------------------------------------------------------------

def parse_vertical_id(id_string: str) -> VerticalId:
    """
    Parse a vertical-ID string into a ``VerticalId`` model.

    Raises
    ------
    ParsingError
        With human-readable detail when the string is malformed.
    """
    if not isinstance(id_string, str):
        raise ParsingError(
            f"Expected a string, got {type(id_string).__name__}"
        )

    match = VERTICAL_ID_PATTERN.match(id_string.strip())
    if not match:
        errors = _get_detailed_parse_errors(id_string.strip())
        raise ParsingError(
            f"Invalid vertical ID format: '{id_string}'. "
            f"Errors: {'; '.join(errors)}"
        )

    parent_ulpin, level, unit_code, revision_str = match.groups()
    revision = int(revision_str)

    if revision < 1:
        raise ParsingError(
            "Revision must be between 01 and 99, got R00"
        )

    return VerticalId(
        parent_ulpin=parent_ulpin,
        level=level,
        unit_code=unit_code,
        revision=revision,
    )


# ------------------------------------------------------------------
# 3. validate_vertical_id
# ------------------------------------------------------------------

def validate_vertical_id(id_string: str) -> ValidationResult:
    """
    Validate a vertical-ID string against all format rules.

    Returns a ``ValidationResult`` with human-readable ``errors`` and
    ``warnings`` — never raises.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(id_string, str):
        return ValidationResult(
            is_valid=False,
            errors=[f"Expected a string, got {type(id_string).__name__}"],
        )

    id_string = id_string.strip()
    if not id_string:
        return ValidationResult(
            is_valid=False,
            errors=["Vertical ID string is empty"],
        )

    # ---- segment count ---------------------------------------------------
    parts = id_string.split("-")
    if len(parts) != 4:
        errors.append(
            f"Expected 4 segments separated by '-', got {len(parts)}: "
            f"'{id_string}'"
        )
        return ValidationResult(is_valid=False, errors=errors)

    ulpin_part, level_part, unit_part, rev_part = parts

    # ---- parent ULPIN ----------------------------------------------------
    if not re.fullmatch(r"[A-Z0-9]{14}", ulpin_part):
        if len(ulpin_part) != 14:
            errors.append(
                f"parent_ulpin must be exactly 14 characters, "
                f"got {len(ulpin_part)}: '{ulpin_part}'"
            )
        if not ulpin_part.isalnum() or ulpin_part != ulpin_part.upper():
            errors.append(
                f"parent_ulpin must contain only uppercase letters and "
                f"digits: '{ulpin_part}'"
            )

    # ---- level -----------------------------------------------------------
    if not level_part.startswith("F"):
        errors.append(
            f"Level segment must start with 'F', got: '{level_part}'"
        )
    else:
        level_val = level_part[1:]
        if not re.fullmatch(r"G|B[1-9]|[0-9]{2}", level_val):
            errors.append(
                f"Level must be G, B1-B9, or 01-99, got: '{level_val}'"
            )
        elif re.fullmatch(r"[0-9]{2}", level_val) and int(level_val) == 0:
            errors.append("Numeric level must be 01-99, not 00")

    # ---- unit code -------------------------------------------------------
    if not unit_part.startswith("U"):
        errors.append(
            f"Unit segment must start with 'U', got: '{unit_part}'"
        )
    else:
        unit_val = unit_part[1:]
        if not unit_val:
            errors.append("Unit code cannot be empty after 'U' prefix")
        elif len(unit_val) > 16:
            errors.append(
                f"Unit code must be at most 16 characters, "
                f"got {len(unit_val)}: '{unit_val}'"
            )
        elif not re.fullmatch(r"[A-Z0-9]+", unit_val):
            errors.append(
                f"Unit code must contain only uppercase letters and "
                f"digits: '{unit_val}'"
            )

    # ---- revision --------------------------------------------------------
    if not rev_part.startswith("R"):
        errors.append(
            f"Revision segment must start with 'R', got: '{rev_part}'"
        )
    else:
        rev_val = rev_part[1:]
        if not re.fullmatch(r"[0-9]{2}", rev_val):
            errors.append(
                f"Revision must be two digits (01-99), got: '{rev_val}'"
            )
        elif int(rev_val) < 1:
            errors.append(
                f"Revision must be between 01 and 99, got: R{rev_val}"
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ------------------------------------------------------------------
# 4. increment_revision
# ------------------------------------------------------------------

def increment_revision(id_string: str) -> str:
    """
    Return a new vertical-ID string with the revision bumped by one.

    Raises ``VerticalIdValidationError`` when the current revision is
    already R99.
    """
    vid = parse_vertical_id(id_string)
    if vid.revision >= 99:
        raise VerticalIdValidationError(
            "Cannot increment revision beyond R99",
            errors=["Revision R99 is the maximum allowed revision"],
        )
    return generate_vertical_id(
        parent_ulpin=vid.parent_ulpin,
        level=vid.level,
        unit_code=vid.unit_code,
        revision=vid.revision + 1,
    )


# ------------------------------------------------------------------
# 5. build_human_readable_label
# ------------------------------------------------------------------

def build_human_readable_label(id_string: str) -> str:
    """
    Return a display-friendly label such as
    ``"Floor 4, Unit 401, Revision 01"``.
    """
    vid = parse_vertical_id(id_string)
    level_display = _level_to_display(vid.level)
    return f"{level_display}, Unit {vid.unit_code}, Revision {vid.revision:02d}"


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _level_to_display(level: str) -> str:
    """Convert a level code to a human-readable string."""
    if level == "G":
        return "Ground Floor"
    if level.startswith("B"):
        return f"Basement {level[1:]}"
    return f"Floor {int(level)}"


def _get_detailed_parse_errors(id_string: str) -> list[str]:
    """Produce granular error messages for a malformed ID string."""
    errors: list[str] = []
    parts = id_string.split("-")

    if len(parts) != 4:
        errors.append(
            f"Expected 4 segments (ULPIN-F<level>-U<unit>-R<rev>), "
            f"got {len(parts)} segments"
        )
        return errors

    ulpin_part, level_part, unit_part, rev_part = parts

    if not re.fullmatch(r"[A-Z0-9]{14}", ulpin_part):
        errors.append(
            f"Invalid parent ULPIN: '{ulpin_part}' "
            f"(must be 14 uppercase alphanumeric chars)"
        )
    if not re.fullmatch(r"F(G|B[1-9]|[0-9]{2})", level_part):
        errors.append(
            f"Invalid level: '{level_part}' "
            f"(must be FG, FB1-FB9, or F01-F99)"
        )
    if not re.fullmatch(r"U[A-Z0-9]{1,16}", unit_part):
        errors.append(
            f"Invalid unit: '{unit_part}' "
            f"(must be U + 1-16 uppercase alphanumeric chars)"
        )
    if not re.fullmatch(r"R[0-9]{2}", rev_part):
        errors.append(
            f"Invalid revision: '{rev_part}' (must be R01-R99)"
        )
    elif int(rev_part[1:]) < 1:
        errors.append(
            f"Invalid revision: '{rev_part}' (must be R01-R99, not R00)"
        )

    if not errors:
        errors.append("Unknown format error")

    return errors
