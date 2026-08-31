"""Service adapter for bhudrishti_topology module."""
from app.services.module_adapter import ensure_module_path
ensure_module_path()

from modules.bhudrishti_topology.src import validate_building
from modules.bhudrishti_topology.src.models import BuildingInput

class TopologyService:
    def validate(self, building_data: dict) -> dict:
        building_input = BuildingInput(**building_data)
        summary = validate_building(building_input)
        return summary.model_dump() if hasattr(summary, "model_dump") else {
            "building_id": summary.building_id, "parent_ulpin": summary.parent_ulpin,
            "total_units": summary.total_units, "total_conflicts": summary.total_conflicts,
            "conflicts_by_severity": summary.conflicts_by_severity, "conflicts_by_type": summary.conflicts_by_type,
            "conflicts": [c.model_dump() if hasattr(c, "model_dump") else c.__dict__ for c in summary.conflicts],
            "is_valid": summary.is_valid
        }
