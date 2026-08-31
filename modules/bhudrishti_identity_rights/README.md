# bhudrishti_identity_rights

> **Prototype extension** — This module does **NOT** replace or constitute
> an officially approved ULPIN format.

Standalone Python module for creating, parsing, validating, revising, and
explaining proposed vertical property IDs for **BhuDrishti 3D**, while
preserving the official parent ULPIN unchanged.

---

## Vertical-ID Format

```
<parent_ulpin>-F<level>-U<unit_code>-R<revision>
```

| Component      | Rules                                          | Examples            |
|----------------|------------------------------------------------|---------------------|
| parent_ulpin   | Exactly 14 uppercase alphanumeric characters   | `7A4B9C2D8E1F6G`   |
| level          | `G`, `B1`–`B9`, or `01`–`99`                  | `04`, `B1`, `G`     |
| unit_code      | 1–16 uppercase alphanumeric characters          | `401`, `PARK24`     |
| revision       | `R01`–`R99`                                    | `R01`, `R02`        |

**Valid examples:**

```
7A4B9C2D8E1F6G-F04-U401-R01
7A4B9C2D8E1F6G-FB1-UPARK24-R01
7A4B9C2D8E1F6G-FG-USHOP01-R02
7A4B9C2D8E1F6G-FB1-UUTIL01-R01
```

---

## Rights Engine

Supported right types: `ownership`, `lease`, `parking_right`, `utility_easement`.

**Unit-code compatibility rules:**

| Right type         | Required unit_code pattern | Example ID                             |
|--------------------|----------------------------|----------------------------------------|
| `parking_right`    | Must contain `PARK`        | `7A4B9C2D8E1F6G-FB1-UPARK24-R01`      |
| `utility_easement` | Must contain `UTIL`        | `7A4B9C2D8E1F6G-FB1-UUTIL01-R01`      |
| `ownership`        | Any unit                   | `7A4B9C2D8E1F6G-F04-U401-R01`         |
| `lease`            | Any unit                   | `7A4B9C2D8E1F6G-FG-USHOP01-R02`       |

**Canonical rights-record fields** (cross-module compatible with BhuDrishti
evidence-report):

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

> **Note:** The holder field is always `holder_name_masked`.
> No other holder field name (`holder_masked`, `holder_name`, etc.) is used.

---

## Installation

```bash
cd bhudrishti_identity_rights
pip install -r requirements.txt
```

Requires **Python 3.11+**, **pydantic ≥ 2.0**.

---

## CLI Usage

Run from the `bhudrishti_identity_rights/` directory:

```bash
# Generate a vertical ID
python -m src.cli generate \
    --parent_ulpin 7A4B9C2D8E1F6G \
    --level 04 \
    --unit_code 401 \
    --revision 1

# Validate a vertical ID
python -m src.cli validate \
    --id "7A4B9C2D8E1F6G-F04-U401-R01"

# Validate rights records from a JSON file
python -m src.cli validate-rights \
    --input examples/sample_input.json

# Run interactive demo with fictional data
python -m src.cli demo
```

---

## Python API

```python
from src import (
    generate_vertical_id,
    parse_vertical_id,
    validate_vertical_id,
    increment_revision,
    build_human_readable_label,
    validate_unit_against_parent,
    validate_rights_record,
    build_property_identity_summary,
)

# Generate
vid = generate_vertical_id("7A4B9C2D8E1F6G", "04", "401", 1)
# "7A4B9C2D8E1F6G-F04-U401-R01"

# Parse
parsed = parse_vertical_id(vid)
# VerticalId(parent_ulpin="7A4B9C2D8E1F6G", level="04", ...)

# Validate
result = validate_vertical_id(vid)
# ValidationResult(is_valid=True, errors=[], warnings=[])

# Increment revision
new_vid = increment_revision(vid)
# "7A4B9C2D8E1F6G-F04-U401-R02"

# Human-readable label
label = build_human_readable_label(vid)
# "Floor 4, Unit 401, Revision 01"

# Validate rights
rights_result = validate_rights_record({
    "vertical_id": vid,
    "right_type": "ownership",
    "holder_name_masked": "R***A",
    "start_date": "2025-01-15",
})
# RightsValidationResult(status="valid", ...)
```

---

## Running Tests

```bash
cd bhudrishti_identity_rights
pytest tests/ -v
```

---

## Project Structure

```
bhudrishti_identity_rights/
├── src/
│   ├── __init__.py              # Public API re-exports
│   ├── __main__.py              # python -m entry point
│   ├── cli.py                   # CLI commands
│   ├── exceptions.py            # Custom exceptions
│   ├── models.py                # Pydantic v2 models
│   ├── vertical_id_engine.py    # ID generation/parsing/validation
│   └── rights_engine.py         # Rights validation engine
├── examples/
│   ├── sample_input.json        # Fictional input data
│   └── sample_output.json       # Expected output
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_vertical_id_engine.py
│   └── test_rights_engine.py
├── README.md
├── INTEGRATION.md
└── requirements.txt
```

---

## Disclaimer

All data used in this module is **fictional**.  This module uses no
database, web server, UI, cloud deployment, paid API, or real land
records.  Geometry coordinates (if ever extended) use local Cartesian
metres, never latitude/longitude.
