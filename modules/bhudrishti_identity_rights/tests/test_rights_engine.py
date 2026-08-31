"""
Comprehensive tests for the rights engine.

Covers: holder_name_masked validation, parking/utility compatibility,
unit-against-parent checks, date logic, duplicate detection, property
identity summary, and cross-module field compatibility.

The canonical holder field is ``holder_name_masked`` — ``holder_masked``
is NOT used anywhere in this module.
"""

import pytest

from src.rights_engine import (
    build_property_identity_summary,
    validate_rights_record,
    validate_unit_against_parent,
)
from src.models import ValidationStatus

ULPIN = "7A4B9C2D8E1F6G"
FLOOR_ID = f"{ULPIN}-F04-U401-R01"
PARK_ID = f"{ULPIN}-FB1-UPARK24-R01"
UTIL_ID = f"{ULPIN}-FB1-UUTIL01-R01"
GROUND_ID = f"{ULPIN}-FG-USHOP01-R02"


# ======================================================================
# validate_unit_against_parent
# ======================================================================

class TestValidateUnitAgainstParent:
    """Tests for validate_unit_against_parent()."""

    def test_matching_ulpin(self):
        result = validate_unit_against_parent(FLOOR_ID, ULPIN)
        assert result.is_valid is True

    def test_mismatched_ulpin(self):
        result = validate_unit_against_parent(FLOOR_ID, "1X2Y3Z4W5V6U7T")
        assert result.is_valid is False
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_invalid_id_string(self):
        result = validate_unit_against_parent("BAD-ID", ULPIN)
        assert result.is_valid is False


# ======================================================================
# validate_rights_record — holder_name_masked
# ======================================================================

class TestHolderNameMasked:
    """
    The canonical holder field is ``holder_name_masked``.

    ``holder_masked`` must NOT be accepted as a field name.
    """

    def test_holder_name_masked_accepted(self):
        """holder_name_masked is the expected field and must be accepted."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.valid

    def test_holder_masked_not_accepted(self):
        """Using 'holder_masked' instead of 'holder_name_masked' → invalid."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_masked": "R***A",  # WRONG field name
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("holder_name_masked" in e for e in result.errors)

    def test_unmasked_holder_rejected(self):
        """Holder name without '*' → invalid."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "Rajesh Kumar",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("masked" in e.lower() for e in result.errors)

    def test_empty_holder_rejected(self):
        """Empty holder string → invalid."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid

    def test_holder_all_stars(self):
        """A fully masked holder (all stars) is still valid."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "****",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.valid


# ======================================================================
# validate_rights_record — parking / utility compatibility
# ======================================================================

class TestParkingUtilityCompatibility:
    """
    parking_right valid only when unit_code contains PARK.
    utility_easement valid only when unit_code contains UTIL.
    """

    def test_parking_right_on_parking_unit_valid(self):
        """UPARK24 + parking_right → valid."""
        record = {
            "vertical_id": PARK_ID,
            "right_type": "parking_right",
            "holder_name_masked": "S***H",
            "start_date": "2025-03-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.valid
        assert any("PASS" in a and "parking" in a.lower()
                    for a in result.audit_explanation)

    def test_parking_right_on_normal_apartment_invalid(self):
        """U401 + parking_right → invalid."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "parking_right",
            "holder_name_masked": "A***N",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("PARK" in e for e in result.errors)

    def test_utility_easement_on_utility_unit_valid(self):
        """UUTIL01 + utility_easement → valid."""
        record = {
            "vertical_id": UTIL_ID,
            "right_type": "utility_easement",
            "holder_name_masked": "M***L",
            "start_date": "2025-06-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.valid
        assert any("PASS" in a and "utility" in a.lower()
                    for a in result.audit_explanation)

    def test_utility_easement_on_normal_apartment_invalid(self):
        """U401 + utility_easement → invalid."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "utility_easement",
            "holder_name_masked": "M***L",
            "start_date": "2025-06-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("UTIL" in e for e in result.errors)

    def test_parking_right_on_shop_unit_invalid(self):
        """USHOP01 + parking_right → invalid (no PARK)."""
        record = {
            "vertical_id": GROUND_ID,
            "right_type": "parking_right",
            "holder_name_masked": "K***A",
            "start_date": "2025-04-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid

    def test_utility_easement_on_parking_unit_invalid(self):
        """UPARK24 + utility_easement → invalid (no UTIL)."""
        record = {
            "vertical_id": PARK_ID,
            "right_type": "utility_easement",
            "holder_name_masked": "K***A",
            "start_date": "2025-04-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid

    def test_ownership_on_any_unit_valid(self):
        """ownership works on any unit type."""
        for vid in [FLOOR_ID, PARK_ID, UTIL_ID, GROUND_ID]:
            record = {
                "vertical_id": vid,
                "right_type": "ownership",
                "holder_name_masked": "R***A",
                "start_date": "2025-01-15",
            }
            result = validate_rights_record(record)
            assert result.status == ValidationStatus.valid, (
                f"ownership should be valid on {vid}"
            )

    def test_lease_on_any_unit_valid(self):
        """lease works on any unit type."""
        for vid in [FLOOR_ID, PARK_ID, UTIL_ID, GROUND_ID]:
            record = {
                "vertical_id": vid,
                "right_type": "lease",
                "holder_name_masked": "T***I",
                "start_date": "2025-02-01",
                "end_date": "2030-02-01",
            }
            result = validate_rights_record(record)
            assert result.status == ValidationStatus.valid, (
                f"lease should be valid on {vid}"
            )


# ======================================================================
# validate_rights_record — date logic
# ======================================================================

class TestDateValidation:
    """Date ordering and format checks."""

    def test_valid_dates(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "lease",
            "holder_name_masked": "T***I",
            "start_date": "2025-01-01",
            "end_date": "2030-12-31",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.valid

    def test_end_before_start_invalid(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "lease",
            "holder_name_masked": "T***I",
            "start_date": "2025-06-01",
            "end_date": "2024-01-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("after" in e.lower() or "end_date" in e
                    for e in result.errors)

    def test_end_equals_start_invalid(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "lease",
            "holder_name_masked": "T***I",
            "start_date": "2025-06-01",
            "end_date": "2025-06-01",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid

    def test_invalid_date_format(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "01-15-2025",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("ISO" in e or "format" in e.lower() for e in result.errors)

    def test_no_end_date_valid(self):
        """Ownership without end_date is fine."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.valid


# ======================================================================
# validate_rights_record — missing / invalid fields
# ======================================================================

class TestMissingFields:
    """Missing or invalid required fields."""

    def test_missing_vertical_id(self):
        record = {
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("vertical_id" in e for e in result.errors)

    def test_missing_right_type(self):
        record = {
            "vertical_id": FLOOR_ID,
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("right_type" in e for e in result.errors)

    def test_missing_start_date(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("start_date" in e for e in result.errors)

    def test_invalid_right_type(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "freehold",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid
        assert any("right_type" in e.lower() for e in result.errors)

    def test_invalid_vertical_id_in_record(self):
        record = {
            "vertical_id": "INVALID-ID",
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert result.status == ValidationStatus.invalid

    def test_audit_trail_present(self):
        """Every decision must have an audit explanation."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        result = validate_rights_record(record)
        assert len(result.audit_explanation) > 0
        assert all(
            a.startswith("PASS") or a.startswith("FAIL")
            or a.startswith("WARNING")
            for a in result.audit_explanation
        )


# ======================================================================
# Duplicate rights → needs_review
# ======================================================================

class TestDuplicateRights:
    """Duplicate right_type entries trigger needs_review."""

    def test_duplicate_ownership_needs_review(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        summary = build_property_identity_summary(
            FLOOR_ID, [record, record],
        )
        assert summary.overall_status == ValidationStatus.needs_review
        # The second record should have a duplicate warning
        assert any(
            "duplicate" in w.lower()
            for w in summary.rights_validation_results[1].warnings
        )


# ======================================================================
# build_property_identity_summary
# ======================================================================

class TestBuildPropertyIdentitySummary:
    """Tests for build_property_identity_summary()."""

    def test_single_valid_record(self):
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
            "notes": "Fictional ownership",
        }
        summary = build_property_identity_summary(FLOOR_ID, [record])
        assert summary.vertical_id == FLOOR_ID
        assert summary.parent_ulpin == ULPIN
        assert summary.level_display == "Floor 4"
        assert summary.unit_code == "401"
        assert summary.revision == 1
        assert "Floor 4" in summary.human_readable_label
        assert summary.overall_status == ValidationStatus.valid
        assert len(summary.rights_records) == 1
        assert summary.rights_records[0].holder_name_masked == "R***A"

    def test_mixed_valid_and_invalid(self):
        valid = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
        }
        invalid = {
            "vertical_id": FLOOR_ID,
            "right_type": "parking_right",
            "holder_name_masked": "A***N",
            "start_date": "2025-01-15",
        }
        summary = build_property_identity_summary(
            FLOOR_ID, [valid, invalid],
        )
        assert summary.overall_status == ValidationStatus.invalid

    def test_empty_records(self):
        summary = build_property_identity_summary(FLOOR_ID, [])
        assert summary.overall_status == ValidationStatus.valid
        assert summary.rights_records == []

    def test_summary_uses_holder_name_masked_field(self):
        """Verify the summary model uses holder_name_masked, not holder_masked."""
        record = {
            "vertical_id": FLOOR_ID,
            "right_type": "ownership",
            "holder_name_masked": "J***N",
            "start_date": "2025-03-01",
        }
        summary = build_property_identity_summary(FLOOR_ID, [record])
        dumped = summary.model_dump()
        # Check nested rights record uses the canonical field name
        assert "holder_name_masked" in dumped["rights_records"][0]
        assert "holder_masked" not in dumped["rights_records"][0]


# ======================================================================
# Cross-module compatibility
# ======================================================================

class TestCrossModuleCompatibility:
    """
    Ensure JSON output structure matches BhuDrishti evidence-report
    canonical fields: vertical_id, right_type, holder_name_masked,
    start_date, end_date, notes.
    """

    def test_rights_record_json_keys(self):
        """RightsRecord serialises with the correct canonical keys."""
        from src.models import RightsRecord, RightType
        from datetime import date

        rr = RightsRecord(
            vertical_id=FLOOR_ID,
            right_type=RightType.ownership,
            holder_name_masked="R***A",
            start_date=date(2025, 1, 15),
            end_date=date(2030, 12, 31),
            notes="Test note",
        )
        data = rr.model_dump()
        expected_keys = {
            "vertical_id",
            "right_type",
            "holder_name_masked",
            "start_date",
            "end_date",
            "notes",
        }
        assert set(data.keys()) == expected_keys
        assert "holder_masked" not in data
