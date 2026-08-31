# Integration Guide — bhudrishti_demo_cadastre

This document explains how the **BhuDrishti 3D** master application
(FastAPI + PostgreSQL) can import and consume every JSON data file produced
by this module.

---

## Overview

The demo module generates **seven JSON files** in `data/`.  Each file maps
directly to one or more database tables and/or API resources in the master
application.

```
data/
├── demo_parcel.geojson           →  parcels table
├── demo_building.json            →  buildings table
├── demo_levels.json              →  levels table
├── demo_spatial_units.json       →  spatial_units table
├── demo_rights_records.json      →  rights_records table
├── demo_source_metadata.json     →  source_metadata table
└── demo_conflict_scenarios.json  →  conflict_scenarios table
```

---

## Step 1: Copy the Module

Place the entire module at:

```
BhuDrishti3D/modules/bhudrishti_demo_cadastre/
```

Ensure the `data/` directory contains all generated JSON files.  If not,
regenerate:

```bash
cd BhuDrishti3D/modules/bhudrishti_demo_cadastre
pip install -r requirements.txt
python -m src.generate_demo_data
```

---

## Step 2: Define SQLAlchemy / Tortoise ORM Models

Map each JSON schema to a database table.  Field names in the JSON already
follow **snake_case** convention, matching typical Python ORM column names.

### Example: `spatial_units` table (SQLAlchemy)

```python
from sqlalchemy import Column, String, Float, JSON, Enum
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class SpatialUnit(Base):
    __tablename__ = "spatial_units"

    unit_id          = Column(String, primary_key=True)
    vertical_id      = Column(String, unique=True, nullable=False)
    parent_ulpin     = Column(String(14), nullable=False, index=True)
    building_id      = Column(String, nullable=False)
    level_code       = Column(String, nullable=False)
    unit_type        = Column(String, nullable=False)
    footprint        = Column(JSON, nullable=False)   # GeoJSON polygon
    z_min_m          = Column(Float, nullable=False)
    z_max_m          = Column(Float, nullable=False)
    area_sqm         = Column(Float, nullable=False)
    usage_type       = Column(String, nullable=False)
    status           = Column(String, nullable=False)
    model_object_name = Column(String, nullable=False)
```

> **Tip:** If using PostGIS, store `footprint` as a `Geometry('POLYGON')`
> column instead of JSON.  You will need to transform the local-metre
> coordinates into a projected CRS first (or keep them as-is for demo).

---

## Step 3: Write an Import Script

Create a FastAPI startup event or management command that reads each JSON
file and upserts rows into the database.

### Example: generic JSON loader

```python
import json
from pathlib import Path
from sqlalchemy.orm import Session

DATA_DIR = Path("modules/bhudrishti_demo_cadastre/data")

def load_json(filename: str) -> list | dict:
    return json.loads((DATA_DIR / filename).read_text("utf-8"))

def import_spatial_units(db: Session) -> int:
    units = load_json("demo_spatial_units.json")
    count = 0
    for u in units:
        obj = SpatialUnit(**u)
        db.merge(obj)
        count += 1
    db.commit()
    return count
```

### Repeat for every table:

| JSON File                      | Loader Target        | Primary Key    |
|-------------------------------|----------------------|----------------|
| `demo_parcel.geojson`         | `parcels`            | `parcel_id`    |
| `demo_building.json`         | `buildings`          | `building_id`  |
| `demo_levels.json`           | `levels`             | `level_code`   |
| `demo_spatial_units.json`    | `spatial_units`      | `unit_id`      |
| `demo_rights_records.json`   | `rights_records`     | `right_id`     |
| `demo_source_metadata.json`  | `source_metadata`    | `source_id`    |
| `demo_conflict_scenarios.json`| `conflict_scenarios` | `conflict_id`  |

---

## Step 4: Expose via FastAPI Endpoints

### Example routes

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/demo", tags=["demo-cadastre"])

@router.get("/parcels/{parcel_id}")
def get_parcel(parcel_id: str, db: Session = Depends(get_db)):
    return db.query(Parcel).filter_by(parcel_id=parcel_id).first()

@router.get("/spatial-units")
def list_units(level_code: str | None = None, db: Session = Depends(get_db)):
    q = db.query(SpatialUnit)
    if level_code:
        q = q.filter_by(level_code=level_code)
    return q.all()

@router.get("/spatial-units/{unit_id}")
def get_unit(unit_id: str, db: Session = Depends(get_db)):
    return db.query(SpatialUnit).filter_by(unit_id=unit_id).first()

@router.get("/rights/{unit_id}")
def get_rights(unit_id: str, db: Session = Depends(get_db)):
    return db.query(RightsRecord).filter_by(unit_id=unit_id).all()

@router.get("/conflicts")
def list_conflicts(db: Session = Depends(get_db)):
    return db.query(ConflictScenario).all()
```

---

## Step 5: Wire Up the Three.js Frontend

Each spatial unit has a `model_object_name` field (e.g.,
`F04_apartment_401`) designed for matching against Three.js mesh objects:

```javascript
// In the Three.js scene loader
const response = await fetch('/api/v1/demo/spatial-units');
const units = await response.json();

units.forEach(unit => {
  const mesh = scene.getObjectByName(unit.model_object_name);
  if (mesh) {
    mesh.userData = unit;  // attach cadastre data to mesh
  }
});
```

---

## Step 6: Validate Before Import

Run the built-in validator to catch issues before database import:

```bash
cd modules/bhudrishti_demo_cadastre
python -m src.validate_demo_data
```

Or call it programmatically from your master app:

```python
from modules.bhudrishti_demo_cadastre.src.validate_demo_data import validate_all

result = validate_all()
if not result.passed:
    raise RuntimeError(f"Demo data invalid:\n{result.summary()}")
```

---

## Key Integration Notes

| Concern | Detail |
|---------|--------|
| **Coordinate system** | Local Cartesian metres, origin at SW corner of parcel. Never lat/lon. |
| **ID format** | Vertical IDs follow `<ULPIN>-F<level>-U<unit>-R<rev>`. |
| **snake_case** | All JSON keys and Python fields use snake_case. |
| **Parent ULPIN** | Always `7A4B9C2D8E1F6G` (14 uppercase alphanumeric). Unchanged across all records. |
| **Conflict scenarios** | The overlap on F04 and the `needs_review` unit are intentional test cases. |
| **Disclaimer** | All data is fictional.  See `demo_source_metadata.json` → `data_disclaimer`. |

---

## Pydantic Models for Direct Import

If your FastAPI app uses Pydantic for request/response schemas, you can
import the models directly:

```python
from modules.bhudrishti_demo_cadastre.src.models import (
    SpatialUnit,
    RightsRecord,
    Level,
    Building,
    ConflictScenario,
    SourceMetadata,
)
```

These models include field validators for ULPIN format, vertical-ID regex,
polygon closure, positive areas, and z-range consistency.
