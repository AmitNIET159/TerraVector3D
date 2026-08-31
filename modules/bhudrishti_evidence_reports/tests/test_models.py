"""Tests for src.models — Pydantic validation, aliases, cross-record checks."""

from __future__ import annotations

import copy

import pytest

from src.models import (
    BuildingData,
    Level,
    ParcelData,
    PropertyRight,
    SourceMetadata,
    SpatialUnit,
    TopologyConflict,
    ValidationInput,
    mask_holder_name,
)


# ===================================================================
# ULPIN validation
# ===================================================================

class TestULPINValidation:
    """Parent ULPIN must be exactly 14 uppercase-alphanumeric characters."""

    def test_valid_ulpin(self, sample_raw_data: dict) -> None:
        vi = ValidationInput(**sample_raw_data)
        assert vi.parent_ulpin == "7A4B9C2D8E1F6G"

    def test_short_ulpin_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["parent_ulpin"] = "ABCD1234"
        with pytest.raises(Exception):
            ValidationInput(**data)

    def test_lowercase_ulpin_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["parent_ulpin"] = "7a4b9c2d8e1f6g"
        with pytest.raises(Exception):
            ValidationInput(**data)


# ===================================================================
# Vertical ID validation
# ===================================================================

class TestVerticalIDValidation:
    """Vertical ID format: <ULPIN>-F<level>-U<unit>-R<revision>."""

    @pytest.mark.parametrize(
        "vid",
        [
            "7A4B9C2D8E1F6G-F04-U401-R01",
            "7A4B9C2D8E1F6G-FB1-UP24-R01",
            "7A4B9C2D8E1F6G-FB1-UUTIL01-R01",
        ],
    )
    def test_valid_vertical_ids(self, vid: str) -> None:
        unit = SpatialUnit(
            vertical_id=vid,
            level_id="LVL-01",
            unit_type="residential",
            area_sqm=100.0,
            usage_type="dwelling",
            boundary_coordinates=[[0, 0], [10, 0], [10, 10], [0, 10]],
            validation_status="valid",
        )
        assert unit.vertical_id == vid

    def test_invalid_vertical_id_rejected(self) -> None:
        with pytest.raises(Exception):
            SpatialUnit(
                vertical_id="BAD-FORMAT",
                level_id="LVL-01",
                unit_type="residential",
                area_sqm=100.0,
                usage_type="dwelling",
                boundary_coordinates=[[0, 0], [10, 0]],
                validation_status="valid",
            )


# ===================================================================
# Severity validation
# ===================================================================

class TestSeverityValidation:
    """Severity must be high, medium, or low."""

    def test_valid_severities(self) -> None:
        for sev in ("high", "medium", "low"):
            conflict = TopologyConflict(
                conflict_id="C1",
                severity=sev,
                conflicting_unit_ids=["U1"],
                conflicting_vertical_ids=["7A4B9C2D8E1F6G-F01-U101-R01"],
                overlap_area_sqm=1.0,
                recommended_action="Review",
                explanation="Test",
            )
            assert conflict.severity == sev

    def test_invalid_severity_rejected(self) -> None:
        with pytest.raises(Exception):
            TopologyConflict(
                conflict_id="C1",
                severity="critical",
                conflicting_unit_ids=["U1"],
                conflicting_vertical_ids=["7A4B9C2D8E1F6G-F01-U101-R01"],
                overlap_area_sqm=1.0,
                recommended_action="Review",
                explanation="Test",
            )


# ===================================================================
# Confidence scores
# ===================================================================

class TestConfidenceScores:
    """Confidence scores must include 'overall' and be 0.0–1.0."""

    def test_missing_overall_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["confidence_scores"] = {"geometric": 0.9}
        with pytest.raises(Exception):
            ValidationInput(**data)

    def test_out_of_range_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["confidence_scores"]["overall"] = 1.5
        with pytest.raises(Exception):
            ValidationInput(**data)


# ===================================================================
# Canonical alias support  (Priority 3)
# ===================================================================

class TestCanonicalAliases:
    """Canonical field names are accepted via Pydantic AliasChoices."""

    def test_level_code_alias(self) -> None:
        """level_code is accepted in place of level_id."""
        level = Level.model_validate({
            "level_code": "LVL-00",
            "level_number": 0,
            "height_m": 4.0,
            "floor_area_sqm": 680.0,
            "level_type": "ground",
        })
        assert level.level_id == "LVL-00"

    def test_status_alias(self) -> None:
        """status is accepted in place of validation_status."""
        unit = SpatialUnit.model_validate({
            "vertical_id": "7A4B9C2D8E1F6G-F01-U101-R01",
            "level_code": "LVL-01",
            "unit_type": "residential",
            "area_sqm": 95.0,
            "usage_type": "dwelling",
            "footprint": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "status": "valid",
        })
        assert unit.validation_status == "valid"

    def test_footprint_alias_building(self) -> None:
        """footprint is accepted in place of footprint_coordinates."""
        bd = BuildingData.model_validate({
            "building_id": "BLD-001",
            "building_name": "Test",
            "footprint": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "height_m": 15.0,
            "num_floors": 4,
        })
        assert len(bd.footprint_coordinates) == 4

    def test_footprint_alias_spatial_unit(self) -> None:
        """footprint is accepted in place of boundary_coordinates."""
        unit = SpatialUnit.model_validate({
            "vertical_id": "7A4B9C2D8E1F6G-F01-U101-R01",
            "level_id": "LVL-01",
            "unit_type": "residential",
            "area_sqm": 95.0,
            "usage_type": "dwelling",
            "footprint": [[0, 0], [10, 0], [10, 10], [0, 10]],
            "validation_status": "valid",
        })
        assert len(unit.boundary_coordinates) == 4

    def test_z_min_z_max_on_spatial_unit(self) -> None:
        """z_min_m and z_max_m are accepted on SpatialUnit."""
        unit = SpatialUnit(
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            level_id="LVL-01",
            unit_type="residential",
            area_sqm=95.0,
            usage_type="dwelling",
            boundary_coordinates=[[0, 0], [10, 0]],
            validation_status="valid",
            z_min_m=4.0,
            z_max_m=7.2,
        )
        assert unit.z_min_m == 4.0
        assert unit.z_max_m == 7.2

    def test_z_min_z_max_on_level(self) -> None:
        """z_min_m and z_max_m are accepted on Level."""
        level = Level(
            level_id="LVL-01",
            level_number=1,
            height_m=3.2,
            floor_area_sqm=650.0,
            level_type="upper",
            z_min_m=4.0,
            z_max_m=7.2,
        )
        assert level.z_min_m == 4.0
        assert level.z_max_m == 7.2

    def test_unit_id_optional(self) -> None:
        """unit_id is an optional field on SpatialUnit."""
        unit = SpatialUnit(
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            unit_id="U101",
            level_id="LVL-01",
            unit_type="residential",
            area_sqm=95.0,
            usage_type="dwelling",
            boundary_coordinates=[[0, 0], [10, 0]],
            validation_status="valid",
        )
        assert unit.unit_id == "U101"


# ===================================================================
# holder_name_masked  (Priority 3)
# ===================================================================

class TestHolderNameMasked:
    """PropertyRight supports holder_name_masked as the primary field."""

    def test_accepts_holder_name_masked_directly(self) -> None:
        right = PropertyRight(
            right_id="R1",
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            rights_type="ownership",
            holder_name_masked="Sn**a Pa**l",
        )
        assert right.holder_name_masked == "Sn**a Pa**l"
        assert right.holder_name is None

    def test_auto_masks_from_holder_name(self) -> None:
        right = PropertyRight(
            right_id="R1",
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            rights_type="ownership",
            holder_name="Sneha Patil",
        )
        assert right.holder_name_masked == "Sn**a Pa**l"

    def test_holder_name_not_required(self) -> None:
        right = PropertyRight(
            right_id="R1",
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            rights_type="ownership",
            holder_name_masked="An***a Bh**t",
        )
        assert right.holder_name is None
        assert right.holder_name_masked == "An***a Bh**t"

    def test_defaults_to_na_when_both_missing(self) -> None:
        right = PropertyRight(
            right_id="R1",
            vertical_id="7A4B9C2D8E1F6G-F01-U101-R01",
            rights_type="ownership",
        )
        assert right.holder_name_masked == "N/A"


# ===================================================================
# Topology conflict canonical fields  (Priority 3)
# ===================================================================

class TestConflictCanonicalFields:
    """TopologyConflict supports canonical fields."""

    def test_conflict_type_optional(self) -> None:
        conflict = TopologyConflict(
            conflict_id="C1",
            severity="high",
            conflict_type="boundary_overlap",
            conflicting_unit_ids=["U1"],
            conflicting_vertical_ids=["7A4B9C2D8E1F6G-F01-U101-R01"],
            overlap_area_sqm=12.8,
            recommended_action="Review",
            explanation="Test",
        )
        assert conflict.conflict_type == "boundary_overlap"

    def test_z_overlap_fields(self) -> None:
        conflict = TopologyConflict(
            conflict_id="C1",
            severity="medium",
            conflicting_unit_ids=["U1"],
            conflicting_vertical_ids=["7A4B9C2D8E1F6G-F01-U101-R01"],
            overlap_area_sqm=4.2,
            overlapping_z_min_m=4.0,
            overlapping_z_max_m=7.2,
            recommended_action="Review",
            explanation="Test",
        )
        assert conflict.overlapping_z_min_m == 4.0
        assert conflict.overlapping_z_max_m == 7.2

    def test_estimated_overlap_volume_cum_syncs(self) -> None:
        conflict = TopologyConflict(
            conflict_id="C1",
            severity="low",
            conflicting_unit_ids=["U1"],
            conflicting_vertical_ids=["7A4B9C2D8E1F6G-F01-U101-R01"],
            overlap_area_sqm=0.6,
            estimated_overlap_volume_cum=1.8,
            recommended_action="Review",
            explanation="Test",
        )
        # estimated_overlap_volume_cum syncs to overlap_volume_cbm
        assert conflict.overlap_volume_cbm == 1.8
        assert conflict.estimated_overlap_volume_cum == 1.8


# ===================================================================
# SHA-256 hex validation  (Priority 3)
# ===================================================================

class TestSHA256HexValidation:
    """sha256_hash must be exactly 64 hex characters."""

    def test_valid_hex_string(self) -> None:
        src = SourceMetadata(
            source_id="S1",
            file_name="test.ifc",
            source_type="BIM_IFC",
            timestamp="2024-01-01T00:00:00+05:30",
            confidence=0.9,
            sha256_hash="a" * 64,
        )
        assert len(src.sha256_hash) == 64

    def test_non_hex_rejected(self) -> None:
        with pytest.raises(Exception):
            SourceMetadata(
                source_id="S1",
                file_name="test.ifc",
                source_type="BIM_IFC",
                timestamp="2024-01-01T00:00:00+05:30",
                confidence=0.9,
                sha256_hash="g" * 64,  # 'g' is not hex
            )

    def test_short_hash_rejected(self) -> None:
        with pytest.raises(Exception):
            SourceMetadata(
                source_id="S1",
                file_name="test.ifc",
                source_type="BIM_IFC",
                timestamp="2024-01-01T00:00:00+05:30",
                confidence=0.9,
                sha256_hash="abcdef",
            )


# ===================================================================
# Cross-record validation  (Priority 3)
# ===================================================================

class TestCrossRecordValidation:
    """ValidationInput cross-validates referential integrity."""

    def test_wrong_ulpin_prefix_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["spatial_units"][0]["vertical_id"] = "XXXXXXXXXXXXXX-FB1-UP24-R01"
        with pytest.raises(Exception, match="does not start with"):
            ValidationInput(**data)

    def test_orphan_property_right_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["property_rights"][0]["vertical_id"] = "7A4B9C2D8E1F6G-F99-U999-R01"
        with pytest.raises(Exception, match="references unknown"):
            ValidationInput(**data)

    def test_orphan_conflict_vertical_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["topology_conflicts"][0]["conflicting_vertical_ids"] = [
            "7A4B9C2D8E1F6G-F99-U999-R01"
        ]
        with pytest.raises(Exception, match="references unknown"):
            ValidationInput(**data)

    def test_building_height_inconsistency_rejected(self, sample_raw_data: dict) -> None:
        data = copy.deepcopy(sample_raw_data)
        data["building"]["height_m"] = 5.0  # Far too short for 6 floors
        with pytest.raises(Exception, match="exceeds.*building height"):
            ValidationInput(**data)

    def test_valid_data_passes(self, sample_raw_data: dict) -> None:
        # Should not raise
        vi = ValidationInput(**sample_raw_data)
        assert vi.parent_ulpin == "7A4B9C2D8E1F6G"


# ===================================================================
# Full model round-trip
# ===================================================================

class TestFullModelRoundTrip:
    """Full model loads and serialises cleanly."""

    def test_model_round_trip(self, sample_input: ValidationInput) -> None:
        dumped = sample_input.model_dump(mode="json")
        reloaded = ValidationInput(**dumped)
        assert reloaded.parent_ulpin == sample_input.parent_ulpin
        assert len(reloaded.spatial_units) == len(sample_input.spatial_units)
        assert len(reloaded.topology_conflicts) == len(sample_input.topology_conflicts)
