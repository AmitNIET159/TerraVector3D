# INTEGRATION.md — FastAPI + Three.js Integration Guide

This document explains how to integrate the `bhudrishti_topology`
module into a FastAPI backend that serves validation results to a
future Three.js frontend.

---

## Architecture

```
┌─────────────┐     JSON POST      ┌───────────────────┐     import      ┌───────────────────────┐
│  Three.js   │ ──────────────────► │  FastAPI Server   │ ──────────────► │  bhudrishti_topology  │
│  Frontend   │ ◄────────────────── │  (REST API)       │ ◄────────────── │  (this module)        │
└─────────────┘  ValidationSummary  └───────────────────┘  ValidationSummary  └───────────────────────┘
```

The module is a **pure Python library** with no web framework
dependency. FastAPI is used only as the HTTP layer.

---

## Step 1: Install Dependencies

```bash
pip install fastapi uvicorn
pip install -r bhudrishti_topology/requirements.txt
```

---

## Step 2: FastAPI Endpoint

Create `server.py` at the project root:

```python
"""FastAPI server that wraps bhudrishti_topology."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from bhudrishti_topology.src import validate_building
from bhudrishti_topology.src.models import BuildingInput, ValidationSummary

app = FastAPI(
    title="BhuDrishti 3D Topology Validator",
    version="0.1.0",
)

# Allow the Three.js frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["POST"],
    allow_headers=["*"],
)


@app.post(
    "/api/v1/validate",
    response_model=ValidationSummary,
    summary="Validate a building and detect 3D conflicts",
)
async def validate(building_input: BuildingInput) -> ValidationSummary:
    """Accept a BuildingInput JSON body, run full topology validation,
    and return a ValidationSummary.

    The Three.js frontend can parse the response to highlight
    conflicting units in the 3D scene.
    """
    try:
        summary = validate_building(building_input)
        return summary
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
```

### Run the server

```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

### Swagger UI

Open `http://localhost:8000/docs` to interactively test the endpoint.

---

## Step 3: Example cURL Request

```bash
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Content-Type: application/json" \
  -d @bhudrishti_topology/examples/conflict_building_input.json
```

### Expected Response (abbreviated)

```json
{
  "building_id": "BLD-002",
  "parent_ulpin": "7A4B9C2D8E1F6G",
  "total_units": 9,
  "total_conflicts": 3,
  "conflicts_by_severity": { "high": 1, "low": 2 },
  "conflicts_by_type": {
    "VOLUME_OVERLAP": 1,
    "UTILITY_EASEMENT_REVIEW": 2
  },
  "is_valid": false,
  "conflicts": [
    {
      "conflict_id": "CONFLICT-A1B2C3D4",
      "conflict_type": "VOLUME_OVERLAP",
      "severity": "high",
      "affected_unit_ids": ["U401", "U402"],
      "affected_vertical_ids": [
        "7A4B9C2D8E1F6G-F04-U401-R01",
        "7A4B9C2D8E1F6G-F04-U402-R01"
      ],
      "horizontal_overlap_area_sqm": 3.4,
      "overlapping_z_min_m": 9.0,
      "overlapping_z_max_m": 12.0,
      "estimated_overlap_volume_cum": 10.2,
      "recommended_action": "Survey and adjust unit boundaries ...",
      "human_readable_explanation": "Units overlap horizontally ..."
    }
  ]
}
```

---

## Step 4: Three.js Frontend Integration

The Three.js frontend would:

1. **POST** the building JSON to `/api/v1/validate`.
2. **Parse** the `ValidationSummary` response.
3. **Highlight** conflicting units using `affected_unit_ids`:

```javascript
// Pseudocode for Three.js conflict visualization
async function validateAndHighlight(buildingData) {
  const response = await fetch('/api/v1/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildingData),
  });

  const summary = await response.json();

  for (const conflict of summary.conflicts) {
    for (const unit_id of conflict.affected_unit_ids) {
      const mesh = scene.getObjectByName(unit_id);
      if (!mesh) continue;

      // Color by severity
      const color = {
        high: 0xff0000,    // red
        medium: 0xffa500,  // orange
        low: 0xffff00,     // yellow
      }[conflict.severity];

      mesh.material.color.setHex(color);
      mesh.material.opacity = 0.6;
      mesh.material.transparent = true;
    }
  }

  return summary;
}
```

---

## Step 5: Additional Endpoints (Optional)

You can expose the individual public functions as separate endpoints:

```python
from bhudrishti_topology.src import (
    calculate_overlap_metrics,
    detect_volume_conflicts,
    validate_spatial_units,
)
from bhudrishti_topology.src.models import SpatialUnit
from typing import List


@app.post("/api/v1/validate-units")
async def validate_units_endpoint(
    building_input: BuildingInput,
) -> list:
    conflicts = validate_spatial_units(
        building_input.spatial_units, building_input
    )
    return [c.model_dump() for c in conflicts]


@app.post("/api/v1/detect-conflicts")
async def detect_conflicts_endpoint(
    units: List[SpatialUnit],
) -> list:
    conflicts = detect_volume_conflicts(units)
    return [c.model_dump() for c in conflicts]


@app.post("/api/v1/overlap-metrics")
async def overlap_metrics_endpoint(
    unit_a: SpatialUnit,
    unit_b: SpatialUnit,
) -> dict:
    return calculate_overlap_metrics(unit_a, unit_b)
```

---

## Notes

- All JSON uses **snake_case** field names.
- Geometry coordinates are in **local Cartesian metres**.
- The module is **stateless** — no database connection required.
- All data is **fictional**. No real land records are used.
- The `ValidationSummary` Pydantic model auto-generates the OpenAPI
  schema, so the Three.js developer gets full type documentation
  from the Swagger UI.
