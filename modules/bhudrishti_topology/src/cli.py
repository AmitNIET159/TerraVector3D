"""CLI entry‑point for the BhuDrishti 3D topology validator.

Usage::

    python -m bhudrishti_topology.src.cli examples/conflict_building_input.json

Or via the installed console script (if packaged)::

    bhudrishti-topology validate examples/conflict_building_input.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import BuildingInput
from .topology_validator import validate_building


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="bhudrishti-topology",
        description="BhuDrishti 3D topology validator — "
        "validate vertical‑property geometry and detect 3D "
        "ownership / property conflicts.",
    )
    sub = parser.add_subparsers(dest="command")

    validate_parser = sub.add_parser(
        "validate",
        help="Validate a building JSON file.",
    )
    validate_parser.add_argument(
        "input_file",
        type=Path,
        help="Path to a BuildingInput JSON file.",
    )
    validate_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write the validation summary JSON to this file "
        "(default: stdout).",
    )
    validate_parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty‑print the JSON output (default: True).",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry‑point called by ``python -m …`` or the console script."""
    args = _parse_args(argv)

    if args.command is None:
        _parse_args(["--help"])
        return 1

    if args.command == "validate":
        return _cmd_validate(args)

    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    input_path: Path = args.input_file
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return 1

    raw = json.loads(input_path.read_text(encoding="utf-8"))
    building = BuildingInput(**raw)
    summary = validate_building(building)

    indent = 2 if args.pretty else None
    output_json = summary.model_dump_json(indent=indent)

    if args.output:
        args.output.write_text(output_json, encoding="utf-8")
        print(f"Validation summary written to {args.output}")
    else:
        # Ensure UTF-8 output on Windows consoles
        import io

        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        print(output_json)

    # Exit code: 0 if valid, 1 if conflicts found
    return 0 if summary.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
