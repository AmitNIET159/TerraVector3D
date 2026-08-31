"""Core topology validation engine for BhuDrishti 3D.

Implements the five required public functions:

1. ``validate_building``
2. ``validate_spatial_units``
3. ``detect_volume_conflicts``
4. ``calculate_overlap_metrics``   (re-exported from geometry_utils)
5. ``generate_validation_summary``

The engine uses a **2.5-D cadastral** method:
* Each unit has a 2-D footprint polygon (local-metre coordinates).
* ``z_min_m`` / ``z_max_m`` define its vertical extent.
* A volumetric conflict exists only when horizontal **and** vertical
  overlap are both present.
"""

from __future__ import annotations

import itertools
from collections import Counter
from typing import Dict, List, Optional, Set

from shapely.geometry import Polygon

from .conflict_classifier import classify_overlap, classify_single_unit_issue
from .geometry_utils import (
    calculate_horizontal_overlap,
    calculate_overlap_volume,
    check_vertical_overlap,
    coords_to_polygon,
    is_polygon_within,
    validate_polygon,
)
from .models import (
    BuildingInput,
    ConflictResult,
    ConflictType,
    LevelInfo,
    Severity,
    SpatialUnit,
    ValidationSummary,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_level_map(levels: List[LevelInfo]) -> Dict[str, LevelInfo]:
    """Return a mapping from ``level_code`` → ``LevelInfo``."""
    return {lv.level_code: lv for lv in levels}


def _make_conflict(
    conflict_type: ConflictType,
    severity: Severity,
    affected_unit_ids: List[str],
    affected_vertical_ids: List[str],
    recommended_action: str,
    explanation: str,
    h_area: float = 0.0,
    z_min: float = 0.0,
    z_max: float = 0.0,
    volume: float = 0.0,
) -> ConflictResult:
    return ConflictResult(
        conflict_type=conflict_type,
        severity=severity,
        affected_unit_ids=affected_unit_ids,
        affected_vertical_ids=affected_vertical_ids,
        horizontal_overlap_area_sqm=round(h_area, 6),
        overlapping_z_min_m=z_min,
        overlapping_z_max_m=z_max,
        estimated_overlap_volume_cum=round(volume, 6),
        recommended_action=recommended_action,
        human_readable_explanation=explanation,
    )


# ---------------------------------------------------------------------------
# 1 – Single-unit validation  (validate_spatial_units)
# ---------------------------------------------------------------------------


def validate_spatial_units(
    spatial_units: List[SpatialUnit],
    building: BuildingInput,
) -> List[ConflictResult]:
    """Validate every spatial unit individually against the building.

    Checks:
    * Invalid / self-intersecting polygon
    * Open polygon ring
    * Invalid z range (``z_min >= z_max``)
    * Negative declared area
    * Unit outside building footprint
    * Unit not assigned to a valid level
    * Floating unit / gap warning
    * Unit extending beyond total building height
    * Duplicate vertical IDs
    """
    conflicts: List[ConflictResult] = []

    level_map = _build_level_map(building.levels)

    # Pre-build building polygon
    bld_valid, _, bld_poly = validate_polygon(building.footprint)

    # Track vertical IDs for duplicate detection
    seen_vertical_ids: Dict[str, str] = {}  # vertical_id → unit_id

    for unit in spatial_units:
        # -- Duplicate vertical ID -------------------------------------
        if unit.vertical_id in seen_vertical_ids:
            existing_uid = seen_vertical_ids[unit.vertical_id]
            ct, sev = ConflictType.DUPLICATE_VERTICAL_ID, Severity.HIGH
            conflicts.append(
                _make_conflict(
                    ct,
                    sev,
                    [existing_uid, unit.unit_id],
                    [unit.vertical_id],
                    "Assign unique vertical IDs to each unit.",
                    f"Vertical ID '{unit.vertical_id}' is shared by "
                    f"units {existing_uid} and {unit.unit_id}.",
                )
            )
        else:
            seen_vertical_ids[unit.vertical_id] = unit.unit_id

        # -- Polygon validity ------------------------------------------
        ring_closed = True
        if not _is_ring_closed(unit.footprint):
            ring_closed = False
            ct, sev, action, expl = classify_single_unit_issue(
                "open_ring", unit
            )
            conflicts.append(
                _make_conflict(
                    ct, sev, [unit.unit_id], [unit.vertical_id],
                    action, expl,
                )
            )

        poly_valid, reason, unit_poly = validate_polygon(unit.footprint)
        if not poly_valid and ring_closed:
            # Only report if we haven't already flagged open ring
            ct, sev, action, expl = classify_single_unit_issue(
                "invalid_geometry", unit, reason
            )
            conflicts.append(
                _make_conflict(
                    ct, sev, [unit.unit_id], [unit.vertical_id],
                    action, expl,
                )
            )

        # -- Z range ---------------------------------------------------
        if unit.z_min_m >= unit.z_max_m:
            ct, sev, action, expl = classify_single_unit_issue(
                "invalid_z_range", unit
            )
            conflicts.append(
                _make_conflict(
                    ct, sev, [unit.unit_id], [unit.vertical_id],
                    action, expl,
                )
            )

        # -- Negative area ---------------------------------------------
        if unit.area_sqm < 0:
            ct, sev, action, expl = classify_single_unit_issue(
                "negative_area", unit
            )
            conflicts.append(
                _make_conflict(
                    ct, sev, [unit.unit_id], [unit.vertical_id],
                    action, expl,
                )
            )

        # -- Unit outside building footprint ---------------------------
        if bld_valid and poly_valid and unit_poly is not None:
            assert bld_poly is not None
            if not is_polygon_within(unit_poly, bld_poly):
                ct, sev, action, expl = classify_single_unit_issue(
                    "unit_outside_building", unit
                )
                conflicts.append(
                    _make_conflict(
                        ct, sev, [unit.unit_id], [unit.vertical_id],
                        action, expl,
                    )
                )

        # -- Level assignment ------------------------------------------
        if unit.level_code not in level_map:
            ct, sev, action, expl = classify_single_unit_issue(
                "level_assignment_error", unit
            )
            conflicts.append(
                _make_conflict(
                    ct, sev, [unit.unit_id], [unit.vertical_id],
                    action, expl,
                )
            )
        else:
            level = level_map[unit.level_code]
            # Floating unit: unit z_min is above level z_min by > 0.5 m
            if unit.z_min_m > level.z_min_m + 0.5:
                ct, sev, action, expl = classify_single_unit_issue(
                    "floating_unit",
                    unit,
                    f"Unit z_min ({unit.z_min_m}) is above level "
                    f"z_min ({level.z_min_m}) by "
                    f"{unit.z_min_m - level.z_min_m:.2f} m.",
                )
                conflicts.append(
                    _make_conflict(
                        ct, sev, [unit.unit_id], [unit.vertical_id],
                        action, expl,
                    )
                )

        # -- Exceeds building height -----------------------------------
        if unit.z_max_m > building.total_height_m:
            ct, sev, action, expl = classify_single_unit_issue(
                "exceeds_building_height",
                unit,
                f"Unit z_max ({unit.z_max_m}) > building height "
                f"({building.total_height_m}).",
            )
            conflicts.append(
                _make_conflict(
                    ct, sev, [unit.unit_id], [unit.vertical_id],
                    action, expl,
                )
            )

    return conflicts


def _is_ring_closed(coords: List[List[float]]) -> bool:
    """Fast closed-ring check."""
    if len(coords) < 4:
        return False
    return (
        coords[0][0] == coords[-1][0] and coords[0][1] == coords[-1][1]
    )


# ---------------------------------------------------------------------------
# 2 – Pairwise volume conflict detection  (detect_volume_conflicts)
# ---------------------------------------------------------------------------


def detect_volume_conflicts(
    spatial_units: List[SpatialUnit],
) -> List[ConflictResult]:
    """Detect volumetric (2.5-D) conflicts between all unit pairs.

    A conflict exists when **both** horizontal polygon overlap **and**
    vertical height overlap are present.
    """
    conflicts: List[ConflictResult] = []

    # Pre-compute polygons (skip invalid ones)
    polys: Dict[str, Optional[Polygon]] = {}
    for u in spatial_units:
        valid, _, poly = validate_polygon(u.footprint)
        polys[u.unit_id] = poly if valid else None

    unit_map = {u.unit_id: u for u in spatial_units}

    for ua, ub in itertools.combinations(spatial_units, 2):
        poly_a = polys.get(ua.unit_id)
        poly_b = polys.get(ub.unit_id)
        if poly_a is None or poly_b is None:
            continue

        h_area, _ = calculate_horizontal_overlap(poly_a, poly_b)
        if h_area < 1e-9:
            continue

        has_v, v_min, v_max = check_vertical_overlap(
            ua.z_min_m, ua.z_max_m, ub.z_min_m, ub.z_max_m
        )
        if not has_v:
            continue

        volume = calculate_overlap_volume(h_area, v_max - v_min)

        ct, sev, action, expl = classify_overlap(ua, ub, h_area)

        conflicts.append(
            _make_conflict(
                ct,
                sev,
                [ua.unit_id, ub.unit_id],
                [ua.vertical_id, ub.vertical_id],
                action,
                expl,
                h_area,
                v_min,
                v_max,
                volume,
            )
        )

    return conflicts


# ---------------------------------------------------------------------------
# 3 – Summary generation  (generate_validation_summary)
# ---------------------------------------------------------------------------


def generate_validation_summary(
    building_input: BuildingInput,
    conflicts: List[ConflictResult],
) -> ValidationSummary:
    """Build a ``ValidationSummary`` from a list of conflicts."""
    by_severity = Counter(c.severity.value for c in conflicts)
    by_type = Counter(c.conflict_type.value for c in conflicts)

    has_high = by_severity.get("high", 0) > 0

    return ValidationSummary(
        building_id=building_input.building_id,
        parent_ulpin=building_input.parent_ulpin,
        total_units=len(building_input.spatial_units),
        total_conflicts=len(conflicts),
        conflicts_by_severity=dict(by_severity),
        conflicts_by_type=dict(by_type),
        conflicts=conflicts,
        is_valid=len(conflicts) == 0 or not has_high,
    )


# ---------------------------------------------------------------------------
# 4 – Top-level orchestrator  (validate_building)
# ---------------------------------------------------------------------------


def validate_building(building_input: BuildingInput) -> ValidationSummary:
    """Run the full validation pipeline on a building.

    1. Validate each spatial unit individually.
    2. Detect pairwise volume conflicts.
    3. Generate a summary.
    """
    unit_conflicts = validate_spatial_units(
        building_input.spatial_units, building_input
    )
    volume_conflicts = detect_volume_conflicts(
        building_input.spatial_units
    )

    all_conflicts = unit_conflicts + volume_conflicts

    return generate_validation_summary(building_input, all_conflicts)
