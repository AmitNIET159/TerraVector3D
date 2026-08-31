"""Tests for the validation module."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.generate_demo_data import generate_all
from src.validate_demo_data import ValidationResult, validate_all


class TestValidateAll:
    """Run the full validator against freshly generated data."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path: Path):
        self.data_dir = tmp_path / "data"
        generate_all(self.data_dir)
        self.result = validate_all(self.data_dir)

    def test_validation_passes(self):
        assert self.result.passed, self.result.summary()

    def test_no_errors(self):
        assert len(self.result.errors) == 0, self.result.errors

    def test_overlap_warning_detected(self):
        overlap_warnings = [
            w for w in self.result.warnings if "Overlap" in w
        ]
        assert len(overlap_warnings) >= 1

    def test_overlap_warning_mentions_f04(self):
        overlap_warnings = [
            w for w in self.result.warnings if "Overlap" in w
        ]
        f04_overlaps = [w for w in overlap_warnings if "04" in w]
        assert len(f04_overlaps) >= 1

    def test_overlap_area_approximately_3_4(self):
        overlap_warnings = [
            w for w in self.result.warnings if "Overlap" in w and "04" in w
        ]
        # The warning should contain a numeric overlap value near 3.4
        assert any("3.4" in w or "3.40" in w for w in overlap_warnings)

    def test_needs_review_info(self):
        nr_info = [i for i in self.result.info if "needs_review" in i]
        assert len(nr_info) >= 1

    def test_parking_right_info(self):
        pr_info = [i for i in self.result.info if "parking_right" in i]
        assert len(pr_info) >= 1

    def test_utility_easement_info(self):
        ue_info = [i for i in self.result.info if "utility_easement" in i]
        assert len(ue_info) >= 1


class TestValidationResult:
    """Unit tests for the ValidationResult helper class."""

    def test_empty_result_passes(self):
        r = ValidationResult()
        assert r.passed

    def test_error_fails(self):
        r = ValidationResult()
        r.error("something wrong")
        assert not r.passed

    def test_warning_still_passes(self):
        r = ValidationResult()
        r.warn("minor issue")
        assert r.passed

    def test_summary_format(self):
        r = ValidationResult()
        r.error("e1")
        r.warn("w1")
        r.add_info("i1")
        s = r.summary()
        assert "FAILED" in s
        assert "[ERROR]" in s
        assert "[WARN]" in s
        assert "[INFO]" in s
