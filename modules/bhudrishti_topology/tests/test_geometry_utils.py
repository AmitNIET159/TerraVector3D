"""Tests for bhudrishti_topology.src.geometry_utils."""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from bhudrishti_topology.src.geometry_utils import (
    calculate_horizontal_overlap,
    calculate_overlap_metrics,
    calculate_overlap_volume,
    check_vertical_overlap,
    coords_to_polygon,
    is_closed_ring,
    is_polygon_within,
    validate_polygon,
)
from tests.conftest import make_unit


# ===================================================================
# coords_to_polygon
# ===================================================================


class TestCoordsToPolygon:
    def test_rectangle(self):
        poly = coords_to_polygon(
            [[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]]
        )
        assert isinstance(poly, Polygon)
        assert abs(poly.area - 50.0) < 1e-6

    def test_triangle(self):
        poly = coords_to_polygon([[0, 0], [10, 0], [5, 5], [0, 0]])
        assert poly.area > 0


# ===================================================================
# is_closed_ring
# ===================================================================


class TestIsClosedRing:
    def test_closed(self):
        assert is_closed_ring([[0, 0], [1, 0], [1, 1], [0, 0]]) is True

    def test_open(self):
        assert is_closed_ring([[0, 0], [1, 0], [1, 1]]) is False

    def test_too_few_points(self):
        assert is_closed_ring([[0, 0], [1, 0]]) is False

    def test_first_ne_last(self):
        assert (
            is_closed_ring([[0, 0], [1, 0], [1, 1], [0, 1]]) is False
        )


# ===================================================================
# validate_polygon
# ===================================================================


class TestValidatePolygon:
    def test_valid_square(self):
        ok, reason, poly = validate_polygon(
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        )
        assert ok is True
        assert reason == ""
        assert poly is not None

    def test_open_ring_fails(self):
        ok, reason, poly = validate_polygon(
            [[0, 0], [10, 0], [10, 10], [0, 10]]
        )
        assert ok is False
        assert "not closed" in reason

    def test_self_intersecting_bowtie(self):
        # A bowtie polygon (self‑intersecting)
        ok, reason, poly = validate_polygon(
            [[0, 0], [10, 10], [10, 0], [0, 10], [0, 0]]
        )
        assert ok is False
        assert "Invalid polygon" in reason or "Self-intersection" in reason


# ===================================================================
# calculate_horizontal_overlap
# ===================================================================


class TestHorizontalOverlap:
    def test_overlapping_rectangles(self):
        a = coords_to_polygon(
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        )
        b = coords_to_polygon(
            [[5, 0], [15, 0], [15, 10], [5, 10], [5, 0]]
        )
        area, geom = calculate_horizontal_overlap(a, b)
        assert abs(area - 50.0) < 1e-6
        assert geom is not None

    def test_non_overlapping(self):
        a = coords_to_polygon(
            [[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]
        )
        b = coords_to_polygon(
            [[10, 10], [15, 10], [15, 15], [10, 15], [10, 10]]
        )
        area, geom = calculate_horizontal_overlap(a, b)
        assert area == 0.0
        assert geom is None

    def test_touching_edge(self):
        a = coords_to_polygon(
            [[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]
        )
        b = coords_to_polygon(
            [[5, 0], [10, 0], [10, 5], [5, 5], [5, 0]]
        )
        area, _ = calculate_horizontal_overlap(a, b)
        assert area == 0.0  # Edge‑touching gives zero area

    def test_deliberate_3_4_sqm_overlap(self):
        """Reproduce the U401/U402 overlap from the conflict example."""
        a = coords_to_polygon(
            [[0, 0], [10.34, 0], [10.34, 10], [0, 10], [0, 0]]
        )
        b = coords_to_polygon(
            [[10.0, 0], [20, 0], [20, 10], [10.0, 10], [10.0, 0]]
        )
        area, _ = calculate_horizontal_overlap(a, b)
        assert abs(area - 3.4) < 0.01


# ===================================================================
# check_vertical_overlap
# ===================================================================


class TestVerticalOverlap:
    def test_overlapping(self):
        has, z_min, z_max = check_vertical_overlap(0, 3, 2, 5)
        assert has is True
        assert z_min == 2.0
        assert z_max == 3.0

    def test_no_overlap(self):
        has, z_min, z_max = check_vertical_overlap(0, 3, 3, 6)
        assert has is False

    def test_full_containment(self):
        has, z_min, z_max = check_vertical_overlap(0, 10, 2, 8)
        assert has is True
        assert z_min == 2.0
        assert z_max == 8.0

    def test_identical_ranges(self):
        has, z_min, z_max = check_vertical_overlap(9, 12, 9, 12)
        assert has is True
        assert z_min == 9.0
        assert z_max == 12.0


# ===================================================================
# calculate_overlap_volume
# ===================================================================


class TestOverlapVolume:
    def test_basic(self):
        vol = calculate_overlap_volume(3.4, 3.0)
        assert abs(vol - 10.2) < 0.01

    def test_zero(self):
        assert calculate_overlap_volume(0.0, 5.0) == 0.0


# ===================================================================
# is_polygon_within
# ===================================================================


class TestPolygonWithin:
    def test_inside(self):
        outer = coords_to_polygon(
            [[0, 0], [20, 0], [20, 10], [0, 10], [0, 0]]
        )
        inner = coords_to_polygon(
            [[1, 1], [10, 1], [10, 9], [1, 9], [1, 1]]
        )
        assert is_polygon_within(inner, outer) is True

    def test_outside(self):
        outer = coords_to_polygon(
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        )
        inner = coords_to_polygon(
            [[15, 15], [20, 15], [20, 20], [15, 20], [15, 15]]
        )
        assert is_polygon_within(inner, outer) is False

    def test_coincident_boundary(self):
        outer = coords_to_polygon(
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        )
        inner = coords_to_polygon(
            [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        )
        assert is_polygon_within(inner, outer) is True


# ===================================================================
# calculate_overlap_metrics (public convenience function)
# ===================================================================


class TestCalculateOverlapMetrics:
    def test_overlapping_units(self):
        ua = make_unit(
            "U401",
            "04",
            footprint=[
                [0, 0], [10.34, 0], [10.34, 10], [0, 10], [0, 0]
            ],
            z_min=9.0,
            z_max=12.0,
        )
        ub = make_unit(
            "U402",
            "04",
            footprint=[
                [10.0, 0], [20.0, 0], [20.0, 10], [10.0, 10], [10.0, 0]
            ],
            z_min=9.0,
            z_max=12.0,
        )
        m = calculate_overlap_metrics(ua, ub)
        assert m["has_overlap"] is True
        assert abs(m["horizontal_overlap_area_sqm"] - 3.4) < 0.01
        assert m["overlapping_z_min_m"] == 9.0
        assert m["overlapping_z_max_m"] == 12.0
        assert abs(m["estimated_overlap_volume_cum"] - 10.2) < 0.1

    def test_no_overlap(self):
        ua = make_unit(
            "A",
            "01",
            footprint=[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        ub = make_unit(
            "B",
            "02",
            footprint=[[10, 10], [15, 10], [15, 15], [10, 15], [10, 10]],
            z_min=3.0,
            z_max=6.0,
        )
        m = calculate_overlap_metrics(ua, ub)
        assert m["has_overlap"] is False
        assert m["estimated_overlap_volume_cum"] == 0.0

    def test_horizontal_only_no_vertical(self):
        ua = make_unit(
            "A",
            "01",
            footprint=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        ub = make_unit(
            "B",
            "02",
            footprint=[[5, 0], [15, 0], [15, 10], [5, 10], [5, 0]],
            z_min=3.0,
            z_max=6.0,
        )
        m = calculate_overlap_metrics(ua, ub)
        assert m["has_overlap"] is False
