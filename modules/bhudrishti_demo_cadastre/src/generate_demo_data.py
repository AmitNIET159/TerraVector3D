"""Generate complete fictional demo data for BhuDrishti 3D.

Run:
    python -m src.generate_demo_data          # from project root
    python src/generate_demo_data.py          # alternative

Outputs seven JSON files into ``data/``.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    Building,
    ConflictScenario,
    Level,
    ParcelFeature,
    ParcelGeoJSON,
    ParcelProperties,
    PolygonGeometry,
    RightsRecord,
    SourceMetadata,
    SpatialUnit,
)

# ── Constants ────────────────────────────────────────────────────────────
PARENT_ULPIN = "7A4B9C2D8E1F6G"
BUILDING_ID = "BLD-GHA-001"
PARCEL_ID = "PRC-DW-001"
BUILDING_NAME = "Green Heights Apartment"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# ── Geometry helpers ─────────────────────────────────────────────────────

def _closed(coords: list[list[float]]) -> list[list[float]]:
    """Return a closed ring (first == last)."""
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    return coords


def _poly(coords: list[list[float]]) -> PolygonGeometry:
    """Wrap a 2-D ring into a PolygonGeometry."""
    return PolygonGeometry(coordinates=[_closed(coords)])


def _shoelace(ring: list[list[float]]) -> float:
    """Compute area of a simple polygon via the shoelace formula."""
    n = len(ring)
    area = 0.0
    for i in range(n - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def _vertical_id(level_code: str, unit_code: str, rev: int = 1) -> str:
    """Build a vertical ID string."""
    return f"{PARENT_ULPIN}-F{level_code}-U{unit_code}-R{rev:02d}"


# ── Parcel ───────────────────────────────────────────────────────────────

def _generate_parcel() -> ParcelGeoJSON:
    ring = [[0, 0], [40, 0], [40, 30], [0, 30]]
    area = _shoelace(_closed(ring))
    feature = ParcelFeature(
        properties=ParcelProperties(
            parent_ulpin=PARENT_ULPIN,
            parcel_id=PARCEL_ID,
            address="Plot 42, Demo Ward, Pune (Fictional)",
            total_area_sqm=round(area, 2),
        ),
        geometry=_poly(ring),
    )
    return ParcelGeoJSON(features=[feature])


# ── Building ─────────────────────────────────────────────────────────────

def _generate_building() -> Building:
    ring = [[5, 5], [35, 5], [35, 25], [5, 25]]
    return Building(
        building_id=BUILDING_ID,
        parcel_id=PARCEL_ID,
        parent_ulpin=PARENT_ULPIN,
        building_name=BUILDING_NAME,
        footprint=_poly(ring),
        total_height_m=19.0,
        num_levels=7,
        source_confidence_score=0.92,
        source_type="demo_floor_plan",
    )


# ── Levels ───────────────────────────────────────────────────────────────

LEVEL_DEFS: list[dict] = [
    {"level_code": "B1", "level_type": "basement",     "z_min_m": -3.0, "z_max_m":  0.0, "elevation_label": "Basement 1"},
    {"level_code": "G",  "level_type": "ground",       "z_min_m":  0.0, "z_max_m":  4.0, "elevation_label": "Ground Floor"},
    {"level_code": "01", "level_type": "residential",   "z_min_m":  4.0, "z_max_m":  7.0, "elevation_label": "Floor 1"},
    {"level_code": "02", "level_type": "residential",   "z_min_m":  7.0, "z_max_m": 10.0, "elevation_label": "Floor 2"},
    {"level_code": "03", "level_type": "residential",   "z_min_m": 10.0, "z_max_m": 13.0, "elevation_label": "Floor 3"},
    {"level_code": "04", "level_type": "residential",   "z_min_m": 13.0, "z_max_m": 16.0, "elevation_label": "Floor 4"},
    {"level_code": "05", "level_type": "residential",   "z_min_m": 16.0, "z_max_m": 19.0, "elevation_label": "Floor 5"},
]


def _generate_levels() -> list[Level]:
    return [Level(building_id=BUILDING_ID, **d) for d in LEVEL_DEFS]


# ── Spatial Units ────────────────────────────────────────────────────────

def _generate_spatial_units() -> list[SpatialUnit]:
    units: list[SpatialUnit] = []

    # -- Basement B1: 6 parking + 1 utility corridor --
    parking_w, parking_d = 5.0, 2.5
    for i in range(1, 7):
        x0 = 5.0 + (i - 1) * parking_w
        x1 = x0 + parking_w
        ring = [[x0, 5.0], [x1, 5.0], [x1, 7.5], [x0, 7.5]]
        code = f"P{i:02d}"
        units.append(SpatialUnit(
            unit_id=f"UNIT-B1-{code}",
            vertical_id=_vertical_id("B1", code),
            parent_ulpin=PARENT_ULPIN,
            building_id=BUILDING_ID,
            level_code="B1",
            unit_type="parking",
            footprint=_poly(ring),
            z_min_m=-3.0,
            z_max_m=0.0,
            area_sqm=round(_shoelace(_closed(ring)), 2),
            usage_type="covered_parking",
            status="registered",
            model_object_name=f"B1_parking_{code}",
        ))

    # Utility corridor along the far wall of B1
    util_ring = [[5, 22], [35, 22], [35, 25], [5, 25]]
    units.append(SpatialUnit(
        unit_id="UNIT-B1-UTIL01",
        vertical_id=_vertical_id("B1", "UTIL01"),
        parent_ulpin=PARENT_ULPIN,
        building_id=BUILDING_ID,
        level_code="B1",
        unit_type="utility_corridor",
        footprint=_poly(util_ring),
        z_min_m=-3.0,
        z_max_m=0.0,
        area_sqm=round(_shoelace(_closed(util_ring)), 2),
        usage_type="services_corridor",
        status="registered",
        model_object_name="B1_utility_UTIL01",
    ))

    # -- Ground floor: lobby / common area --
    lobby_ring = [[5, 5], [35, 5], [35, 25], [5, 25]]
    units.append(SpatialUnit(
        unit_id="UNIT-G-LOBBY01",
        vertical_id=_vertical_id("G", "LOBBY01"),
        parent_ulpin=PARENT_ULPIN,
        building_id=BUILDING_ID,
        level_code="G",
        unit_type="common_area",
        footprint=_poly(lobby_ring),
        z_min_m=0.0,
        z_max_m=4.0,
        area_sqm=round(_shoelace(_closed(lobby_ring)), 2),
        usage_type="lobby",
        status="registered",
        model_object_name="G_common_LOBBY01",
    ))

    # -- Residential floors F01–F05: 2 flats each --
    for floor_num in range(1, 6):
        lc = f"{floor_num:02d}"
        level_def = LEVEL_DEFS[floor_num + 1]  # index 2..6
        z_lo = level_def["z_min_m"]
        z_hi = level_def["z_max_m"]

        for side in (1, 2):
            flat_num = floor_num * 100 + side
            code = str(flat_num)

            if side == 1:
                # Left half  (normal: x ∈ [5, 20])
                if lc == "04":
                    # ── Intentional overlap: U401 extends 0.17 m past midline
                    x_right = 20.17
                else:
                    x_right = 20.0
                ring = [[5, 5], [x_right, 5], [x_right, 25], [5, 25]]
            else:
                # Right half (always starts at x = 20)
                ring = [[20, 5], [35, 5], [35, 25], [20, 25]]

            # Decide status — U302 is needs_review
            status = "needs_review" if (lc == "03" and side == 2) else "registered"

            units.append(SpatialUnit(
                unit_id=f"UNIT-F{lc}-{code}",
                vertical_id=_vertical_id(lc, code),
                parent_ulpin=PARENT_ULPIN,
                building_id=BUILDING_ID,
                level_code=lc,
                unit_type="apartment",
                footprint=_poly(ring),
                z_min_m=z_lo,
                z_max_m=z_hi,
                area_sqm=round(_shoelace(_closed(ring)), 2),
                usage_type="residential",
                status=status,
                model_object_name=f"F{lc}_apartment_{code}",
            ))

    return units


# ── Rights Records ───────────────────────────────────────────────────────

_MASKED_NAMES = [
    "R***H S***A",
    "P***A D***I",
    "S***T M***R",
    "A***L K***R",
    "N***A G***E",
    "V***Y P***L",
    "M***A J***I",
    "K***N B***T",
    "D***K R***E",
    "T***A C***N",
    "J***S W***R",
    "L***A F***Z",
]


def _generate_rights_records(units: list[SpatialUnit]) -> list[RightsRecord]:
    records: list[RightsRecord] = []
    seq = 1
    name_idx = 0

    for u in units:
        if u.unit_type == "apartment":
            # Every flat gets an ownership right
            records.append(RightsRecord(
                right_id=f"RIGHT-{seq:03d}",
                unit_id=u.unit_id,
                vertical_id=u.vertical_id,
                right_type="ownership",
                holder_name_masked=_MASKED_NAMES[name_idx % len(_MASKED_NAMES)],
                record_status="active" if u.status == "registered" else "under_review",
                document_reference=f"DOC/DEMO/{seq:04d}/2024",
                effective_date="2024-01-15",
            ))
            seq += 1
            name_idx += 1

        elif u.unit_type == "parking" and u.unit_id == "UNIT-B1-P03":
            # One parking unit gets a parking_right
            records.append(RightsRecord(
                right_id=f"RIGHT-{seq:03d}",
                unit_id=u.unit_id,
                vertical_id=u.vertical_id,
                right_type="parking_right",
                holder_name_masked=_MASKED_NAMES[name_idx % len(_MASKED_NAMES)],
                record_status="active",
                document_reference=f"DOC/DEMO/{seq:04d}/2024",
                effective_date="2024-03-01",
            ))
            seq += 1
            name_idx += 1

        elif u.unit_type == "utility_corridor":
            records.append(RightsRecord(
                right_id=f"RIGHT-{seq:03d}",
                unit_id=u.unit_id,
                vertical_id=u.vertical_id,
                right_type="utility_easement",
                holder_name_masked="PUNE M***L CORP",
                record_status="active",
                document_reference=f"DOC/DEMO/{seq:04d}/2024",
                effective_date="2023-06-01",
            ))
            seq += 1

    # Add a lease on flat 201 as extra variety
    flat_201 = next(u for u in units if u.unit_id == "UNIT-F02-201")
    records.append(RightsRecord(
        right_id=f"RIGHT-{seq:03d}",
        unit_id=flat_201.unit_id,
        vertical_id=flat_201.vertical_id,
        right_type="lease",
        holder_name_masked="B***A T***T",
        record_status="active",
        document_reference=f"DOC/DEMO/{seq:04d}/2024",
        effective_date="2024-06-01",
    ))

    return records


# ── Source Metadata ──────────────────────────────────────────────────────

def _generate_source_metadata() -> SourceMetadata:
    return SourceMetadata(
        source_id="SRC-DEMO-001",
        source_type="demo_floor_plan",
        description=(
            "Fictional floor-plan data generated programmatically for the "
            "BhuDrishti 3D SIH demonstration.  No real land records, property "
            "owners, or geographic locations are represented."
        ),
        confidence_score=0.92,
        coordinate_system="local_cartesian_metres",
        unit_of_measure="metres",
        generation_timestamp=datetime.now(timezone.utc).isoformat(),
        data_disclaimer=(
            "ALL DATA IS FICTIONAL.  This dataset was created solely for "
            "hackathon / demo purposes and must not be used for any legal, "
            "financial, or administrative decision-making."
        ),
    )


# ── Conflict Scenarios ──────────────────────────────────────────────────

def _generate_conflict_scenarios(units: list[SpatialUnit]) -> list[ConflictScenario]:
    u401 = next(u for u in units if u.unit_id == "UNIT-F04-401")
    u402 = next(u for u in units if u.unit_id == "UNIT-F04-402")
    u302 = next(u for u in units if u.unit_id == "UNIT-F03-302")
    util = next(u for u in units if u.unit_id == "UNIT-B1-UTIL01")

    return [
        ConflictScenario(
            conflict_id="CONFLICT-001",
            conflict_type="spatial_overlap",
            description=(
                "Units U401 and U402 on level F04 have overlapping footprints.  "
                "U401 extends 0.17 m past the partition midline, creating an "
                "overlap strip of approximately 3.4 sq.m."
            ),
            affected_unit_ids=[u401.unit_id, u402.unit_id],
            affected_vertical_ids=[u401.vertical_id, u402.vertical_id],
            overlap_area_sqm=3.4,
            severity="medium",
            recommended_action=(
                "Initiate re-survey of floor 4 partition wall and update "
                "cadastral records accordingly."
            ),
        ),
        ConflictScenario(
            conflict_id="CONFLICT-002",
            conflict_type="infrastructure_passthrough",
            description=(
                "An underground utility corridor (UTIL01) passes through "
                "basement level B1, crossing beneath the parking area.  "
                "Easement documentation must be verified."
            ),
            affected_unit_ids=[util.unit_id],
            affected_vertical_ids=[util.vertical_id],
            severity="low",
            recommended_action=(
                "Verify utility easement registration and cross-check with "
                "municipal services department records."
            ),
        ),
        ConflictScenario(
            conflict_id="CONFLICT-003",
            conflict_type="status_review",
            description=(
                "Unit U302 on level F03 is flagged as needs_review due to "
                "pending ownership documentation."
            ),
            affected_unit_ids=[u302.unit_id],
            affected_vertical_ids=[u302.vertical_id],
            severity="medium",
            recommended_action=(
                "Request updated ownership documents from the current holder "
                "and schedule a verification hearing."
            ),
        ),
    ]


# ── Main orchestrator ────────────────────────────────────────────────────

def generate_all(output_dir: Path | None = None) -> dict[str, object]:
    """Generate every demo data file and write them to *output_dir*.

    Returns a dict mapping filename → parsed model object for downstream
    validation.
    """
    out = output_dir or DATA_DIR
    out.mkdir(parents=True, exist_ok=True)

    parcel = _generate_parcel()
    building = _generate_building()
    levels = _generate_levels()
    units = _generate_spatial_units()
    rights = _generate_rights_records(units)
    source_meta = _generate_source_metadata()
    conflicts = _generate_conflict_scenarios(units)

    payloads: dict[str, object] = {
        "demo_parcel.geojson": parcel,
        "demo_building.json": building,
        "demo_levels.json": levels,
        "demo_spatial_units.json": units,
        "demo_rights_records.json": rights,
        "demo_source_metadata.json": source_meta,
        "demo_conflict_scenarios.json": conflicts,
    }

    for fname, obj in payloads.items():
        path = out / fname
        if isinstance(obj, list):
            data = [item.model_dump() for item in obj]
        else:
            data = obj.model_dump()
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  [OK] {path}")

    return payloads


# ── CLI entry point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating BhuDrishti 3D demo data ...")
    generate_all()
    print("Done.")
