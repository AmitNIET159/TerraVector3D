# Integration Guide — bhudrishti_evidence_reports

> How to integrate this module into the **BhuDrishti3D** backend
> (future FastAPI service).

---

## Module Placement

```
BhuDrishti3D/
├── modules/
│   └── bhudrishti_evidence_reports/   ← place this module here
│       ├── src/
│       ├── templates/
│       ├── examples/
│       ├── tests/
│       ├── README.md
│       ├── INTEGRATION.md
│       └── requirements.txt
├── app/
│   ├── main.py                        ← FastAPI app
│   └── routers/
│       └── reports.py                 ← report endpoints
└── requirements.txt
```

---

## Python Imports

### Full Pipeline

```python
from modules.bhudrishti_evidence_reports.src import generate_report

result = generate_report(input_data_dict, output_dir="./reports")
# result["html_path"]     → path to HTML report
# result["pdf_path"]      → path to PDF report
# result["manifest_path"] → path to verification manifest
# result["manifest"]      → manifest dict (same report_id across all outputs)
```

### Individual Functions

```python
from modules.bhudrishti_evidence_reports.src import (
    generate_report,
    generate_html_report,
    generate_pdf_report,
    create_verification_manifest,
    calculate_audit_hash,
    ValidationInput,
)
```

### Audit Hash Only

```python
from modules.bhudrishti_evidence_reports.src.audit_hash import (
    calculate_audit_hash,
    calculate_file_hash,
)

data_hash = calculate_audit_hash({"key": "value"})
file_hash = calculate_file_hash("/path/to/file.ifc")
```

### QR Code Only

```python
from modules.bhudrishti_evidence_reports.src.qr_verification import (
    build_qr_payload,
    generate_qr_code_base64,
    generate_qr_code_bytes,
    save_qr_code,
)

payload = build_qr_payload(
    report_id="RPT-ABC123",
    parent_ulpin="7A4B9C2D8E1F6G",
    timestamp="2024-11-20T12:00:00+05:30",
    sha256_hash="a" * 64,
)
qr_b64 = generate_qr_code_base64(payload)
```

---

## FastAPI Integration Example

### `app/routers/reports.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pathlib import Path
import tempfile

from modules.bhudrishti_evidence_reports.src import (
    generate_report,
    generate_html_report,
    generate_pdf_report,
    create_verification_manifest,
    calculate_audit_hash,
    ValidationInput,
)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.post("/generate")
async def generate_full_report(input_data: ValidationInput):
    """Generate HTML + PDF + manifest from validated input.

    All outputs share the same report_id and input hash.
    """
    output_dir = Path(tempfile.mkdtemp(prefix="bhudrishti_report_"))
    result = generate_report(input_data, output_dir=output_dir)
    return JSONResponse(content={
        "report_id": result["manifest"]["report_id"],
        "html_path": result["html_path"],
        "pdf_path": result["pdf_path"],
        "manifest": result["manifest"],
    })


@router.post("/generate/html")
async def generate_html_only(input_data: ValidationInput):
    """Generate HTML report and return content."""
    html_content = generate_html_report(input_data)
    return HTMLResponse(content=html_content)


@router.post("/generate/pdf")
async def generate_pdf_only(input_data: ValidationInput):
    """Generate PDF report and return file."""
    output_dir = Path(tempfile.mkdtemp(prefix="bhudrishti_pdf_"))
    pdf_path = output_dir / "report.pdf"
    generate_pdf_report(input_data, pdf_path)
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="BhuDrishti3D_validation_report.pdf",
    )


@router.post("/manifest")
async def get_manifest(input_data: ValidationInput):
    """Generate verification manifest only."""
    manifest = create_verification_manifest(input_data)
    return JSONResponse(content=manifest)


@router.post("/hash")
async def compute_hash(input_data: ValidationInput):
    """Compute SHA-256 audit hash of the input data."""
    data_hash = calculate_audit_hash(input_data.model_dump(mode="json"))
    return JSONResponse(content={
        "parent_ulpin": input_data.parent_ulpin,
        "sha256_hash": data_hash,
    })
```

### `app/main.py`

```python
from fastapi import FastAPI
from app.routers import reports

app = FastAPI(
    title="BhuDrishti 3D API",
    version="0.9.1",
    description="3D Cadastral Validation Platform",
)

app.include_router(reports.router)
```

---

## Input Schema — Key Points

The `ValidationInput` Pydantic model handles all input validation automatically.
When used with FastAPI, invalid requests return `422 Unprocessable Entity`
with detailed error messages.

### Canonical Field Aliases

Fields accept both the Python attribute name and a canonical alias:

| Python Field | Canonical Alias | Model |
|---|---|---|
| `level_id` | `level_code` | `Level`, `SpatialUnit` |
| `validation_status` | `status` | `SpatialUnit` |
| `footprint_coordinates` | `footprint` | `BuildingData` |
| `boundary_coordinates` | `footprint` | `SpatialUnit` |
| `holder_name_masked` | *(preferred — no alias)* | `PropertyRight` |

### Holder Name Privacy

- `holder_name` is **optional**. If provided, it is auto-masked.
- `holder_name_masked` is the **preferred** input field.
- Reports **only display** `holder_name_masked`, never raw names.

### Example Property Right (canonical)

```json
{
  "right_id": "RGT-001",
  "vertical_id": "7A4B9C2D8E1F6G-FB1-UP24-R01",
  "rights_type": "ownership",
  "holder_name_masked": "Pr**a De*****h",
  "registration_date": "2023-04-15",
  "valid": true
}
```

### Validation Rules

| Field | Rule |
|-------|------|
| `parent_ulpin` | Exactly 14 uppercase alphanumeric characters |
| `spatial_units[].vertical_id` | Must match `<ULPIN>-F<level>-U<unit>-R<revision>` |
| `spatial_units[].vertical_id` | Must start with `parent_ulpin-` |
| `property_rights[].vertical_id` | Must reference an existing spatial unit |
| `topology_conflicts[].conflicting_vertical_ids` | Must reference existing spatial units |
| `topology_conflicts[].severity` | Must be `high`, `medium`, or `low` |
| `spatial_units[].validation_status` | Must be `valid`, `conflict`, or `pending` |
| `confidence_scores` | Must include `overall` key; all values 0.0–1.0 |
| `source_metadata[].sha256_hash` | Exactly 64 hexadecimal characters |
| `building.height_m` | Must be consistent with level z-ranges (10% tolerance) |

---

## Dependencies for FastAPI Backend

Add these to the backend `requirements.txt`:

```
# From bhudrishti_evidence_reports/requirements.txt
Jinja2>=3.1.0
reportlab>=4.0.0
qrcode>=7.4.0
Pillow>=10.0.0
pydantic>=2.0.0

# FastAPI backend
fastapi>=0.100.0
uvicorn>=0.23.0
python-multipart>=0.0.6
```

---

## Environment Notes

- **No internet required** — QR codes use local verification payloads.
- **No database required** — Input is pure JSON; output is file-based.
- **No paid APIs** — All dependencies are free and open-source.
- **No login/auth** — Authentication should be handled at the FastAPI layer.
- **Geometry** — All coordinates use local Cartesian metres (never lat/lon).
- **Fictional data** — Sample data is entirely fictional for prototyping.

---

## Running Module Tests from Backend Root

```bash
# From BhuDrishti3D/ root:
cd modules/bhudrishti_evidence_reports
pip install -r requirements.txt
pytest tests/ -v
```
