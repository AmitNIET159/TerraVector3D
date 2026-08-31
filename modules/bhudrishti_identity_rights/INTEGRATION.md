# Integration Guide — bhudrishti_identity_rights

> **Prototype extension** — This module does **NOT** replace or
> constitute an officially approved ULPIN format.

This document shows how to integrate the `bhudrishti_identity_rights`
module into a larger BhuDrishti 3D application, including exact Python
imports and FastAPI-ready usage patterns.

---

## Module Placement

Place the module at:

```
BhuDrishti3D/
└── modules/
    └── bhudrishti_identity_rights/
        ├── src/
        ├── examples/
        ├── tests/
        ├── README.md
        ├── INTEGRATION.md
        └── requirements.txt
```

Add the module root to your Python path or install with
`pip install -e modules/bhudrishti_identity_rights`.

---

## Python Imports

```python
# --- From the src package directly ---

from src import (
    # Vertical-ID engine
    generate_vertical_id,
    parse_vertical_id,
    validate_vertical_id,
    increment_revision,
    build_human_readable_label,
    # Rights engine
    validate_unit_against_parent,
    validate_rights_record,
    build_property_identity_summary,
    # Models
    VerticalId,
    RightsRecord,
    ValidationResult,
    RightsValidationResult,
    PropertyIdentitySummary,
    RightType,
    ValidationStatus,
    # Exceptions
    VerticalIdError,
    VerticalIdValidationError,
    ParsingError,
    RightsValidationError,
)
```

---

## Canonical Rights-Record Structure

Every rights record must use the following JSON fields, compatible with
the BhuDrishti evidence-report module:

```json
{
    "vertical_id": "7A4B9C2D8E1F6G-F04-U401-R01",
    "right_type": "ownership",
    "holder_name_masked": "R***A",
    "start_date": "2025-01-15",
    "end_date": null,
    "notes": "Fictional ownership record"
}
```

> **Important:** The holder field is always `holder_name_masked`.
> Do **not** use `holder_masked`, `holder_name`, or any other variant.

---

## FastAPI-Ready Usage

Below are example FastAPI routes that wrap the module's public API.
These are ready to drop into your application — no modification needed
beyond adjusting import paths.

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date

# Adjust import path to match your project layout
from src import (
    generate_vertical_id,
    validate_vertical_id,
    parse_vertical_id,
    increment_revision,
    build_human_readable_label,
    validate_rights_record,
    build_property_identity_summary,
    validate_unit_against_parent,
    ParsingError,
    VerticalIdValidationError,
)

app = FastAPI(
    title="BhuDrishti Identity & Rights API",
    description="Prototype vertical-property-ID engine (NOT official ULPIN)",
    version="1.0.0",
)


# ------------------------------------------------------------------
# Request / response models
# ------------------------------------------------------------------

class GenerateRequest(BaseModel):
    parent_ulpin: str
    level: str
    unit_code: str
    revision: int = 1

class GenerateResponse(BaseModel):
    vertical_id: str
    human_readable_label: str

class ValidateResponse(BaseModel):
    is_valid: bool
    errors: list[str]
    warnings: list[str]

class RightsRecordRequest(BaseModel):
    vertical_id: str
    right_type: str
    holder_name_masked: str
    start_date: str
    end_date: Optional[str] = None
    notes: Optional[str] = None


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.post("/api/v1/vertical-id/generate", response_model=GenerateResponse)
def api_generate(req: GenerateRequest):
    """Generate a prototype vertical property ID."""
    try:
        vid = generate_vertical_id(
            parent_ulpin=req.parent_ulpin,
            level=req.level,
            unit_code=req.unit_code,
            revision=req.revision,
        )
        label = build_human_readable_label(vid)
        return GenerateResponse(
            vertical_id=vid,
            human_readable_label=label,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/api/v1/vertical-id/validate")
def api_validate(id: str):
    """Validate a vertical ID string."""
    result = validate_vertical_id(id)
    return result.model_dump()


@app.post("/api/v1/vertical-id/increment-revision")
def api_increment(id: str):
    """Increment the revision of a vertical ID."""
    try:
        new_id = increment_revision(id)
        label = build_human_readable_label(new_id)
        return {"vertical_id": new_id, "human_readable_label": label}
    except VerticalIdValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ParsingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/v1/rights/validate")
def api_validate_rights(req: RightsRecordRequest):
    """Validate a rights record against all rules."""
    record = req.model_dump()
    result = validate_rights_record(record)
    return result.model_dump()


@app.post("/api/v1/property/summary")
def api_property_summary(vertical_id: str, records: list[RightsRecordRequest]):
    """Build a full property-identity summary."""
    try:
        record_dicts = [r.model_dump() for r in records]
        summary = build_property_identity_summary(vertical_id, record_dicts)
        return summary.model_dump()
    except ParsingError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/api/v1/vertical-id/check-parent")
def api_check_parent(vertical_id: str, parent_ulpin: str):
    """Verify that a vertical ID belongs to the given parent ULPIN."""
    result = validate_unit_against_parent(vertical_id, parent_ulpin)
    return result.model_dump()
```

---

## Example Usage Flow

```python
# 1. Generate a vertical ID
vid = generate_vertical_id("7A4B9C2D8E1F6G", "04", "401", 1)
# → "7A4B9C2D8E1F6G-F04-U401-R01"

# 2. Validate it
result = validate_vertical_id(vid)
assert result.is_valid

# 3. Parse components
parsed = parse_vertical_id(vid)
assert parsed.parent_ulpin == "7A4B9C2D8E1F6G"
assert parsed.level == "04"
assert parsed.unit_code == "401"
assert parsed.revision == 1

# 4. Check against parent
check = validate_unit_against_parent(vid, "7A4B9C2D8E1F6G")
assert check.is_valid

# 5. Create and validate a rights record
record = {
    "vertical_id": vid,
    "right_type": "ownership",
    "holder_name_masked": "R***A",
    "start_date": "2025-01-15",
    "end_date": None,
    "notes": "Fictional ownership record",
}
rights_result = validate_rights_record(record)
assert rights_result.status.value == "valid"

# 6. Build a full summary
summary = build_property_identity_summary(vid, [record])
assert summary.overall_status.value == "valid"
assert summary.human_readable_label == "Floor 4, Unit 401, Revision 01"

# 7. Increment revision for amendments
new_vid = increment_revision(vid)
# → "7A4B9C2D8E1F6G-F04-U401-R02"
```

---

## Cross-Module Compatibility

The `RightsRecord` model serialises to JSON with these exact keys:

```json
{
    "vertical_id": "...",
    "right_type": "...",
    "holder_name_masked": "...",
    "start_date": "...",
    "end_date": "...",
    "notes": "..."
}
```

This structure is directly consumable by the BhuDrishti evidence-report
module without field renaming or adaptation.

---

## Running Tests

```bash
cd bhudrishti_identity_rights
pip install -r requirements.txt
pytest tests/ -v
```

All tests validate that `holder_name_masked` is the only accepted holder
field and that `holder_masked` is rejected.
