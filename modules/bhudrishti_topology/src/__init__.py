"""BhuDrishti 3D Topology Validator — public API.

This package validates vertical property geometry and detects 3D
ownership / property conflicts using a 2.5‑D cadastral method.

Public functions
----------------
validate_building
    Run full validation on a ``BuildingInput``.
validate_spatial_units
    Validate individual spatial units against a building.
detect_volume_conflicts
    Detect pairwise 2.5‑D volume conflicts.
calculate_overlap_metrics
    Calculate overlap metrics between two ``SpatialUnit`` objects.
generate_validation_summary
    Generate a ``ValidationSummary`` from a list of conflicts.
"""

from .geometry_utils import calculate_overlap_metrics
from .models import (
    BuildingInput,
    ConflictResult,
    ConflictType,
    LevelInfo,
    Severity,
    SpatialUnit,
    ValidationSummary,
)
from .topology_validator import (
    detect_volume_conflicts,
    generate_validation_summary,
    validate_building,
    validate_spatial_units,
)

__all__ = [
    # Public functions
    "validate_building",
    "validate_spatial_units",
    "detect_volume_conflicts",
    "calculate_overlap_metrics",
    "generate_validation_summary",
    # Models
    "BuildingInput",
    "ConflictResult",
    "ConflictType",
    "LevelInfo",
    "Severity",
    "SpatialUnit",
    "ValidationSummary",
]

__version__ = "0.1.0"
