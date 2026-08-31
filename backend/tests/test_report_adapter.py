"""Tests for the report service adapter."""
import sys
import tempfile
from pathlib import Path
import pytest
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.report_service import ReportService

@pytest.fixture
def report_service():
    return ReportService()

def test_generate_report(report_service):
    validation_data = {
        "parent_ulpin": "7A4B9C2D8E1F6G",
        "timestamp": "2026-08-30T12:00:00Z",
        "generated_by": "BhuDrishti 3D Test Suite",
        "confidence_scores": {"overall": 0.85},
        "parcel": {
            "parcel_id": "P001",
            "area_sqm": 300.0,
            "boundary_coordinates": [[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]],
            "land_use": "residential",
            "survey_number": "SUR-001",
        },
        "building": {
            "building_id": "BLD001",
            "building_name": "Test Tower",
            "footprint": [[2, 2], [18, 2], [18, 13], [2, 13], [2, 2]],
            "height_m": 15.0,
            "num_floors": 5,
        },
        "levels": [
            {
                "level_code": "G",
                "level_number": 0,
                "height_m": 3.0,
                "floor_area_sqm": 176.0,
                "level_type": "above_ground",
                "z_min_m": 0.0,
                "z_max_m": 3.0,
            },
        ],
        "spatial_units": [
            {
                "vertical_id": "7A4B9C2D8E1F6G-FG-USHOP01-R01",
                "unit_id": "U001",
                "level_code": "G",
                "unit_type": "commercial",
                "area_sqm": 80.0,
                "usage_type": "commercial",
                "footprint": [[3, 3], [10, 3], [10, 13], [3, 13], [3, 3]],
                "status": "valid",
                "z_min_m": 0.0,
                "z_max_m": 3.0,
            },
        ],
        "property_rights": [
            {
                "right_id": "R001",
                "vertical_id": "7A4B9C2D8E1F6G-FG-USHOP01-R01",
                "rights_type": "ownership",
                "holder_name_masked": "R***A",
                "valid": True,
            },
        ],
        "topology_conflicts": [],
        "source_metadata": [
            {
                "source_id": "SRC001",
                "file_name": "test_data.geojson",
                "source_type": "geojson",
                "timestamp": "2026-08-30T12:00:00Z",
                "confidence": 0.9,
                "sha256_hash": "a" * 64,
            },
        ],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        result = report_service.generate(validation_data, output_dir=tmpdir)
        assert "html_path" in result
        assert "pdf_path" in result
        assert "manifest" in result
