"""Geometry helper functions for 2.5-D cadastral topology validation.

All coordinates are in local Cartesian metres (never lat/lon).
A "volumetric" overlap exists when **both** horizontal polygon overlap
**and** vertical height-range overlap are present.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from shapely.geometry import Polygon
from shapely.validation import explain_validity

from .models import SpatialUnit


# ---------------------------------------------------------------------------
# Polygon construction helpers
# ---------------------------------------------------------------------------


def coords_to_polygon(coords: List[List[float]]) -> Polygon:
    """Convert a list of ``[x, y]`` pairs to a Shapely ``Polygon``.

    The coordinate list **must** form a closed ring (first == last).
    """
    tuples = [(c[0], c[1]) for c in coords]
    return Polygon(tuples)


# ---------------------------------------------------------------------------
# Polygon validation
# ---------------------------------------------------------------------------


def is_closed_ring(coords: List[List[float]]) -> bool:
    """Return ``True`` if the coordinate ring is closed.

    A valid closed ring has ≥ 4 vertices and its first vertex equals
    its last vertex.
    """
    if len(coords) < 4:
        return False
    return coords[0][0] == coords[-1][0] and coords[0][1] == coords[-1][1]


def validate_polygon(
    coords: List[List[float]],
) -> Tuple[bool, str, Optional[Polygon]]:
    """Validate a coordinate ring and return ``(is_valid, reason, polygon)``.

    Checks performed:
    * Ring is closed.
    * Polygon is non-empty and geometrically valid (not self-intersecting).

    Returns the constructed ``Polygon`` on success so callers avoid
    re-building it.
    """
    if not is_closed_ring(coords):
        return False, "Polygon ring is not closed", None

    poly = coords_to_polygon(coords)

    if poly.is_empty:
        return False, "Polygon is empty", None

    if not poly.is_valid:
        reason = explain_validity(poly)
        return False, f"Invalid polygon: {reason}", None

    return True, "", poly


# ---------------------------------------------------------------------------
# Overlap calculations
# ---------------------------------------------------------------------------


def calculate_horizontal_overlap(
    poly_a: Polygon, poly_b: Polygon
) -> Tuple[float, Optional[Polygon]]:
    """Return ``(overlap_area, intersection_geometry)`` for two polygons.

    If the polygons do not intersect the area is ``0.0`` and geometry is
    ``None``.
    """
    if not poly_a.intersects(poly_b):
        return 0.0, None

    intersection = poly_a.intersection(poly_b)
    area = intersection.area
    if area < 1e-9:
        return 0.0, None
    return area, intersection


def check_vertical_overlap(
    z_min_a: float,
    z_max_a: float,
    z_min_b: float,
    z_max_b: float,
) -> Tuple[bool, float, float]:
    """Check whether two vertical ranges overlap.

    Returns ``(has_overlap, overlap_z_min, overlap_z_max)``.
    """
    overlap_min = max(z_min_a, z_min_b)
    overlap_max = min(z_max_a, z_max_b)
    if overlap_min < overlap_max:
        return True, overlap_min, overlap_max
    return False, 0.0, 0.0


def calculate_overlap_volume(
    horizontal_area: float, z_overlap_height: float
) -> float:
    """Return the estimated overlap volume in cubic metres."""
    return round(horizontal_area * z_overlap_height, 6)


# ---------------------------------------------------------------------------
# Containment
# ---------------------------------------------------------------------------


def is_polygon_within(
    inner: Polygon, outer: Polygon, tolerance: float = 0.01
) -> bool:
    """Return ``True`` if *inner* lies within *outer* (with tolerance).

    A small negative buffer on *inner* and positive buffer on *outer*
    is applied to avoid false negatives from floating-point artefacts.
    """
    if inner.within(outer):
        return True
    return inner.buffer(-tolerance).within(outer.buffer(tolerance))


# ---------------------------------------------------------------------------
# Public convenience function (one of the 5 required public APIs)
# ---------------------------------------------------------------------------


def calculate_overlap_metrics(
    unit_a: SpatialUnit, unit_b: SpatialUnit
) -> Dict:
    """Calculate full overlap metrics between two spatial units.

    Returns a dictionary with the keys:
    * ``has_overlap`` – bool
    * ``horizontal_overlap_area_sqm`` – float
    * ``overlapping_z_min_m`` – float
    * ``overlapping_z_max_m`` – float
    * ``estimated_overlap_volume_cum`` – float (cubic metres)
    """
    result: Dict = {
        "has_overlap": False,
        "horizontal_overlap_area_sqm": 0.0,
        "overlapping_z_min_m": 0.0,
        "overlapping_z_max_m": 0.0,
        "estimated_overlap_volume_cum": 0.0,
    }

    # ---- Horizontal --------------------------------------------------
    valid_a, _, poly_a = validate_polygon(unit_a.footprint)
    valid_b, _, poly_b = validate_polygon(unit_b.footprint)
    if not (valid_a and valid_b):
        return result

    h_area, _ = calculate_horizontal_overlap(poly_a, poly_b)
    if h_area < 1e-9:
        return result

    # ---- Vertical ----------------------------------------------------
    has_v, v_min, v_max = check_vertical_overlap(
        unit_a.z_min_m, unit_a.z_max_m, unit_b.z_min_m, unit_b.z_max_m
    )
    if not has_v:
        return result

    volume = calculate_overlap_volume(h_area, v_max - v_min)

    result.update(
        {
            "has_overlap": True,
            "horizontal_overlap_area_sqm": round(h_area, 6),
            "overlapping_z_min_m": v_min,
            "overlapping_z_max_m": v_max,
            "estimated_overlap_volume_cum": volume,
        }
    )
    return result
