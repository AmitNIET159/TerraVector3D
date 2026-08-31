# BhuDrishti 3D — Demo Cadastre Module

> **⚠️ FICTIONAL DATA DISCLAIMER**
>
> Every record in this module — property boundaries, unit geometries, owner
> names, rights records, and conflict scenarios — is **entirely fictional**.
> No real land records, property owners, survey data, or geographic locations
> are represented.  This dataset exists **solely** for hackathon / SIH
> demonstration purposes and **must not** be used for any legal, financial, or
> administrative decision-making.

## Purpose

`bhudrishti_demo_cadastre` generates a complete, internally consistent set of
demo data for **BhuDrishti 3D** — a 3D ULPIN and Vertical Property Mapping
System.  The data describes a single fictional multi-storey apartment building:

| Field             | Value                               |
|-------------------|-------------------------------------|
| Building name     | Green Heights Apartment             |
| Location          | Demo Ward, Pune (fictional)         |
| Parent ULPIN      | `7A4B9C2D8E1F6G`                    |
| Structure         | 1 basement, ground floor, 5 residential floors |
| Units             | 10 flats, 6 parking, 1 utility corridor, 1 lobby |

## Vertical ID Format

Every spatial unit receives a **vertical ID** following this scheme:

```
<parent_ulpin>-F<level_code>-U<unit_code>-R<revision>
```

Examples:

```
7A4B9C2D8E1F6G-F04-U401-R01        # Flat 401 on Floor 4
7A4B9C2D8E1F6G-FB1-UP03-R01        # Parking P03 in Basement 1
7A4B9C2D8E1F6G-FB1-UUTIL01-R01     # Utility corridor in Basement 1
7A4B9C2D8E1F6G-FG-ULOBBY01-R01     # Lobby on Ground Floor
```

## Coordinate System

All geometry uses **local Cartesian metres** (never latitude/longitude).
The origin `(0, 0)` is the south-west corner of the parcel.

## Directory Structure

```
bhudrishti_demo_cadastre/
├── src/
│   ├── __init__.py
│   ├── models.py               # Pydantic v2 data models
│   ├── generate_demo_data.py   # Generates all JSON files
│   └── validate_demo_data.py   # Validates generated data
├── data/                        # Generated JSON output
│   ├── demo_parcel.geojson
│   ├── demo_building.json
│   ├── demo_levels.json
│   ├── demo_spatial_units.json
│   ├── demo_rights_records.json
│   ├── demo_source_metadata.json
│   └── demo_conflict_scenarios.json
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_generate.py
│   └── test_validate.py
├── README.md
├── INTEGRATION.md
└── requirements.txt
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate demo data

```bash
python -m src.generate_demo_data
```

This writes seven JSON files into `data/`.

### 3. Validate the generated data

```bash
python -m src.validate_demo_data
```

Expected output: **Validation PASSED** with warnings for the intentional F04
overlap and info messages about the `needs_review` unit, parking right, and
utility easement.

### 4. Run tests

```bash
pytest tests/ -v
```

## Intentional Validation Scenarios

The following edge cases are **deliberately** built into the data:

| # | Scenario | Details |
|---|----------|---------|
| 1 | **Spatial overlap** | Flats U401 and U402 on level F04 overlap by ≈ 3.4 sq.m |
| 2 | **Infrastructure passthrough** | A utility corridor runs through basement B1 |
| 3 | **Parking right** | Parking unit P03 has a valid `parking_right` record |
| 4 | **Needs-review unit** | Flat U302 on level F03 is marked `needs_review` |

## Data File Summary

| File | Format | Description |
|------|--------|-------------|
| `demo_parcel.geojson` | GeoJSON FeatureCollection | Parcel boundary & metadata |
| `demo_building.json` | JSON object | Building footprint & attributes |
| `demo_levels.json` | JSON array | 7 levels (B1, G, F01–F05) |
| `demo_spatial_units.json` | JSON array | 18 spatial units with footprints |
| `demo_rights_records.json` | JSON array | Ownership, lease, parking, easement records |
| `demo_source_metadata.json` | JSON object | Data provenance & disclaimer |
| `demo_conflict_scenarios.json` | JSON array | 3 documented edge-case scenarios |

## Sample Input / Output

**Input:** None — the generator is self-contained.

**Sample output** (excerpt from `demo_spatial_units.json`):

```json
{
  "unit_id": "UNIT-F04-401",
  "vertical_id": "7A4B9C2D8E1F6G-F04-U401-R01",
  "parent_ulpin": "7A4B9C2D8E1F6G",
  "building_id": "BLD-GHA-001",
  "level_code": "04",
  "unit_type": "apartment",
  "footprint": {
    "type": "Polygon",
    "coordinates": [[[5, 5], [20.17, 5], [20.17, 25], [5, 25], [5, 5]]]
  },
  "z_min_m": 13.0,
  "z_max_m": 16.0,
  "area_sqm": 303.4,
  "usage_type": "residential",
  "status": "registered",
  "model_object_name": "F04_apartment_401"
}
```

## License

This module is provided as-is for demonstration and educational purposes.
