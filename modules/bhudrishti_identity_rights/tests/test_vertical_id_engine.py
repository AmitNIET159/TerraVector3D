"""
Comprehensive tests for the vertical-ID engine.

Covers: valid IDs, malformed IDs, basement levels, ground floor,
revision increment, R99 boundary, human-readable labels, parse
round-trips, and detailed validation errors.
"""

import pytest

from src.vertical_id_engine import (
    build_human_readable_label,
    generate_vertical_id,
    increment_revision,
    parse_vertical_id,
    validate_vertical_id,
)
from src.exceptions import ParsingError, VerticalIdValidationError

ULPIN = "7A4B9C2D8E1F6G"


# ======================================================================
# generate_vertical_id
# ======================================================================

class TestGenerateVerticalId:
    """Tests for generate_vertical_id()."""

    def test_basic_floor(self):
        result = generate_vertical_id(ULPIN, "04", "401", 1)
        assert result == f"{ULPIN}-F04-U401-R01"

    def test_basement(self):
        result = generate_vertical_id(ULPIN, "B1", "PARK24", 1)
        assert result == f"{ULPIN}-FB1-UPARK24-R01"

    def test_ground_floor(self):
        result = generate_vertical_id(ULPIN, "G", "SHOP01", 2)
        assert result == f"{ULPIN}-FG-USHOP01-R02"

    def test_utility_basement(self):
        result = generate_vertical_id(ULPIN, "B1", "UTIL01", 1)
        assert result == f"{ULPIN}-FB1-UUTIL01-R01"

    def test_default_revision(self):
        result = generate_vertical_id(ULPIN, "04", "401")
        assert result.endswith("-R01")

    def test_high_floor(self):
        result = generate_vertical_id(ULPIN, "99", "PENT01", 1)
        assert result == f"{ULPIN}-F99-UPENT01-R01"

    def test_deep_basement(self):
        result = generate_vertical_id(ULPIN, "B9", "STORE01", 3)
        assert result == f"{ULPIN}-FB9-USTORE01-R03"

    def test_deterministic(self):
        """Same inputs must always produce the same output."""
        a = generate_vertical_id(ULPIN, "04", "401", 1)
        b = generate_vertical_id(ULPIN, "04", "401", 1)
        assert a == b

    def test_invalid_ulpin_too_short(self):
        with pytest.raises(Exception):
            generate_vertical_id("ABC", "04", "401", 1)

    def test_invalid_ulpin_lowercase(self):
        with pytest.raises(Exception):
            generate_vertical_id("7a4b9c2d8e1f6g", "04", "401", 1)

    def test_invalid_level_00(self):
        with pytest.raises(Exception):
            generate_vertical_id(ULPIN, "00", "401", 1)

    def test_invalid_revision_zero(self):
        with pytest.raises(Exception):
            generate_vertical_id(ULPIN, "04", "401", 0)

    def test_invalid_revision_100(self):
        with pytest.raises(Exception):
            generate_vertical_id(ULPIN, "04", "401", 100)

    def test_invalid_unit_code_lowercase(self):
        with pytest.raises(Exception):
            generate_vertical_id(ULPIN, "04", "apt401", 1)

    def test_invalid_unit_code_too_long(self):
        with pytest.raises(Exception):
            generate_vertical_id(ULPIN, "04", "A" * 17, 1)


# ======================================================================
# parse_vertical_id
# ======================================================================

class TestParseVerticalId:
    """Tests for parse_vertical_id()."""

    def test_parse_floor(self):
        vid = parse_vertical_id(f"{ULPIN}-F04-U401-R01")
        assert vid.parent_ulpin == ULPIN
        assert vid.level == "04"
        assert vid.unit_code == "401"
        assert vid.revision == 1

    def test_parse_basement(self):
        vid = parse_vertical_id(f"{ULPIN}-FB1-UPARK24-R01")
        assert vid.level == "B1"
        assert vid.unit_code == "PARK24"

    def test_parse_ground(self):
        vid = parse_vertical_id(f"{ULPIN}-FG-USHOP01-R02")
        assert vid.level == "G"
        assert vid.revision == 2

    def test_parse_utility(self):
        vid = parse_vertical_id(f"{ULPIN}-FB1-UUTIL01-R01")
        assert vid.unit_code == "UTIL01"

    def test_round_trip(self):
        """generate → parse → regenerate must be identity."""
        original = generate_vertical_id(ULPIN, "B3", "MECH02", 5)
        parsed = parse_vertical_id(original)
        regenerated = generate_vertical_id(
            parsed.parent_ulpin,
            parsed.level,
            parsed.unit_code,
            parsed.revision,
        )
        assert regenerated == original

    def test_parse_non_string(self):
        with pytest.raises(ParsingError, match="Expected a string"):
            parse_vertical_id(12345)  # type: ignore[arg-type]

    def test_parse_empty_string(self):
        with pytest.raises(ParsingError):
            parse_vertical_id("")

    def test_parse_too_few_segments(self):
        with pytest.raises(ParsingError, match="segments"):
            parse_vertical_id(f"{ULPIN}-F04-U401")

    def test_parse_too_many_segments(self):
        with pytest.raises(ParsingError, match="segments"):
            parse_vertical_id(f"{ULPIN}-F04-U401-R01-EXTRA")

    def test_parse_bad_ulpin(self):
        with pytest.raises(ParsingError, match="ULPIN"):
            parse_vertical_id("SHORT-F04-U401-R01")

    def test_parse_bad_level(self):
        with pytest.raises(ParsingError, match="level"):
            parse_vertical_id(f"{ULPIN}-FX9-U401-R01")

    def test_parse_bad_revision(self):
        with pytest.raises(ParsingError, match="revision"):
            parse_vertical_id(f"{ULPIN}-F04-U401-RABC")

    def test_parse_lowercase_ulpin(self):
        with pytest.raises(ParsingError):
            parse_vertical_id("7a4b9c2d8e1f6g-F04-U401-R01")


# ======================================================================
# validate_vertical_id
# ======================================================================

class TestValidateVerticalId:
    """Tests for validate_vertical_id()."""

    @pytest.mark.parametrize("vid", [
        f"{ULPIN}-F04-U401-R01",
        f"{ULPIN}-FB1-UPARK24-R01",
        f"{ULPIN}-FG-USHOP01-R02",
        f"{ULPIN}-FB1-UUTIL01-R01",
        f"{ULPIN}-F99-UPENT01-R99",
        f"{ULPIN}-FB9-USTORE01-R03",
    ])
    def test_valid_ids(self, vid):
        result = validate_vertical_id(vid)
        assert result.is_valid is True
        assert result.errors == []

    def test_invalid_empty(self):
        result = validate_vertical_id("")
        assert result.is_valid is False

    def test_invalid_non_string(self):
        result = validate_vertical_id(None)  # type: ignore[arg-type]
        assert result.is_valid is False

    def test_invalid_wrong_segment_count(self):
        result = validate_vertical_id("ONLY-TWO")
        assert result.is_valid is False
        assert any("segments" in e.lower() for e in result.errors)

    def test_invalid_ulpin_short(self):
        result = validate_vertical_id("ABC-F04-U401-R01")
        assert result.is_valid is False
        assert any("14 characters" in e or "ULPIN" in e for e in result.errors)

    def test_invalid_ulpin_lowercase(self):
        result = validate_vertical_id("7a4b9c2d8e1f6g-F04-U401-R01")
        assert result.is_valid is False

    def test_invalid_level_x(self):
        result = validate_vertical_id(f"{ULPIN}-FX9-U401-R01")
        assert result.is_valid is False
        assert any("level" in e.lower() for e in result.errors)

    def test_invalid_level_00(self):
        result = validate_vertical_id(f"{ULPIN}-F00-U401-R01")
        assert result.is_valid is False
        assert any("00" in e for e in result.errors)

    def test_invalid_unit_missing(self):
        result = validate_vertical_id(f"{ULPIN}-F04-U-R01")
        assert result.is_valid is False

    def test_invalid_unit_too_long(self):
        result = validate_vertical_id(
            f"{ULPIN}-F04-U{'A' * 17}-R01"
        )
        assert result.is_valid is False

    def test_invalid_revision_r00(self):
        result = validate_vertical_id(f"{ULPIN}-F04-U401-R00")
        assert result.is_valid is False
        assert any("01" in e or "00" in e for e in result.errors)

    def test_invalid_revision_letters(self):
        result = validate_vertical_id(f"{ULPIN}-F04-U401-RAB")
        assert result.is_valid is False

    def test_missing_f_prefix(self):
        result = validate_vertical_id(f"{ULPIN}-X04-U401-R01")
        assert result.is_valid is False
        assert any("'F'" in e for e in result.errors)

    def test_missing_u_prefix(self):
        result = validate_vertical_id(f"{ULPIN}-F04-X401-R01")
        assert result.is_valid is False
        assert any("'U'" in e for e in result.errors)

    def test_missing_r_prefix(self):
        result = validate_vertical_id(f"{ULPIN}-F04-U401-X01")
        assert result.is_valid is False
        assert any("'R'" in e for e in result.errors)


# ======================================================================
# increment_revision
# ======================================================================

class TestIncrementRevision:
    """Tests for increment_revision()."""

    def test_r01_to_r02(self):
        old = f"{ULPIN}-F04-U401-R01"
        new = increment_revision(old)
        assert new == f"{ULPIN}-F04-U401-R02"

    def test_r50_to_r51(self):
        old = f"{ULPIN}-FG-USHOP01-R50"
        new = increment_revision(old)
        assert new.endswith("-R51")

    def test_r98_to_r99(self):
        old = f"{ULPIN}-F04-U401-R98"
        new = increment_revision(old)
        assert new.endswith("-R99")

    def test_r99_raises(self):
        old = f"{ULPIN}-F04-U401-R99"
        with pytest.raises(VerticalIdValidationError, match="R99"):
            increment_revision(old)

    def test_preserves_all_components(self):
        old = f"{ULPIN}-FB3-UMECH02-R07"
        new = increment_revision(old)
        vid = parse_vertical_id(new)
        assert vid.parent_ulpin == ULPIN
        assert vid.level == "B3"
        assert vid.unit_code == "MECH02"
        assert vid.revision == 8


# ======================================================================
# build_human_readable_label
# ======================================================================

class TestBuildHumanReadableLabel:
    """Tests for build_human_readable_label()."""

    def test_floor(self):
        label = build_human_readable_label(f"{ULPIN}-F04-U401-R01")
        assert label == "Floor 4, Unit 401, Revision 01"

    def test_ground(self):
        label = build_human_readable_label(f"{ULPIN}-FG-USHOP01-R02")
        assert label == "Ground Floor, Unit SHOP01, Revision 02"

    def test_basement(self):
        label = build_human_readable_label(f"{ULPIN}-FB1-UPARK24-R01")
        assert label == "Basement 1, Unit PARK24, Revision 01"

    def test_deep_basement(self):
        label = build_human_readable_label(f"{ULPIN}-FB9-USTORE01-R03")
        assert label == "Basement 9, Unit STORE01, Revision 03"

    def test_high_floor(self):
        label = build_human_readable_label(f"{ULPIN}-F99-UPENT01-R01")
        assert label == "Floor 99, Unit PENT01, Revision 01"

    def test_utility(self):
        label = build_human_readable_label(f"{ULPIN}-FB1-UUTIL01-R01")
        assert label == "Basement 1, Unit UTIL01, Revision 01"
