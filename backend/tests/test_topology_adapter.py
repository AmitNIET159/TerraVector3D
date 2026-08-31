"""Tests for the topology service adapter."""
import sys
from pathlib import Path
import pytest
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.topology_service import TopologyService

@pytest.fixture
def topology_service():
    return TopologyService()

def test_validate_valid_building(topology_service):
    building_data = {
        "building_id": "BLD001",
        "parent_ulpin": "7A4B9C2D8E1F6G",
        "footprint": [[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]],
        "levels": [
            {"level_code": "G", "z_min_m": 0.0, "z_max_m": 3.0},
            {"level_code": "01", "z_min_m": 3.0, "z_max_m": 6.0},
        ],
        "total_height_m": 6.0,
        "spatial_units": [
            {
                "unit_id": "U001",
                "vertical_id": "7A4B9C2D8E1F6G-FG-USHOP01-R01",
                "parent_ulpin": "7A4B9C2D8E1F6G",
                "building_id": "BLD001",
                "level_code": "G",
                "unit_type": "commercial",
                "footprint": [[1, 1], [10, 1], [10, 14], [1, 14], [1, 1]],
                "z_min_m": 0.0,
                "z_max_m": 3.0,
                "area_sqm": 117.0,
                "usage_type": "commercial",
                "status": "valid",
            },
        ],
    }
    result = topology_service.validate(building_data)
    assert "building_id" in result
    assert "is_valid" in result
    assert result["total_units"] == 1
