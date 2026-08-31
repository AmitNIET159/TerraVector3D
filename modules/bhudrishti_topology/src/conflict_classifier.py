"""Classify spatial conflicts and assign severity.

The classifier determines the ``ConflictType`` and ``Severity`` for
every pair of overlapping spatial units, taking into account unit types
(apartment, parking, utility, easement, …).
"""

from __future__ import annotations

from typing import Tuple

from .models import ConflictType, Severity, SpatialUnit


# ---------------------------------------------------------------------------
# Unit-type sets used for classification
# ---------------------------------------------------------------------------

_HARD_TYPES = {"apartment", "commercial"}
_PARKING_TYPES = {"parking"}
_SOFT_TYPES = {"utility", "easement", "common_area"}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def classify_overlap(
    unit_a: SpatialUnit,
    unit_b: SpatialUnit,
    horizontal_area: float,
) -> Tuple[ConflictType, Severity, str, str]:
    """Determine the conflict type and severity for an overlapping pair.

    Parameters
    ----------
    unit_a, unit_b:
        The two overlapping spatial units.
    horizontal_area:
        Horizontal overlap area in m².

    Returns
    -------
    tuple of (ConflictType, Severity, recommended_action, explanation)
    """
    types = {unit_a.unit_type, unit_b.unit_type}

    # ---- Parking / Apartment overlap ---------------------------------
    if types & _HARD_TYPES and types & _PARKING_TYPES:
        return (
            ConflictType.PARKING_APARTMENT_OVERLAP,
            Severity.HIGH,
            (
                "Reassign parking or apartment boundaries so they do "
                "not share the same volume."
            ),
            (
                f"Parking unit and apartment/commercial unit overlap "
                f"horizontally by {horizontal_area:.2f} sq m in the same "
                f"vertical range.  This is a high-severity conflict "
                f"requiring immediate boundary correction."
            ),
        )

    # ---- Utility / Easement (allowed but needs review) ---------------
    if types.issubset(_SOFT_TYPES):
        return (
            ConflictType.UTILITY_EASEMENT_REVIEW,
            Severity.LOW,
            (
                "Review utility and easement boundaries; overlap may "
                "be permissible but must be documented."
            ),
            (
                f"Utility/easement units overlap horizontally by "
                f"{horizontal_area:.2f} sq m.  This overlap is "
                f"potentially acceptable but requires formal review."
            ),
        )

    # ---- Mixed soft + hard (utility crossing an apartment, etc.) -----
    if types & _SOFT_TYPES and types & _HARD_TYPES:
        return (
            ConflictType.UTILITY_EASEMENT_REVIEW,
            Severity.MEDIUM,
            (
                "Verify that the utility/easement through the "
                "apartment/commercial unit is legally registered."
            ),
            (
                f"A utility or easement unit overlaps with an "
                f"apartment/commercial unit by {horizontal_area:.2f} sq m.  "
                f"Medium severity — requires legal review."
            ),
        )

    # ---- Parking + soft (utility/easement in parking area) -----------
    if types & _PARKING_TYPES and types & _SOFT_TYPES:
        return (
            ConflictType.UTILITY_EASEMENT_REVIEW,
            Severity.LOW,
            (
                "Review utility/easement overlap with parking; "
                "overlap may be permissible but must be documented."
            ),
            (
                f"Parking and utility/easement units overlap "
                f"horizontally by {horizontal_area:.2f} sq m.  "
                f"This overlap is potentially acceptable but "
                f"requires formal review."
            ),
        )

    # ---- Default: two hard units (apartment × apartment, etc.) -------
    return (
        ConflictType.VOLUME_OVERLAP,
        Severity.HIGH,
        (
            "Survey and adjust unit boundaries to eliminate the "
            "volumetric overlap."
        ),
        (
            f"Units overlap horizontally by {horizontal_area:.2f} sq m "
            f"within the same vertical range.  This is a high-severity "
            f"ownership conflict requiring immediate resolution."
        ),
    )


def classify_single_unit_issue(
    issue_kind: str,
    unit: SpatialUnit,
    detail: str = "",
) -> Tuple[ConflictType, Severity, str, str]:
    """Classify a validation issue that affects a single unit.

    ``issue_kind`` is one of:
    * ``invalid_geometry``
    * ``open_ring``
    * ``invalid_z_range``
    * ``negative_area``
    * ``unit_outside_building``
    * ``level_assignment_error``
    * ``floating_unit``
    * ``exceeds_building_height``
    """
    _map = {
        "invalid_geometry": (
            ConflictType.INVALID_GEOMETRY,
            Severity.HIGH,
            "Fix the polygon geometry (remove self-intersections).",
            f"Unit {unit.unit_id} has invalid or self-intersecting "
            f"geometry. {detail}",
        ),
        "open_ring": (
            ConflictType.INVALID_GEOMETRY,
            Severity.HIGH,
            "Close the polygon ring (first coordinate must equal last).",
            f"Unit {unit.unit_id} has an open polygon ring. {detail}",
        ),
        "invalid_z_range": (
            ConflictType.INVALID_Z_RANGE,
            Severity.HIGH,
            "Correct z_min_m / z_max_m so that z_min < z_max.",
            f"Unit {unit.unit_id} has an invalid z range "
            f"(z_min={unit.z_min_m}, z_max={unit.z_max_m}). {detail}",
        ),
        "negative_area": (
            ConflictType.INVALID_GEOMETRY,
            Severity.HIGH,
            "Provide a positive area_sqm value.",
            f"Unit {unit.unit_id} has a negative area "
            f"({unit.area_sqm} sq m). {detail}",
        ),
        "unit_outside_building": (
            ConflictType.UNIT_OUTSIDE_BUILDING,
            Severity.MEDIUM,
            "Adjust the unit footprint to fall within the building "
            "boundary.",
            f"Unit {unit.unit_id} extends beyond the building "
            f"footprint. {detail}",
        ),
        "level_assignment_error": (
            ConflictType.LEVEL_ASSIGNMENT_ERROR,
            Severity.MEDIUM,
            "Assign the unit to an existing building level or add "
            "the missing level definition.",
            f"Unit {unit.unit_id} references level '{unit.level_code}' "
            f"which is not defined for the building. {detail}",
        ),
        "floating_unit": (
            ConflictType.FLOATING_UNIT_WARNING,
            Severity.LOW,
            "Verify there is no unintended vertical gap below this "
            "unit.",
            f"Unit {unit.unit_id} appears to float above its assigned "
            f"level's z_min_m. {detail}",
        ),
        "exceeds_building_height": (
            ConflictType.INVALID_Z_RANGE,
            Severity.MEDIUM,
            "Reduce unit height or update the building's "
            "total_height_m.",
            f"Unit {unit.unit_id} extends above the building's "
            f"total height. {detail}",
        ),
    }

    entry = _map.get(issue_kind)
    if entry is None:
        return (
            ConflictType.INVALID_GEOMETRY,
            Severity.MEDIUM,
            "Investigate the reported issue.",
            f"Unit {unit.unit_id}: unknown issue '{issue_kind}'. "
            f"{detail}",
        )
    return entry
