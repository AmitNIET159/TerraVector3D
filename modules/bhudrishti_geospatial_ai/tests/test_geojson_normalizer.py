"""Tests for GeoJSON normaliser."""

import json
import pytest
from pathlib import Path

from src.geojson_normalizer import normalize_geojson
from src.models import validate_ulpin, DEMO_PARENT_ULPIN


def _write_geojson(tmp_path: Path, geometry: dict, properties: dict | None = None) -> Path:
    """Helper: write a GeoJSON FeatureCollection to a temp file."""
    path = tmp_path / "test.geojson"
    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties or {},
            }
        ],
    }
    path.write_text(json.dumps(fc), encoding="utf-8")
    return path


class TestNormalizeGeojson:
    def test_valid_polygon(self, tmp_path):
        geom = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]],
        }
        path = _write_geojson(tmp_path, geom)
        result = normalize_geojson(str(path))

        assert result["parent_ulpin"] == DEMO_PARENT_ULPIN
        assert result["coordinate_reference"] == "LOCAL_METERS"
        assert result["human_verification_required"] is True
        assert result["area_sqm"] > 0
        assert "footprint" in result
        assert "bounding_box" in result
        assert "confidence_score" in result
        assert "warnings" in result
        assert "source_type" in result

    def test_multipolygon_preserved(self, tmp_path):
        geom = {
            "type": "MultiPolygon",
            "coordinates": [
                [[[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]]],
                [[[10, 10], [15, 10], [15, 15], [10, 15], [10, 10]]],
            ],
        }
        path = _write_geojson(tmp_path, geom)
        result = normalize_geojson(str(path))

        # footprint should be a list of polygon coord lists
        assert isinstance(result["footprint"], list)
        assert len(result["footprint"]) == 2
        # each part should itself be a list of [x, y] pairs
        for part in result["footprint"]:
            assert isinstance(part, list)
            assert all(isinstance(p, list) and len(p) == 2 for p in part)

    def test_ccw_winding(self, tmp_path):
        # Clockwise polygon
        geom = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [0, 10], [10, 10], [10, 0], [0, 0]]],
        }
        path = _write_geojson(tmp_path, geom)
        result = normalize_geojson(str(path))

        # After normalisation, the signed area (shoelace) should be positive (CCW)
        coords = result["footprint"]
        signed_area = sum(
            coords[i][0] * coords[i + 1][1] - coords[i + 1][0] * coords[i][1]
            for i in range(len(coords) - 1)
        )
        assert signed_area > 0, "Polygon should be wound counter-clockwise"

    def test_invalid_geojson_empty(self, tmp_path):
        path = tmp_path / "empty.geojson"
        path.write_text(json.dumps({"type": "FeatureCollection", "features": []}), encoding="utf-8")
        with pytest.raises(ValueError):
            normalize_geojson(str(path))

    def test_area_positive(self, tmp_path):
        geom = {
            "type": "Polygon",
            "coordinates": [[[5, 5], [15, 5], [15, 25], [5, 25], [5, 5]]],
        }
        path = _write_geojson(tmp_path, geom)
        result = normalize_geojson(str(path))
        assert result["area_sqm"] == pytest.approx(200.0, abs=0.1)

    def test_translation_to_origin(self, tmp_path):
        geom = {
            "type": "Polygon",
            "coordinates": [[[100, 200], [110, 200], [110, 210], [100, 210], [100, 200]]],
        }
        path = _write_geojson(tmp_path, geom)
        result = normalize_geojson(str(path))
        bb = result["bounding_box"]
        assert bb["min_x"] == pytest.approx(0.0, abs=0.01)
        assert bb["min_y"] == pytest.approx(0.0, abs=0.01)


class TestValidateUlpin:
    def test_valid(self):
        assert validate_ulpin("7A4B9C2D8E1F6G") == "7A4B9C2D8E1F6G"

    @pytest.mark.parametrize("bad_ulpin", [
        "abc",
        "12345",
        "7a4b9c2d8e1f6g",  # lowercase
        "7A4B9C2D8E1F6G!",  # special char
        "7A4B9C2D8E1F6",  # 13 chars
        "7A4B9C2D8E1F6GX",  # 15 chars
    ])
    def test_invalid(self, bad_ulpin):
        with pytest.raises(ValueError):
            validate_ulpin(bad_ulpin)
