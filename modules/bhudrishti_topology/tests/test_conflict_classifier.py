"""Tests for bhudrishti_topology.src.conflict_classifier."""

from __future__ import annotations

import pytest

from bhudrishti_topology.src.conflict_classifier import (
    classify_overlap,
    classify_single_unit_issue,
)
from bhudrishti_topology.src.models import ConflictType, Severity
from tests.conftest import make_unit


# ===================================================================
# classify_overlap
# ===================================================================


class TestClassifyOverlap:
    def test_apartment_apartment(self):
        ua = make_unit("A", "01", unit_type="apartment")
        ub = make_unit("B", "01", unit_type="apartment")
        ct, sev, action, expl = classify_overlap(ua, ub, 5.0)
        assert ct == ConflictType.VOLUME_OVERLAP
        assert sev == Severity.HIGH

    def test_parking_apartment(self):
        park = make_unit("P", "01", unit_type="parking")
        apt = make_unit("A", "01", unit_type="apartment")
        ct, sev, _, _ = classify_overlap(park, apt, 10.0)
        assert ct == ConflictType.PARKING_APARTMENT_OVERLAP
        assert sev == Severity.HIGH

    def test_apartment_parking_reversed(self):
        apt = make_unit("A", "01", unit_type="apartment")
        park = make_unit("P", "01", unit_type="parking")
        ct, sev, _, _ = classify_overlap(apt, park, 10.0)
        assert ct == ConflictType.PARKING_APARTMENT_OVERLAP

    def test_utility_easement(self):
        util = make_unit("U", "01", unit_type="utility")
        ease = make_unit("E", "01", unit_type="easement")
        ct, sev, _, _ = classify_overlap(util, ease, 3.0)
        assert ct == ConflictType.UTILITY_EASEMENT_REVIEW
        assert sev == Severity.LOW

    def test_utility_utility(self):
        u1 = make_unit("U1", "01", unit_type="utility")
        u2 = make_unit("U2", "01", unit_type="utility")
        ct, sev, _, _ = classify_overlap(u1, u2, 2.0)
        assert ct == ConflictType.UTILITY_EASEMENT_REVIEW
        assert sev == Severity.LOW

    def test_commercial_commercial(self):
        c1 = make_unit("C1", "01", unit_type="commercial")
        c2 = make_unit("C2", "01", unit_type="commercial")
        ct, sev, _, _ = classify_overlap(c1, c2, 7.0)
        assert ct == ConflictType.VOLUME_OVERLAP
        assert sev == Severity.HIGH

    def test_utility_apartment_medium(self):
        util = make_unit("U", "01", unit_type="utility")
        apt = make_unit("A", "01", unit_type="apartment")
        ct, sev, _, _ = classify_overlap(util, apt, 4.0)
        assert ct == ConflictType.UTILITY_EASEMENT_REVIEW
        assert sev == Severity.MEDIUM

    def test_explanation_contains_area(self):
        ua = make_unit("A", "01", unit_type="apartment")
        ub = make_unit("B", "01", unit_type="apartment")
        _, _, _, expl = classify_overlap(ua, ub, 3.40)
        assert "3.40" in expl

    def test_parking_commercial(self):
        park = make_unit("P", "01", unit_type="parking")
        comm = make_unit("C", "01", unit_type="commercial")
        ct, sev, _, _ = classify_overlap(park, comm, 5.0)
        assert ct == ConflictType.PARKING_APARTMENT_OVERLAP
        assert sev == Severity.HIGH


# ===================================================================
# classify_single_unit_issue
# ===================================================================


class TestClassifySingleUnitIssue:
    @pytest.mark.parametrize(
        "issue_kind,expected_type,expected_severity",
        [
            ("invalid_geometry", ConflictType.INVALID_GEOMETRY, Severity.HIGH),
            ("open_ring", ConflictType.INVALID_GEOMETRY, Severity.HIGH),
            ("invalid_z_range", ConflictType.INVALID_Z_RANGE, Severity.HIGH),
            ("negative_area", ConflictType.INVALID_GEOMETRY, Severity.HIGH),
            (
                "unit_outside_building",
                ConflictType.UNIT_OUTSIDE_BUILDING,
                Severity.MEDIUM,
            ),
            (
                "level_assignment_error",
                ConflictType.LEVEL_ASSIGNMENT_ERROR,
                Severity.MEDIUM,
            ),
            (
                "floating_unit",
                ConflictType.FLOATING_UNIT_WARNING,
                Severity.LOW,
            ),
            (
                "exceeds_building_height",
                ConflictType.INVALID_Z_RANGE,
                Severity.MEDIUM,
            ),
        ],
    )
    def test_known_issue_kinds(self, issue_kind, expected_type, expected_severity):
        unit = make_unit("TEST", "01")
        ct, sev, action, expl = classify_single_unit_issue(
            issue_kind, unit, "extra detail"
        )
        assert ct == expected_type
        assert sev == expected_severity
        assert len(action) > 0
        assert "TEST" in expl

    def test_unknown_issue_kind(self):
        unit = make_unit("TEST", "01")
        ct, sev, _, expl = classify_single_unit_issue(
            "totally_made_up", unit
        )
        assert ct == ConflictType.INVALID_GEOMETRY  # fallback
        assert sev == Severity.MEDIUM
        assert "totally_made_up" in expl
