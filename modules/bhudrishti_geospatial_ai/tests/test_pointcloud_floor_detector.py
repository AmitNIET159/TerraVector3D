"""Tests for point-cloud floor detector."""

import numpy as np
import pytest
from pathlib import Path

from src.pointcloud_floor_detector import detect_floor_levels
from src.synthetic_pointcloud_generator import generate_synthetic_pointcloud
from src.ply_io import write_ply


@pytest.fixture
def synthetic_ply(tmp_path) -> Path:
    """Generate a deterministic synthetic building point cloud."""
    ply_path = tmp_path / "building.ply"
    generate_synthetic_pointcloud(
        str(ply_path),
        num_floors=5,
        include_basement=True,
        floor_height_m=3.0,
        points_per_slab=2500,
        noise_m=0.02,
        random_seed=42,
    )
    return ply_path


class TestPointcloudFloorDetector:
    def test_detect_levels_from_synthetic(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        # B1, G, F01-F05 = 7 cadastral levels + ROOF
        cadastral = result["suggested_cadastral_levels"]
        assert len(cadastral) == 7, (
            f"Expected 7 cadastral levels (B1,G,F01-F05), got {len(cadastral)}: "
            f"{[lv['level_code'] for lv in cadastral]}"
        )

    def test_b1_g_f_sequence(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        cadastral = result["suggested_cadastral_levels"]
        codes = [lv["level_code"] for lv in cadastral]

        # Should have B1
        assert "B1" in codes, f"Expected B1 in {codes}"
        # Should have G
        assert "G" in codes, f"Expected G in {codes}"
        # Should have F01 through F05
        for i in range(1, 6):
            expected = f"F{i:02d}"
            assert expected in codes, f"Expected {expected} in {codes}"

        # B1 must come before G which comes before F01
        b1_idx = codes.index("B1")
        g_idx = codes.index("G")
        f01_idx = codes.index("F01")
        assert b1_idx < g_idx < f01_idx

    def test_roof_not_f06(self, synthetic_ply):
        """Roof slab must never be classified as F06 by default."""
        result = detect_floor_levels(str(synthetic_ply))
        all_codes = [lv["level_code"] for lv in result["suggested_levels"]]
        cadastral_codes = [lv["level_code"] for lv in result["suggested_cadastral_levels"]]

        assert "F06" not in all_codes, f"F06 should not exist, got {all_codes}"
        assert "F06" not in cadastral_codes
        assert "ROOF" in all_codes, f"Expected ROOF in {all_codes}"

    def test_roof_is_not_cadastral(self, synthetic_ply):
        """ROOF entry must have is_cadastral_unit_level=False."""
        result = detect_floor_levels(str(synthetic_ply))
        roof_levels = [
            lv for lv in result["suggested_levels"]
            if lv["level_code"] == "ROOF"
        ]
        assert len(roof_levels) == 1
        roof = roof_levels[0]
        assert roof["is_cadastral_unit_level"] is False
        assert roof["level_type"] == "roof_slab"

    def test_roof_as_terrace_when_configured(self, synthetic_ply):
        """When include_roof_as_terrace=True, roof becomes a cadastral level."""
        result = detect_floor_levels(
            str(synthetic_ply), include_roof_as_terrace=True,
        )
        all_levels = result["suggested_levels"]
        cadastral = result["suggested_cadastral_levels"]

        # Last entry should be TERRACE, not ROOF
        last = all_levels[-1]
        assert last["level_code"] == "TERRACE"
        assert last["level_type"] == "terrace"
        assert last["is_cadastral_unit_level"] is True

        # TERRACE should appear in cadastral levels
        cadastral_codes = [lv["level_code"] for lv in cadastral]
        assert "TERRACE" in cadastral_codes

    def test_roof_slab_z_m_present(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        assert result["roof_slab_z_m"] is not None
        assert result["roof_slab_z_m"] > 0

    def test_z_min_z_max_volumes(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        for lv in result["suggested_cadastral_levels"]:
            assert lv["z_min_m"] < lv["z_max_m"]

    def test_slab_elevations_sorted(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        slabs = result["detected_slab_elevations_m"]
        assert slabs == sorted(slabs)

    def test_methods_used(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        assert len(result["method_used"]) >= 1
        for m in result["method_used"]:
            assert m in ("histogram", "ransac", "dbscan")

    def test_methods_attempted_always_three(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        assert set(result["methods_attempted"]) == {
            "histogram", "ransac", "dbscan",
        }

    def test_method_agreement_score_range(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        assert 0.0 <= result["method_agreement_score"] <= 1.0

    def test_estimated_floor_height(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        assert result["estimated_floor_height_m"] == pytest.approx(3.0, abs=1.0)

    def test_human_verification_all_levels(self, synthetic_ply):
        result = detect_floor_levels(str(synthetic_ply))
        assert result["human_verification_required"] is True
        for lv in result["suggested_levels"]:
            assert lv["human_verification_required"] is True

    def test_insufficient_points(self, tmp_path):
        ply_path = tmp_path / "tiny.ply"
        points = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]])
        write_ply(str(ply_path), points)

        result = detect_floor_levels(str(ply_path))
        assert any("Insufficient" in w for w in result["warnings"])

    def test_level_types_correct(self, synthetic_ply):
        """Each level_type must match its code category."""
        result = detect_floor_levels(str(synthetic_ply))
        for lv in result["suggested_levels"]:
            code = lv["level_code"]
            if code.startswith("B"):
                assert lv["level_type"] == "basement"
            elif code == "G":
                assert lv["level_type"] == "ground"
            elif code == "ROOF":
                assert lv["level_type"] == "roof_slab"
            elif code.startswith("F"):
                assert lv["level_type"] == "floor"

    def test_suggested_cadastral_excludes_roof(self, synthetic_ply):
        """suggested_cadastral_levels must not contain ROOF."""
        result = detect_floor_levels(str(synthetic_ply))
        for lv in result["suggested_cadastral_levels"]:
            assert lv["level_code"] != "ROOF"
            assert lv["is_cadastral_unit_level"] is True
