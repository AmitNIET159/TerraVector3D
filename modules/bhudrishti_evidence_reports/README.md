# BhuDrishti 3D — Evidence Reports Module

> **bhudrishti_evidence_reports** — Generate professional, evidence-based
> vertical-property validation reports from canonical JSON input.

---

## Overview

This standalone Python module produces polished **HTML** and **PDF** reports
suitable for:

- **SIH demo presentations**
- **Officer review** of 3-D cadastral data
- **Property-conflict explanation** with evidence-backed details

### Report Sections

| # | Section | Content |
|---|---------|---------|
| 1 | **Summary** | ULPIN, building, floors, units, conflicts, confidence |
| 2 | **Vertical-Unit Register** | Per-unit table with masked holder names |
| 3 | **Topology Conflicts** | Severity-coded cards with overlap metrics |
| 4 | **Evidence Sources** | File provenance with SHA-256 integrity hashes |
| 5 | **QR Verification** | Embedded QR with local verification payload |
| — | **Disclaimer** | Mandatory prototype advisory |

---

## Quick Start

### 1. Install dependencies

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Generate reports (CLI)

```bash
python -m src.cli --input examples/sample_input.json --output output/
```

### 3. Generate reports (Python)

```python
import json
from src import generate_report

with open("examples/sample_input.json") as f:
    data = json.load(f)

result = generate_report(data, output_dir="output")

print(result["html_path"])     # output/BhuDrishti3D_validation_report.html
print(result["pdf_path"])      # output/BhuDrishti3D_validation_report.pdf
print(result["manifest_path"]) # output/verification_manifest.json
```

---

## Project Structure

```
bhudrishti_evidence_reports/
├── src/
│   ├── __init__.py              # Public API exports
│   ├── models.py                # Pydantic data models
│   ├── report_generator.py      # Main orchestrator (HTML + PDF + manifest)
│   ├── audit_hash.py            # SHA-256 hashing utilities
│   ├── qr_verification.py       # QR code generation
│   ├── template_renderer.py     # Jinja2 rendering
│   └── cli.py                   # CLI entry-point
├── templates/
│   └── validation_report.html.j2
├── examples/
│   └── sample_input.json
├── output/                      # Generated report files
│   ├── BhuDrishti3D_validation_report.html
│   ├── BhuDrishti3D_validation_report.pdf
│   └── verification_manifest.json
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_audit_hash.py
│   ├── test_qr_verification.py
│   └── test_report_generator.py
├── README.md
├── INTEGRATION.md
└── requirements.txt
```

---

## Public API

| Function | Description |
|----------|-------------|
| `generate_report(input_data, output_dir)` | Full pipeline → HTML + PDF + manifest + console summary |
| `generate_html_report(input_data, output_path)` | HTML report only |
| `generate_pdf_report(input_data, output_path)` | PDF report only |
| `create_verification_manifest(input_data, ...)` | JSON verification manifest |
| `calculate_audit_hash(data)` | SHA-256 hash of any data |

All functions accept either a `ValidationInput` Pydantic model or a raw `dict`.

---

## Input Schema

The canonical input JSON must conform to the `ValidationInput` schema
(see `src/models.py`). Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `parent_ulpin` | `str` (14 chars) | Uppercase alphanumeric ULPIN |
| `parcel` | `ParcelData` | Land parcel metadata |
| `building` | `BuildingData` | Building-level data |
| `levels` | `list[Level]` | Floor/storey records |
| `spatial_units` | `list[SpatialUnit]` | 3-D spatial units with vertical IDs |
| `property_rights` | `list[PropertyRight]` | Rights linked to units |
| `topology_conflicts` | `list[TopologyConflict]` | Detected conflicts |
| `source_metadata` | `list[SourceMetadata]` | Evidence provenance |
| `confidence_scores` | `dict[str, float]` | Must include `"overall"` |
| `timestamp` | `str` | Generation timestamp |
| `generated_by` | `str` | Pipeline/system identifier |

### Vertical ID Format

```
<parent_ulpin>-F<level>-U<unit_code>-R<revision>
```

Examples:
- `7A4B9C2D8E1F6G-F04-U401-R01` — Floor 4, Unit 401
- `7A4B9C2D8E1F6G-FB1-UP24-R01` — Basement 1, Parking 24
- `7A4B9C2D8E1F6G-FB1-UUTIL01-R01` — Basement 1, Utility 01

### Geometry Coordinates

All coordinates use **local Cartesian metres** (never latitude/longitude).

---

## Running Tests

```bash
# From the project root:
pytest tests/ -v
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| Jinja2 | HTML template rendering |
| ReportLab | PDF generation |
| qrcode | QR code creation |
| Pillow | Image processing for QR |
| Pydantic | Input validation & models |
| pytest | Testing framework |

All packages are **free and open-source**. No paid APIs, cloud services,
or internet connectivity required.

---

## Disclaimer

> Prototype decision-support output. Final cadastral verification,
> ownership determination and legal record approval remain with the
> authorized land-record authority.

