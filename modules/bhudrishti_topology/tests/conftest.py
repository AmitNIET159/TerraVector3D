"""Shared fixtures for bhudrishti_topology tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bhudrishti_topology.src.models import (
    BuildingInput,
    LevelInfo,
    SpatialUnit,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

# ---------------------------------------------------------------------------
# Helpers to build units quickly
# ---------------------------------------------------------------------------

_ULPIN = "7A4B9C2D8E1F6G"


def make_unit(
    unit_id: str = "U101",
    level_code: str = "01",
    unit_type: str = "apartment",
    footprint: list | None = None,
    z_min: float = 0.0,
    z_max: float = 3.0,
    area: float = 100.0,
    usage: str = "residential",
    status: str = "active",
    building_id: str = "BLD-TEST",
    vertical_id: str | None = None,
) -> SpatialUnit:
    if footprint is None:
        footprint = [
            [0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]
        ]
    if vertical_id is None:
        vertical_id = f"{_ULPIN}-F{level_code}-U{unit_id}-R01"
    return SpatialUnit(
        unit_id=unit_id,
        vertical_id=vertical_id,
        parent_ulpin=_ULPIN,
        building_id=building_id,
        level_code=level_code,
        unit_type=unit_type,
        footprint=footprint,
        z_min_m=z_min,
        z_max_m=z_max,
        area_sqm=area,
        usage_type=usage,
        status=status,
    )


def make_building(
    building_id: str = "BLD-TEST",
    units: list[SpatialUnit] | None = None,
    levels: list[LevelInfo] | None = None,
    total_height: float = 12.0,
    footprint: list | None = None,
) -> BuildingInput:
    if footprint is None:
        footprint = [
            [0.0, 0.0], [20.0, 0.0], [20.0, 10.0], [0.0, 10.0], [0.0, 0.0]
        ]
    if levels is None:
        levels = [
            LevelInfo(level_code="01", z_min_m=0.0, z_max_m=3.0),
            LevelInfo(level_code="02", z_min_m=3.0, z_max_m=6.0),
            LevelInfo(level_code="03", z_min_m=6.0, z_max_m=9.0),
            LevelInfo(level_code="04", z_min_m=9.0, z_max_m=12.0),
        ]
    if units is None:
        units = []
    return BuildingInput(
        building_id=building_id,
        parent_ulpin=_ULPIN,
        footprint=footprint,
        levels=levels,
        total_height_m=total_height,
        spatial_units=units,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ulpin() -> str:
    return _ULPIN


@pytest.fixture
def sample_unit() -> SpatialUnit:
    return make_unit()


@pytest.fixture
def sample_building() -> BuildingInput:
    return make_building(
        units=[
            make_unit("U101", "01"),
            make_unit(
                "U102", "01",
                footprint=[
                    [10.0, 0.0], [20.0, 0.0], [20.0, 10.0],
                    [10.0, 10.0], [10.0, 0.0],
                ],
            ),
        ]
    )


@pytest.fixture
def valid_building_json() -> dict:
    path = EXAMPLES_DIR / "valid_building_input.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def conflict_building_json() -> dict:
    path = EXAMPLES_DIR / "conflict_building_input.json"
    return json.loads(path.read_text(encoding="utf-8"))
