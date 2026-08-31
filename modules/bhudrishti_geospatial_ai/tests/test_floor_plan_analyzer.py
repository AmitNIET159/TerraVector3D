"""Tests for floor-plan analyser."""

import numpy as np
import cv2
import pytest
from pathlib import Path

from src.floor_plan_analyzer import analyze_floor_plan


def _create_test_image(tmp_path: Path, n_rooms: int = 3) -> Path:
    """Create a synthetic floor-plan image with white-bordered rooms on black."""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    rooms = [
        (50, 50, 250, 180),
        (300, 50, 500, 180),
        (50, 230, 250, 400),
    ]
    for x1, y1, x2, y2 in rooms[:n_rooms]:
        cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
        # Fill interior so contour detection picks up closed regions
        cv2.rectangle(img, (x1 + 3, y1 + 3), (x2 - 3, y2 - 3), (180, 180, 180), -1)
    path = tmp_path / "test_floor_plan.png"
    cv2.imwrite(str(path), img)
    return path


class TestFloorPlanAnalyzer:
    def test_detect_contours(self, tmp_path):
        img_path = _create_test_image(tmp_path)
        result = analyze_floor_plan(str(img_path), metres_per_pixel=0.05)
        assert len(result["proposed_units"]) >= 1

    def test_no_scale_area_null(self, tmp_path):
        img_path = _create_test_image(tmp_path)
        result = analyze_floor_plan(str(img_path), metres_per_pixel=None)
        for unit in result["proposed_units"]:
            assert unit["area_sqm"] is None
            assert unit["metric_area_available"] is False
            assert any(
                "Scale calibration" in w for w in unit["warnings"]
            )

    def test_with_scale_area_computed(self, tmp_path):
        img_path = _create_test_image(tmp_path)
        result = analyze_floor_plan(str(img_path), metres_per_pixel=0.05)
        for unit in result["proposed_units"]:
            assert unit["area_sqm"] is not None
            assert unit["area_sqm"] > 0
            assert unit["metric_area_available"] is True

    def test_human_verification_required(self, tmp_path):
        img_path = _create_test_image(tmp_path)
        result = analyze_floor_plan(str(img_path))
        assert result["human_verification_required"] is True
        for unit in result["proposed_units"]:
            assert unit["human_verification_required"] is True

    def test_confidence_range(self, tmp_path):
        img_path = _create_test_image(tmp_path)
        result = analyze_floor_plan(str(img_path))
        for unit in result["proposed_units"]:
            assert 0.0 <= unit["confidence_score"] <= 1.0

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            analyze_floor_plan("nonexistent_image.png")
