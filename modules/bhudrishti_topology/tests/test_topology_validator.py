"""Tests for bhudrishti_topology.src.topology_validator."""

from __future__ import annotations

import json

import pytest

from bhudrishti_topology.src.models import (
    BuildingInput,
    ConflictType,
    LevelInfo,
    Severity,
    SpatialUnit,
    ValidationSummary,
)
from bhudrishti_topology.src.topology_validator import (
    detect_volume_conflicts,
    generate_validation_summary,
    validate_building,
    validate_spatial_units,
)
from tests.conftest import make_building, make_unit


# ===================================================================
# validate_spatial_units — single‑unit checks
# ===================================================================


class TestValidateSpatialUnits:
    def test_valid_units_no_conflicts(self):
        bld = make_building(
            units=[
                make_unit("U101", "01"),
                make_unit(
                    "U102",
                    "01",
                    footprint=[
                        [10, 0], [20, 0], [20, 10], [10, 10], [10, 0]
                    ],
                ),
            ]
        )
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        assert len(conflicts) == 0

    def test_open_ring(self):
        unit = make_unit(
            "BAD",
            "01",
            footprint=[[0, 0], [10, 0], [10, 10], [0, 10]],  # not closed
        )
        bld = make_building(units=[unit])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.INVALID_GEOMETRY in types

    def test_invalid_z_range(self):
        unit = make_unit("BAD", "01", z_min=5.0, z_max=2.0)
        bld = make_building(units=[unit])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.INVALID_Z_RANGE in types

    def test_negative_area(self):
        unit = make_unit("BAD", "01", area=-50.0)
        bld = make_building(units=[unit])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.INVALID_GEOMETRY in types

    def test_unit_outside_building(self):
        unit = make_unit(
            "OUTSIDE",
            "01",
            footprint=[
                [50, 50], [60, 50], [60, 60], [50, 60], [50, 50]
            ],
        )
        bld = make_building(units=[unit])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.UNIT_OUTSIDE_BUILDING in types

    def test_level_assignment_error(self):
        unit = make_unit("BAD", "99")  # level "99" doesn't exist
        bld = make_building(units=[unit])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.LEVEL_ASSIGNMENT_ERROR in types

    def test_floating_unit_warning(self):
        # Level 01 is z 0–3; unit starts at 1.5 → floats by 1.5 m
        unit = make_unit("FLOAT", "01", z_min=1.5, z_max=3.0)
        bld = make_building(units=[unit])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.FLOATING_UNIT_WARNING in types

    def test_exceeds_building_height(self):
        unit = make_unit("HIGH", "04", z_min=9.0, z_max=15.0)
        bld = make_building(units=[unit], total_height=12.0)
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.INVALID_Z_RANGE in types

    def test_duplicate_vertical_id(self):
        vid = "7A4B9C2D8E1F6G-F01-UDUPE-R01"
        u1 = make_unit("DUPE1", "01", vertical_id=vid)
        u2 = make_unit("DUPE2", "01", vertical_id=vid,
                        footprint=[
                            [10, 0], [20, 0], [20, 10], [10, 10], [10, 0]
                        ])
        bld = make_building(units=[u1, u2])
        conflicts = validate_spatial_units(bld.spatial_units, bld)
        types = [c.conflict_type for c in conflicts]
        assert ConflictType.DUPLICATE_VERTICAL_ID in types


# ===================================================================
# detect_volume_conflicts — pairwise checks
# ===================================================================


class TestDetectVolumeConflicts:
    def test_no_overlap(self):
        u1 = make_unit(
            "U101",
            "01",
            footprint=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        u2 = make_unit(
            "U102",
            "01",
            footprint=[
                [10, 0], [20, 0], [20, 10], [10, 10], [10, 0]
            ],
            z_min=0.0,
            z_max=3.0,
        )
        assert len(detect_volume_conflicts([u1, u2])) == 0

    def test_apartment_apartment_overlap(self):
        u1 = make_unit(
            "U401",
            "04",
            footprint=[
                [0, 0], [10.34, 0], [10.34, 10], [0, 10], [0, 0]
            ],
            z_min=9.0,
            z_max=12.0,
        )
        u2 = make_unit(
            "U402",
            "04",
            footprint=[
                [10.0, 0], [20, 0], [20, 10], [10.0, 10], [10.0, 0]
            ],
            z_min=9.0,
            z_max=12.0,
        )
        conflicts = detect_volume_conflicts([u1, u2])
        assert len(conflicts) == 1
        c = conflicts[0]
        assert c.conflict_type == ConflictType.VOLUME_OVERLAP
        assert c.severity == Severity.HIGH
        assert abs(c.horizontal_overlap_area_sqm - 3.4) < 0.01
        assert c.overlapping_z_min_m == 9.0
        assert c.overlapping_z_max_m == 12.0
        assert abs(c.estimated_overlap_volume_cum - 10.2) < 0.1

    def test_utility_easement_review(self):
        util = make_unit(
            "UTIL01",
            "01",
            unit_type="utility",
            usage="utility",
            footprint=[[0, 0], [10, 0], [10, 5], [0, 5], [0, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        ease = make_unit(
            "EASE01",
            "01",
            unit_type="easement",
            usage="easement",
            footprint=[[5, 0], [15, 0], [15, 5], [5, 5], [5, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        conflicts = detect_volume_conflicts([util, ease])
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.UTILITY_EASEMENT_REVIEW
        assert conflicts[0].severity == Severity.LOW

    def test_parking_apartment_overlap(self):
        park = make_unit(
            "P01",
            "01",
            unit_type="parking",
            usage="parking",
            footprint=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        apt = make_unit(
            "U101",
            "01",
            unit_type="apartment",
            footprint=[[5, 0], [15, 0], [15, 10], [5, 10], [5, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        conflicts = detect_volume_conflicts([park, apt])
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.PARKING_APARTMENT_OVERLAP
        assert conflicts[0].severity == Severity.HIGH

    def test_horizontal_only_no_vertical(self):
        u1 = make_unit(
            "A",
            "01",
            footprint=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]],
            z_min=0.0,
            z_max=3.0,
        )
        u2 = make_unit(
            "B",
            "02",
            footprint=[[5, 0], [15, 0], [15, 10], [5, 10], [5, 0]],
            z_min=3.0,
            z_max=6.0,
        )
        assert len(detect_volume_conflicts([u1, u2])) == 0


# ===================================================================
# generate_validation_summary
# ===================================================================


class TestGenerateValidationSummary:
    def test_empty_conflicts(self):
        bld = make_building(
            units=[make_unit("U101", "01")]
        )
        summary = generate_validation_summary(bld, [])
        assert summary.is_valid is True
        assert summary.total_conflicts == 0

    def test_with_high_severity(self):
        from bhudrishti_topology.src.models import ConflictResult

        conflict = ConflictResult(
            conflict_type=ConflictType.VOLUME_OVERLAP,
            severity=Severity.HIGH,
            affected_unit_ids=["U1", "U2"],
            affected_vertical_ids=["V1", "V2"],
            recommended_action="Fix",
            human_readable_explanation="Overlap",
        )
        bld = make_building(units=[make_unit("U1", "01")])
        summary = generate_validation_summary(bld, [conflict])
        assert summary.is_valid is False
        assert summary.total_conflicts == 1
        assert summary.conflicts_by_severity.get("high") == 1


# ===================================================================
# validate_building — end‑to‑end
# ===================================================================


class TestValidateBuilding:
    def test_valid_building_from_json(self, valid_building_json):
        bld = BuildingInput(**valid_building_json)
        summary = validate_building(bld)
        assert summary.is_valid is True
        assert summary.total_conflicts == 0

    def test_conflict_building_from_json(self, conflict_building_json):
        bld = BuildingInput(**conflict_building_json)
        summary = validate_building(bld)
        assert summary.is_valid is False
        assert summary.total_conflicts >= 1

        # Must find the deliberate U401/U402 VOLUME_OVERLAP
        vol_overlaps = [
            c
            for c in summary.conflicts
            if c.conflict_type == ConflictType.VOLUME_OVERLAP
        ]
        assert len(vol_overlaps) >= 1

        overlap = vol_overlaps[0]
        assert overlap.severity == Severity.HIGH
        assert set(overlap.affected_unit_ids) == {"U401", "U402"}
        assert abs(overlap.horizontal_overlap_area_sqm - 3.4) < 0.05
        assert abs(overlap.estimated_overlap_volume_cum - 10.2) < 0.5

    def test_conflict_building_has_utility_review(
        self, conflict_building_json
    ):
        bld = BuildingInput(**conflict_building_json)
        summary = validate_building(bld)
        reviews = [
            c
            for c in summary.conflicts
            if c.conflict_type == ConflictType.UTILITY_EASEMENT_REVIEW
        ]
        assert len(reviews) >= 1

    def test_summary_serializes_to_json(self, valid_building_json):
        bld = BuildingInput(**valid_building_json)
        summary = validate_building(bld)
        j = json.loads(summary.model_dump_json())
        assert "building_id" in j
        assert "conflicts" in j
        assert "is_valid" in j
