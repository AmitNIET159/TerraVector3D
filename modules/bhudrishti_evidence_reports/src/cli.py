"""
CLI entry-point for BhuDrishti 3D evidence report generation.

Usage
-----
    python -m bhudrishti_evidence_reports.src.cli --input examples/sample_input.json --output output/

Or from the package root:

    python -m src.cli --input examples/sample_input.json --output output/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import ValidationInput
from .report_generator import generate_report


def main(argv: list[str] | None = None) -> None:
    """Parse CLI arguments and run the report pipeline."""
    parser = argparse.ArgumentParser(
        prog="bhudrishti_evidence_reports",
        description="Generate BhuDrishti 3D Vertical Property Validation Reports.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        type=Path,
        help="Path to the canonical JSON input file.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("output"),
        help="Output directory for generated reports (default: ./output).",
    )
    args = parser.parse_args(argv)

    input_path: Path = args.input
    output_dir: Path = args.output

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading input from: {input_path}")
    with open(input_path, "r", encoding="utf-8") as fh:
        raw_data = json.load(fh)

    # Validate
    try:
        input_data = ValidationInput(**raw_data)
    except Exception as exc:
        print(f"ERROR: Input validation failed:\n{exc}", file=sys.stderr)
        sys.exit(2)

    # Generate
    result = generate_report(input_data, output_dir)

    print("\nReport generation complete.")
    print(f"  HTML : {result['html_path']}")
    print(f"  PDF  : {result['pdf_path']}")
    print(f"  JSON : {result['manifest_path']}")


if __name__ == "__main__":
    main()

