"""Tests for bhudrishti_topology.src.models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from bhudrishti_topology.src.models import (
    BuildingInput,
    ConflictResult,
    ConflictType,
    LevelInfo,
    Severity,
    SpatialUnit,
    ValidationSummary,
)


# ===================================================================
# LevelInfo
# ===================================================================


class TestLevelInfo:
    def test_valid_level(self):
        lv = LevelInfo(level_code="01", z_min_m=0.0, z_max_m=3.0)
        assert lv.z_max_m > lv.z_min_m

    def test_invalid_z_range_raises(self):
        with pytest.raises(ValidationError, match="z_min_m"):
            LevelInfo(level_code="01", z_min_m=5.0, z_max_m=3.0)

    def test_equal_z_raises(self):
        with pytest.raises(ValidationError, match="z_min_m"):
            LevelInfo(level_code="01", z_min_m=3.0, z_max_m=3.0)


# ===================================================================
# SpatialUnit — ULPIN validation
# ===================================================================


class TestSpatialUnitUlpin:
    def test_valid_14_char_ulpin(self):
        unit = SpatialUnit(
            unit_id="U1",
            vertical_id="7A4B9C2D8E1F6G-F01-UU1-R01",
            parent_ulpin="7A4B9C2D8E1F6G",
            building_id="B1",
            level_code="01",
            unit_type="apartment",
            footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
            z_min_m=0.0,
            z_max_m=3.0,
            area_sqm=1.0,
            usage_type="residential",
            status="active",
        )
        assert unit.parent_ulpin == "7A4B9C2D8E1F6G"

    def test_ulpin_too_short_raises(self):
        with pytest.raises(ValidationError, match="14 uppercase"):
            SpatialUnit(
                unit_id="U1",
                vertical_id="7A4B9C2D8E1F6-F01-UU1-R01",
                parent_ulpin="7A4B9C2D8E1F6",  # 13 chars
                building_id="B1",
                level_code="01",
                unit_type="apartment",
                footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                z_min_m=0.0,
                z_max_m=3.0,
                area_sqm=1.0,
                usage_type="residential",
                status="active",
            )

    def test_ulpin_lowercase_raises(self):
        with pytest.raises(ValidationError, match="14 uppercase"):
            SpatialUnit(
                unit_id="U1",
                vertical_id="7a4b9c2d8e1f6g-F01-UU1-R01",
                parent_ulpin="7a4b9c2d8e1f6g",  # lowercase
                building_id="B1",
                level_code="01",
                unit_type="apartment",
                footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                z_min_m=0.0,
                z_max_m=3.0,
                area_sqm=1.0,
                usage_type="residential",
                status="active",
            )


# ===================================================================
# SpatialUnit — Vertical ID validation
# ===================================================================


class TestSpatialUnitVerticalId:
    def test_valid_apartment_vertical_id(self):
        unit = SpatialUnit(
            unit_id="U401",
            vertical_id="7A4B9C2D8E1F6G-F04-U401-R01",
            parent_ulpin="7A4B9C2D8E1F6G",
            building_id="B1",
            level_code="04",
            unit_type="apartment",
            footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
            z_min_m=9.0,
            z_max_m=12.0,
            area_sqm=1.0,
            usage_type="residential",
            status="active",
        )
        assert unit.vertical_id == "7A4B9C2D8E1F6G-F04-U401-R01"

    def test_valid_parking_vertical_id(self):
        unit = SpatialUnit(
            unit_id="P24",
            vertical_id="7A4B9C2D8E1F6G-FB1-UP24-R01",
            parent_ulpin="7A4B9C2D8E1F6G",
            building_id="B1",
            level_code="B1",
            unit_type="parking",
            footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
            z_min_m=-3.0,
            z_max_m=0.0,
            area_sqm=1.0,
            usage_type="parking",
            status="active",
        )
        assert "FB1" in unit.vertical_id

    def test_valid_utility_vertical_id(self):
        unit = SpatialUnit(
            unit_id="UTIL01",
            vertical_id="7A4B9C2D8E1F6G-FB1-UUTIL01-R01",
            parent_ulpin="7A4B9C2D8E1F6G",
            building_id="B1",
            level_code="B1",
            unit_type="utility",
            footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
            z_min_m=-3.0,
            z_max_m=0.0,
            area_sqm=1.0,
            usage_type="utility",
            status="active",
        )
        assert "UUTIL01" in unit.vertical_id

    def test_invalid_vertical_id_format_raises(self):
        with pytest.raises(ValidationError, match="vertical_id"):
            SpatialUnit(
                unit_id="U1",
                vertical_id="INVALID-FORMAT",
                parent_ulpin="7A4B9C2D8E1F6G",
                building_id="B1",
                level_code="01",
                unit_type="apartment",
                footprint=[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]],
                z_min_m=0.0,
                z_max_m=3.0,
                area_sqm=1.0,
                usage_type="residential",
                status="active",
            )


# ===================================================================
# ConflictResult
# ===================================================================


class TestConflictResult:
    def test_auto_generated_conflict_id(self):
        cr = ConflictResult(
            conflict_type=ConflictType.VOLUME_OVERLAP,
            severity=Severity.HIGH,
            affected_unit_ids=["U1", "U2"],
            affected_vertical_ids=["VID1", "VID2"],
            recommended_action="Fix it.",
            human_readable_explanation="Two units overlap.",
        )
        assert cr.conflict_id.startswith("CONFLICT-")
        assert len(cr.conflict_id) == len("CONFLICT-") + 8

    def test_default_numeric_fields(self):
        cr = ConflictResult(
            conflict_type=ConflictType.INVALID_GEOMETRY,
            severity=Severity.HIGH,
            affected_unit_ids=["U1"],
            affected_vertical_ids=["VID1"],
            recommended_action="Fix geometry.",
            human_readable_explanation="Bad polygon.",
        )
        assert cr.horizontal_overlap_area_sqm == 0.0
        assert cr.estimated_overlap_volume_cum == 0.0


# ===================================================================
# ValidationSummary
# ===================================================================


class TestValidationSummary:
    def test_valid_summary(self):
        vs = ValidationSummary(
            building_id="B1",
            parent_ulpin="7A4B9C2D8E1F6G",
            total_units=5,
            total_conflicts=0,
            conflicts_by_severity={},
            conflicts_by_type={},
            conflicts=[],
            is_valid=True,
        )
        assert vs.is_valid is True
        assert vs.total_conflicts == 0


# ===================================================================
# BuildingInput — from example JSON
# ===================================================================


class TestBuildingInputFromJson:
    def test_load_valid_building(self, valid_building_json):
        bld = BuildingInput(**valid_building_json)
        assert bld.building_id == "BLD-001"
        assert len(bld.spatial_units) == 7
        assert len(bld.levels) == 4

    def test_load_conflict_building(self, conflict_building_json):
        bld = BuildingInput(**conflict_building_json)
        assert bld.building_id == "BLD-002"
        assert len(bld.spatial_units) == 9
