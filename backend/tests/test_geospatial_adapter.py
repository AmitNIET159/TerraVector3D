"""Tests for the geospatial service adapter."""
import sys
from pathlib import Path
import pytest
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.geospatial_service import GeospatialService

@pytest.fixture
def geospatial_service():
    return GeospatialService()

def test_normalize_geojson(geospatial_service):
    geojson = {
        "type": "Feature",
        "properties": {"ulpin": "7A4B9C2D8E1F6G"},
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]],
        },
    }
    result = geospatial_service.normalize(geojson)
    assert "area_sqm" in result
    assert "coordinate_reference" in result
    assert result["coordinate_reference"] == "LOCAL_METERS"
