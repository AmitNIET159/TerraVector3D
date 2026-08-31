"""Tests for Pydantic models in src.models."""

from __future__ import annotations

import pytest

from src.models import (
    Building,
    ConflictScenario,
    Level,
    ParcelFeature,
    ParcelGeoJSON,
    ParcelProperties,
    PolygonGeometry,
    RightsRecord,
    SourceMetadata,
    SpatialUnit,
)


# ── PolygonGeometry ──────────────────────────────────────────────────────

class TestPolygonGeometry:
    def test_valid_closed_ring(self):
        pg = PolygonGeometry(
            coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
        )
        assert pg.type == "Polygon"
        assert len(pg.coordinates[0]) == 5

    def test_unclosed_ring_raises(self):
        with pytest.raises(ValueError, match="not closed"):
            PolygonGeometry(
                coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10]]]
            )

    def test_too_few_points_raises(self):
        with pytest.raises(ValueError, match=">= 4"):
            PolygonGeometry(coordinates=[[[0, 0], [1, 1], [0, 0]]])


# ── ParcelProperties ────────────────────────────────────────────────────

class TestParcelProperties:
    def test_valid_ulpin(self):
        p = ParcelProperties(
            parent_ulpin="7A4B9C2D8E1F6G",
            parcel_id="PRC-001",
            address="Test",
            total_area_sqm=100.0,
        )
        assert p.parent_ulpin == "7A4B9C2D8E1F6G"

    def test_invalid_ulpin_length(self):
        with pytest.raises(ValueError, match="14 uppercase"):
            ParcelProperties(
                parent_ulpin="SHORT",
                parcel_id="PRC-001",
                address="Test",
                total_area_sqm=100.0,
            )

    def test_invalid_ulpin_lowercase(self):
        with pytest.raises(ValueError, match="14 uppercase"):
            ParcelProperties(
                parent_ulpin="7a4b9c2d8e1f6g",
                parcel_id="PRC-001",
                address="Test",
                total_area_sqm=100.0,
            )

    def test_zero_area_raises(self):
        with pytest.raises(ValueError):
            ParcelProperties(
                parent_ulpin="7A4B9C2D8E1F6G",
                parcel_id="PRC-001",
                address="Test",
                total_area_sqm=0.0,
            )


# ── Level ────────────────────────────────────────────────────────────────

class TestLevel:
    def test_valid_level(self):
        lvl = Level(
            level_code="01",
            building_id="BLD-001",
            level_type="residential",
            z_min_m=4.0,
            z_max_m=7.0,
            elevation_label="Floor 1",
        )
        assert lvl.z_max_m > lvl.z_min_m

    def test_z_max_below_z_min_raises(self):
        with pytest.raises(ValueError, match="greater than"):
            Level(
                level_code="X",
                building_id="B",
                level_type="test",
                z_min_m=10.0,
                z_max_m=5.0,
                elevation_label="Bad",
            )


# ── SpatialUnit ─────────────────────────────────────────────────────────

class TestSpatialUnit:
    def test_valid_vertical_id(self):
        su = SpatialUnit(
            unit_id="UNIT-F01-101",
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            parent_ulpin="7A4B9C2D8E1F6G",
            building_id="BLD-001",
            level_code="01",
            unit_type="apartment",
            footprint=PolygonGeometry(
                coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
            ),
            z_min_m=4.0,
            z_max_m=7.0,
            area_sqm=100.0,
            usage_type="residential",
            status="registered",
            model_object_name="F01_apartment_101",
        )
        assert su.vertical_id.startswith("7A4B9C2D8E1F6G")

    def test_invalid_vertical_id_raises(self):
        with pytest.raises(ValueError, match="Invalid vertical_id"):
            SpatialUnit(
                unit_id="U1",
                vertical_id="BAD-FORMAT",
                parent_ulpin="7A4B9C2D8E1F6G",
                building_id="B",
                level_code="01",
                unit_type="apartment",
                footprint=PolygonGeometry(
                    coordinates=[
                        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
                    ]
                ),
                z_min_m=0,
                z_max_m=3,
                area_sqm=1,
                usage_type="x",
                status="registered",
                model_object_name="x",
            )


# ── Building ─────────────────────────────────────────────────────────────

class TestBuilding:
    def test_confidence_bounds(self):
        with pytest.raises(ValueError):
            Building(
                building_id="B",
                parcel_id="P",
                parent_ulpin="7A4B9C2D8E1F6G",
                building_name="X",
                footprint=PolygonGeometry(
                    coordinates=[
                        [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
                    ]
                ),
                total_height_m=10,
                num_levels=1,
                source_confidence_score=1.5,  # out of bounds
                source_type="test",
            )
