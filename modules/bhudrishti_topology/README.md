# bhudrishti_topology

**Validate vertical property geometry and detect 3D ownership / property
conflicts for BhuDrishti 3D.**

## Overview

`bhudrishti_topology` is a standalone Python module that implements
**2.5-D cadastral topology validation**:

| Dimension | What it represents |
|---|---|
| **2-D footprint** | Closed polygon in local Cartesian metres |
| **z_min_m / z_max_m** | Vertical height extents of the spatial unit |
| **Volume** | Approximated as *footprint area × height* |

A **volumetric conflict** exists only when **both** horizontal polygon
overlap **and** vertical height-range overlap are present.

---

## Directory Structure

```
bhudrishti_topology/
├── src/
│   ├── __init__.py              # Public API re-exports
│   ├── models.py                # Pydantic data models & enums
│   ├── geometry_utils.py        # Shapely polygon helpers
│   ├── topology_validator.py    # Core validation engine
│   ├── conflict_classifier.py   # Conflict type & severity logic
│   └── cli.py                   # Command-line interface
├── examples/
│   ├── valid_building_input.json
│   ├── conflict_building_input.json
│   └── expected_conflict_output.json
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_geometry_utils.py
│   ├── test_topology_validator.py
│   └── test_conflict_classifier.py
├── README.md
├── INTEGRATION.md
└── requirements.txt
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the CLI

```bash
# From the parent directory of bhudrishti_topology/
python -m bhudrishti_topology.src.cli validate bhudrishti_topology/examples/conflict_building_input.json
```

### 3. Run tests

```bash
cd bhudrishti_topology
python -m pytest tests/ -v
```

---

## Vertical ID Format

```
<parent_ulpin>-F<level>-U<unit_code>-R<revision>
```

| Field | Description | Example |
|---|---|---|
| `parent_ulpin` | 14 uppercase alphanumeric chars | `7A4B9C2D8E1F6G` |
| `F<level>` | Floor / level code | `F04`, `FB1` |
| `U<unit_code>` | Unit identifier | `U401`, `UP24`, `UUTIL01` |
| `R<revision>` | Revision number | `R01` |

**Examples:**
- `7A4B9C2D8E1F6G-F04-U401-R01`
- `7A4B9C2D8E1F6G-FB1-UP24-R01`
- `7A4B9C2D8E1F6G-FB1-UUTIL01-R01`

---

## Public API

### 1. `validate_building(building_input: BuildingInput) -> ValidationSummary`

Run the full validation pipeline on a building — validates individual
units, detects pairwise volume conflicts, and returns a summary.

### 2. `validate_spatial_units(spatial_units, building) -> List[ConflictResult]`

Validate each spatial unit against the building definition:
- Invalid / self-intersecting polygon
- Open polygon ring
- Invalid z range (z_min ≥ z_max)
- Negative area
- Duplicate vertical ID
- Unit outside building footprint
- Unit not assigned to a valid level
- Floating unit / gap warning
- Unit extending beyond total building height

### 3. `detect_volume_conflicts(spatial_units) -> List[ConflictResult]`

Detect pairwise 2.5-D volumetric conflicts:
- Apartment × apartment → `VOLUME_OVERLAP` (high)
- Parking × apartment → `PARKING_APARTMENT_OVERLAP` (high)
- Utility × easement → `UTILITY_EASEMENT_REVIEW` (low)
- Utility × apartment → `UTILITY_EASEMENT_REVIEW` (medium)

### 4. `calculate_overlap_metrics(unit_a, unit_b) -> dict`

Calculate overlap metrics between any two spatial units. Returns:

```python
{
    "has_overlap": True,
    "horizontal_overlap_area_sqm": 3.4,
    "overlapping_z_min_m": 9.0,
    "overlapping_z_max_m": 12.0,
    "estimated_overlap_volume_cum": 10.2,
}
```

### 5. `generate_validation_summary(building_input, conflicts) -> ValidationSummary`

Build a `ValidationSummary` from a list of conflict results.

---

## Conflict Types

| Type | Severity | Trigger |
|---|---|---|
| `VOLUME_OVERLAP` | high | Two hard units (apartment/commercial) overlap |
| `DUPLICATE_VERTICAL_ID` | high | Same vertical ID on multiple units |
| `INVALID_GEOMETRY` | high | Self-intersecting, open ring, negative area |
| `INVALID_Z_RANGE` | high/medium | z_min ≥ z_max or exceeds building height |
| `UNIT_OUTSIDE_BUILDING` | medium | Unit footprint outside building boundary |
| `LEVEL_ASSIGNMENT_ERROR` | medium | Unit references undefined level |
| `PARKING_APARTMENT_OVERLAP` | high | Parking and apartment share volume |
| `UTILITY_EASEMENT_REVIEW` | low/medium | Utility/easement overlap (needs review) |
| `FLOATING_UNIT_WARNING` | low | Unit z_min above level z_min by > 0.5 m |

---

## Conflict Result Schema

Every conflict result contains:

| Field | Type | Description |
|---|---|---|
| `conflict_id` | string | Auto-generated UUID-based ID |
| `conflict_type` | enum | One of the 9 conflict types |
| `severity` | enum | `low`, `medium`, or `high` |
| `affected_unit_ids` | list[str] | Unit IDs involved |
| `affected_vertical_ids` | list[str] | Vertical IDs involved |
| `horizontal_overlap_area_sqm` | float | Horizontal overlap in m² |
| `overlapping_z_min_m` | float | Bottom of vertical overlap |
| `overlapping_z_max_m` | float | Top of vertical overlap |
| `estimated_overlap_volume_cum` | float | Overlap volume in m³ |
| `recommended_action` | string | What to do about it |
| `human_readable_explanation` | string | Plain-language description |

---

## Example: Deliberate Overlap

The `conflict_building_input.json` example contains a deliberate overlap
between `U401` and `U402` on floor 4:

- **U401** footprint: `(0,0)–(10.34,10)` → 103.4 m²
- **U402** footprint: `(10.0,0)–(20,10)` → 100.0 m²
- **Overlap strip**: `(10.0,0)–(10.34,10)` = **≈ 3.4 m²**
- **Vertical range**: both 9.0–12.0 m → height 3.0 m
- **Volume**: 3.4 × 3.0 = **≈ 10.2 m³**
- **Conflict type**: `VOLUME_OVERLAP`, severity `high`

---

## Python Usage

```python
import json
from bhudrishti_topology.src import validate_building
from bhudrishti_topology.src.models import BuildingInput

with open("examples/conflict_building_input.json") as f:
    data = json.load(f)

building = BuildingInput(**data)
summary = validate_building(building)

print(f"Valid: {summary.is_valid}")
print(f"Conflicts: {summary.total_conflicts}")
for c in summary.conflicts:
    print(f"  [{c.severity.value}] {c.conflict_type.value}: "
          f"{c.human_readable_explanation}")
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| shapely | ≥ 2.0 | Polygon geometry operations |
| pydantic | ≥ 2.0 | Data validation & serialization |
| pytest | ≥ 7.0 | Test framework |

All packages are free and open-source. No paid APIs, databases, or
cloud services are required.

---

## Notes

- All coordinates are in **local Cartesian metres** (never lat/lon).
- All data is **fictional** — no real land records are used.
- Parent ULPIN is always **exactly 14 uppercase alphanumeric characters**.
- The module is designed for future integration with FastAPI and
  Three.js — see [INTEGRATION.md](INTEGRATION.md).
