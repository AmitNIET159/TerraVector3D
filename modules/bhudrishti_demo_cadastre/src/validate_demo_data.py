"""Validate generated BhuDrishti 3D demo data.

Run:
    python -m src.validate_demo_data          # from project root
    python src/validate_demo_data.py          # alternative

Checks:
  1. All IDs are unique (except deliberate test scenarios).
  2. All polygon rings are closed.
  3. All areas are positive.
  4. z_max > z_min for every unit and level.
  5. Every unit belongs to a known level.
  6. Vertical-ID format is correct.
  7. Detects the intentional F04 overlap (~3.4 sq.m.).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .models import PARENT_ULPIN_RE, VERTICAL_ID_RE

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ── Geometry helpers ─────────────────────────────────────────────────────

def _ring_is_closed(ring: list[list[float]]) -> bool:
    return len(ring) >= 4 and ring[0] == ring[-1]


def _shoelace(ring: list[list[float]]) -> float:
    n = len(ring)
    area = 0.0
    for i in range(n - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _rect_bounds(ring: list[list[float]]) -> tuple[float, float, float, float]:
    """Return (x_min, y_min, x_max, y_max) of an axis-aligned ring."""
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def _rect_overlap_area(
    r1: tuple[float, float, float, float],
    r2: tuple[float, float, float, float],
) -> float:
    """Compute intersection area of two axis-aligned rectangles."""
    x_overlap = max(0, min(r1[2], r2[2]) - max(r1[0], r2[0]))
    y_overlap = max(0, min(r1[3], r2[3]) - max(r1[1], r2[1]))
    return x_overlap * y_overlap


# ── Validation results ──────────────────────────────────────────────────

class ValidationResult:
    """Accumulates validation errors and warnings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def add_info(self, msg: str) -> None:
        self.info.append(msg)

    def summary(self) -> str:
        lines = [
            f"Validation {'PASSED' if self.passed else 'FAILED'}",
            f"  Errors:   {len(self.errors)}",
            f"  Warnings: {len(self.warnings)}",
            f"  Info:     {len(self.info)}",
        ]
        for e in self.errors:
            lines.append(f"  [ERROR]   {e}")
        for w in self.warnings:
            lines.append(f"  [WARN]    {w}")
        for i in self.info:
            lines.append(f"  [INFO]    {i}")
        return "\n".join(lines)


# ── Core validators ─────────────────────────────────────────────────────

def _load_json(name: str, data_dir: Path) -> Any:
    path = data_dir / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_parcel(data: dict, result: ValidationResult) -> None:
    for feat in data.get("features", []):
        props = feat["properties"]
        ulpin = props["parent_ulpin"]
        if not PARENT_ULPIN_RE.match(ulpin):
            result.error(f"Parcel ULPIN invalid: {ulpin}")
        if props["total_area_sqm"] <= 0:
            result.error("Parcel area not positive")
        for ring in feat["geometry"]["coordinates"]:
            if not _ring_is_closed(ring):
                result.error("Parcel polygon ring not closed")


def validate_building(data: dict, result: ValidationResult) -> None:
    if not PARENT_ULPIN_RE.match(data["parent_ulpin"]):
        result.error(f"Building ULPIN invalid: {data['parent_ulpin']}")
    if data["total_height_m"] <= 0:
        result.error("Building height not positive")
    for ring in data["footprint"]["coordinates"]:
        if not _ring_is_closed(ring):
            result.error("Building footprint not closed")


def validate_levels(data: list[dict], result: ValidationResult) -> set[str]:
    codes: set[str] = set()
    for lvl in data:
        code = lvl["level_code"]
        if code in codes:
            result.error(f"Duplicate level_code: {code}")
        codes.add(code)
        if lvl["z_max_m"] <= lvl["z_min_m"]:
            result.error(f"Level {code}: z_max_m <= z_min_m")
    return codes


def validate_spatial_units(
    data: list[dict],
    known_levels: set[str],
    result: ValidationResult,
) -> None:
    unit_ids: set[str] = set()
    vertical_ids: set[str] = set()

    for u in data:
        uid = u["unit_id"]
        vid = u["vertical_id"]

        # Uniqueness
        if uid in unit_ids:
            result.error(f"Duplicate unit_id: {uid}")
        unit_ids.add(uid)

        if vid in vertical_ids:
            result.error(f"Duplicate vertical_id: {vid}")
        vertical_ids.add(vid)

        # ULPIN
        if not PARENT_ULPIN_RE.match(u["parent_ulpin"]):
            result.error(f"Unit {uid}: invalid parent_ulpin")

        # Vertical-ID format
        if not VERTICAL_ID_RE.match(vid):
            result.error(f"Unit {uid}: invalid vertical_id format: {vid}")

        # Polygon closed
        for ring in u["footprint"]["coordinates"]:
            if not _ring_is_closed(ring):
                result.error(f"Unit {uid}: polygon not closed")

        # Positive area
        if u["area_sqm"] <= 0:
            result.error(f"Unit {uid}: area not positive")

        # z range
        if u["z_max_m"] <= u["z_min_m"]:
            result.error(f"Unit {uid}: z_max_m <= z_min_m")

        # Level membership
        if u["level_code"] not in known_levels:
            result.error(f"Unit {uid}: unknown level_code '{u['level_code']}'")

    # ── Overlap detection (axis-aligned rectangles) ─────────────
    # Group units by level
    by_level: dict[str, list[dict]] = {}
    for u in data:
        by_level.setdefault(u["level_code"], []).append(u)

    for lc, group in by_level.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                r1 = _rect_bounds(group[i]["footprint"]["coordinates"][0])
                r2 = _rect_bounds(group[j]["footprint"]["coordinates"][0])
                ov = _rect_overlap_area(r1, r2)
                if ov > 0.01:  # threshold 0.01 sq.m
                    result.warn(
                        f"Overlap on level {lc}: {group[i]['unit_id']} & "
                        f"{group[j]['unit_id']} ~ {ov:.2f} sq.m"
                    )


def validate_rights_records(
    data: list[dict],
    known_unit_ids: set[str],
    result: ValidationResult,
) -> None:
    right_ids: set[str] = set()
    for r in data:
        rid = r["right_id"]
        if rid in right_ids:
            result.error(f"Duplicate right_id: {rid}")
        right_ids.add(rid)
        if r["unit_id"] not in known_unit_ids:
            result.error(f"Right {rid}: unknown unit_id '{r['unit_id']}'")


def validate_source_metadata(data: dict, result: ValidationResult) -> None:
    if data.get("coordinate_system") != "local_cartesian_metres":
        result.warn("Unexpected coordinate_system")
    if not (0.0 <= data.get("confidence_score", -1) <= 1.0):
        result.error("confidence_score out of [0, 1]")


def validate_conflict_scenarios(
    data: list[dict],
    known_unit_ids: set[str],
    result: ValidationResult,
) -> None:
    for c in data:
        for uid in c.get("affected_unit_ids", []):
            if uid not in known_unit_ids:
                result.error(
                    f"Conflict {c['conflict_id']}: unknown unit_id {uid}"
                )


# ── Public API ───────────────────────────────────────────────────────────

def validate_all(data_dir: Path | None = None) -> ValidationResult:
    """Run every validation check and return a :class:`ValidationResult`."""
    d = data_dir or DATA_DIR
    result = ValidationResult()

    parcel = _load_json("demo_parcel.geojson", d)
    building = _load_json("demo_building.json", d)
    levels = _load_json("demo_levels.json", d)
    units = _load_json("demo_spatial_units.json", d)
    rights = _load_json("demo_rights_records.json", d)
    source = _load_json("demo_source_metadata.json", d)
    conflicts = _load_json("demo_conflict_scenarios.json", d)

    validate_parcel(parcel, result)
    validate_building(building, result)
    known_levels = validate_levels(levels, result)
    validate_spatial_units(units, known_levels, result)

    known_unit_ids = {u["unit_id"] for u in units}
    validate_rights_records(rights, known_unit_ids, result)
    validate_source_metadata(source, result)
    validate_conflict_scenarios(conflicts, known_unit_ids, result)

    # ── Expected info items ──────────────────────────────────────
    needs_review = [u for u in units if u["status"] == "needs_review"]
    if needs_review:
        result.add_info(
            f"{len(needs_review)} unit(s) flagged as needs_review: "
            + ", ".join(u["unit_id"] for u in needs_review)
        )

    parking_rights = [r for r in rights if r["right_type"] == "parking_right"]
    if parking_rights:
        result.add_info(
            f"{len(parking_rights)} parking_right record(s) found"
        )

    utility_easements = [
        r for r in rights if r["right_type"] == "utility_easement"
    ]
    if utility_easements:
        result.add_info(
            f"{len(utility_easements)} utility_easement record(s) found"
        )

    return result


# ── CLI entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    res = validate_all()
    print(res.summary())
    sys.exit(0 if res.passed else 1)
