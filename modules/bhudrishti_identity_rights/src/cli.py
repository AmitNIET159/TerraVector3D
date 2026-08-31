#!/usr/bin/env python3
"""
CLI for bhudrishti_identity_rights.

Usage (run from the ``bhudrishti_identity_rights/`` directory)::

    python -m src.cli generate --parent_ulpin 7A4B9C2D8E1F6G --level 04 --unit_code 401
    python -m src.cli validate --id "7A4B9C2D8E1F6G-F04-U401-R01"
    python -m src.cli validate-rights --input examples/sample_input.json
    python -m src.cli demo
"""

from __future__ import annotations

import argparse
import json
import sys

from .vertical_id_engine import (
    build_human_readable_label,
    generate_vertical_id,
    increment_revision,
    parse_vertical_id,
    validate_vertical_id,
)
from .rights_engine import (
    build_property_identity_summary,
    validate_rights_record,
)


def _cmd_generate(args: argparse.Namespace) -> None:
    """Generate a vertical ID."""
    vid = generate_vertical_id(
        parent_ulpin=args.parent_ulpin,
        level=args.level,
        unit_code=args.unit_code,
        revision=args.revision,
    )
    label = build_human_readable_label(vid)
    print(json.dumps({
        "vertical_id": vid,
        "human_readable_label": label,
    }, indent=2))


def _cmd_validate(args: argparse.Namespace) -> None:
    """Validate a vertical ID string."""
    result = validate_vertical_id(args.id)
    print(json.dumps(result.model_dump(), indent=2))


def _cmd_validate_rights(args: argparse.Namespace) -> None:
    """Validate rights records from a JSON file."""
    with open(args.input, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    records = data.get("rights_records", [])
    results = []
    for record in records:
        result = validate_rights_record(record)
        results.append({
            "record": record,
            "result": result.model_dump(),
        })
    print(json.dumps(results, indent=2, default=str))


def _cmd_demo(_args: argparse.Namespace) -> None:
    """Run a quick demonstration with fictional data."""
    print("=" * 60)
    print("  BhuDrishti Identity & Rights — Demo")
    print("  (Prototype extension — NOT an official ULPIN format)")
    print("=" * 60)

    ulpin = "7A4B9C2D8E1F6G"

    # --- Generate IDs ---
    ids = [
        ("04", "401", 1),
        ("B1", "PARK24", 1),
        ("G", "SHOP01", 2),
        ("B1", "UTIL01", 1),
    ]
    print("\n--- Generated Vertical IDs ---")
    generated = []
    for level, unit, rev in ids:
        vid = generate_vertical_id(ulpin, level, unit, rev)
        label = build_human_readable_label(vid)
        generated.append(vid)
        print(f"  {vid}  →  {label}")

    # --- Validate ---
    print("\n--- Validation ---")
    good = generated[0]
    bad = "INVALID-ID-STRING"
    for test_id in [good, bad]:
        result = validate_vertical_id(test_id)
        status = "✓ VALID" if result.is_valid else "✗ INVALID"
        print(f"  {test_id}  →  {status}")
        for err in result.errors:
            print(f"      error: {err}")

    # --- Increment revision ---
    print("\n--- Increment Revision ---")
    old = generated[0]
    new = increment_revision(old)
    print(f"  {old}  →  {new}")

    # --- Rights validation ---
    print("\n--- Rights Validation ---")
    records = [
        {
            "vertical_id": generated[0],
            "right_type": "ownership",
            "holder_name_masked": "R***A",
            "start_date": "2025-01-15",
            "notes": "Fictional ownership record",
        },
        {
            "vertical_id": generated[1],
            "right_type": "parking_right",
            "holder_name_masked": "S***H",
            "start_date": "2025-03-01",
            "notes": "Basement parking slot",
        },
        {
            "vertical_id": generated[0],
            "right_type": "parking_right",
            "holder_name_masked": "A***N",
            "start_date": "2025-01-15",
            "notes": "Invalid — apartment unit with parking_right",
        },
        {
            "vertical_id": generated[3],
            "right_type": "utility_easement",
            "holder_name_masked": "M***L",
            "start_date": "2025-06-01",
            "notes": "Utility corridor easement",
        },
    ]

    for rec in records:
        result = validate_rights_record(rec)
        print(f"\n  Right: {rec['right_type']} on {rec['vertical_id']}")
        print(f"  Status: {result.status.value}")
        for line in result.audit_explanation:
            print(f"    {line}")

    # --- Property summary ---
    print("\n--- Property Identity Summary ---")
    summary = build_property_identity_summary(
        generated[0],
        [records[0]],
    )
    print(json.dumps(summary.model_dump(), indent=2, default=str))

    print("\n" + "=" * 60)
    print("  Demo complete.")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bhudrishti_identity_rights",
        description=(
            "CLI for BhuDrishti vertical-property-ID and rights "
            "validation (prototype extension)."
        ),
    )
    sub = parser.add_subparsers(dest="command")

    # generate
    gen = sub.add_parser("generate", help="Generate a vertical ID")
    gen.add_argument("--parent_ulpin", required=True)
    gen.add_argument("--level", required=True)
    gen.add_argument("--unit_code", required=True)
    gen.add_argument("--revision", type=int, default=1)

    # validate
    val = sub.add_parser("validate", help="Validate a vertical ID")
    val.add_argument("--id", required=True)

    # validate-rights
    vr = sub.add_parser(
        "validate-rights",
        help="Validate rights records from a JSON file",
    )
    vr.add_argument("--input", required=True, help="Path to JSON file")

    # demo
    sub.add_parser("demo", help="Run a quick demo with fictional data")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    dispatch = {
        "generate": _cmd_generate,
        "validate": _cmd_validate,
        "validate-rights": _cmd_validate_rights,
        "demo": _cmd_demo,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
