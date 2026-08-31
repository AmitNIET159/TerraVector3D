"""Shared fixtures for BhuDrishti demo cadastre tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """Return the data/ directory, generating files first if missing."""
    d = Path(__file__).resolve().parent.parent / "data"
    if not (d / "demo_parcel.geojson").exists():
        from src.generate_demo_data import generate_all

        generate_all(d)
    return d


@pytest.fixture(scope="session")
def parcel_data(data_dir: Path) -> dict:
    return json.loads((data_dir / "demo_parcel.geojson").read_text("utf-8"))


@pytest.fixture(scope="session")
def building_data(data_dir: Path) -> dict:
    return json.loads((data_dir / "demo_building.json").read_text("utf-8"))


@pytest.fixture(scope="session")
def levels_data(data_dir: Path) -> list[dict]:
    return json.loads((data_dir / "demo_levels.json").read_text("utf-8"))


@pytest.fixture(scope="session")
def units_data(data_dir: Path) -> list[dict]:
    return json.loads((data_dir / "demo_spatial_units.json").read_text("utf-8"))


@pytest.fixture(scope="session")
def rights_data(data_dir: Path) -> list[dict]:
    return json.loads((data_dir / "demo_rights_records.json").read_text("utf-8"))


@pytest.fixture(scope="session")
def source_data(data_dir: Path) -> dict:
    return json.loads(
        (data_dir / "demo_source_metadata.json").read_text("utf-8")
    )


@pytest.fixture(scope="session")
def conflicts_data(data_dir: Path) -> list[dict]:
    return json.loads(
        (data_dir / "demo_conflict_scenarios.json").read_text("utf-8")
    )
