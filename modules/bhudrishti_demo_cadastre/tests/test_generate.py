"""Tests for the data-generation pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.generate_demo_data import generate_all


class TestGenerateAll:
    """Verify that generate_all() produces consistent, well-formed data."""

    @pytest.fixture(autouse=True)
    def _gen(self, tmp_path: Path):
        self.out = tmp_path / "data"
        self.payloads = generate_all(self.out)

    # ── File existence ───────────────────────────────────────────
    EXPECTED_FILES = [
        "demo_parcel.geojson",
        "demo_building.json",
        "demo_levels.json",
        "demo_spatial_units.json",
        "demo_rights_records.json",
        "demo_source_metadata.json",
        "demo_conflict_scenarios.json",
    ]

    @pytest.mark.parametrize("fname", EXPECTED_FILES)
    def test_file_exists(self, fname: str):
        assert (self.out / fname).exists()

    @pytest.mark.parametrize("fname", EXPECTED_FILES)
    def test_file_is_valid_json(self, fname: str):
        data = json.loads((self.out / fname).read_text("utf-8"))
        assert data  # non-empty

    # ── Parcel ───────────────────────────────────────────────────
    def test_parcel_has_one_feature(self):
        data = json.loads(
            (self.out / "demo_parcel.geojson").read_text("utf-8")
        )
        assert len(data["features"]) == 1

    def test_parcel_ulpin(self):
        data = json.loads(
            (self.out / "demo_parcel.geojson").read_text("utf-8")
        )
        assert (
            data["features"][0]["properties"]["parent_ulpin"]
            == "7A4B9C2D8E1F6G"
        )

    def test_parcel_area_positive(self):
        data = json.loads(
            (self.out / "demo_parcel.geojson").read_text("utf-8")
        )
        assert data["features"][0]["properties"]["total_area_sqm"] > 0

    # ── Building ─────────────────────────────────────────────────
    def test_building_name(self):
        data = json.loads(
            (self.out / "demo_building.json").read_text("utf-8")
        )
        assert data["building_name"] == "Green Heights Apartment"

    def test_building_source_type(self):
        data = json.loads(
            (self.out / "demo_building.json").read_text("utf-8")
        )
        assert data["source_type"] == "demo_floor_plan"

    # ── Levels ───────────────────────────────────────────────────
    def test_seven_levels(self):
        data = json.loads(
            (self.out / "demo_levels.json").read_text("utf-8")
        )
        assert len(data) == 7

    def test_level_codes(self):
        data = json.loads(
            (self.out / "demo_levels.json").read_text("utf-8")
        )
        codes = {l["level_code"] for l in data}
        assert codes == {"B1", "G", "01", "02", "03", "04", "05"}

    def test_levels_z_ascending(self):
        data = json.loads(
            (self.out / "demo_levels.json").read_text("utf-8")
        )
        for lvl in data:
            assert lvl["z_max_m"] > lvl["z_min_m"]

    # ── Spatial units ────────────────────────────────────────────
    def test_unit_count(self):
        """10 flats + 6 parking + 1 utility corridor + 1 lobby = 18."""
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        assert len(data) == 18

    def test_ten_apartments(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        apts = [u for u in data if u["unit_type"] == "apartment"]
        assert len(apts) == 10

    def test_six_parking(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        pkg = [u for u in data if u["unit_type"] == "parking"]
        assert len(pkg) == 6

    def test_one_utility_corridor(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        util = [u for u in data if u["unit_type"] == "utility_corridor"]
        assert len(util) == 1

    def test_one_common_area(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        common = [u for u in data if u["unit_type"] == "common_area"]
        assert len(common) == 1

    def test_unique_unit_ids(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        ids = [u["unit_id"] for u in data]
        assert len(ids) == len(set(ids))

    def test_unique_vertical_ids(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        vids = [u["vertical_id"] for u in data]
        assert len(vids) == len(set(vids))

    def test_all_polygons_closed(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        for u in data:
            ring = u["footprint"]["coordinates"][0]
            assert ring[0] == ring[-1], f"Not closed: {u['unit_id']}"

    def test_all_areas_positive(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        for u in data:
            assert u["area_sqm"] > 0, f"Non-positive area: {u['unit_id']}"

    def test_all_z_ranges_valid(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        for u in data:
            assert u["z_max_m"] > u["z_min_m"], u["unit_id"]

    def test_vertical_id_format(self):
        import re

        pattern = re.compile(r"^[A-Z0-9]{14}-F[A-Z0-9]+-U[A-Z0-9]+-R\d{2}$")
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        for u in data:
            assert pattern.match(u["vertical_id"]), u["vertical_id"]

    def test_vertical_id_contains_parent_ulpin(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        for u in data:
            assert u["vertical_id"].startswith("7A4B9C2D8E1F6G-")

    # ── Deliberate overlap on F04 ────────────────────────────────
    def test_f04_overlap_exists(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        u401 = next(u for u in data if u["unit_id"] == "UNIT-F04-401")
        u402 = next(u for u in data if u["unit_id"] == "UNIT-F04-402")

        r1 = u401["footprint"]["coordinates"][0]
        r2 = u402["footprint"]["coordinates"][0]

        # Compute bounding-box overlap
        xs1, ys1 = [p[0] for p in r1], [p[1] for p in r1]
        xs2, ys2 = [p[0] for p in r2], [p[1] for p in r2]
        x_ov = max(0, min(max(xs1), max(xs2)) - max(min(xs1), min(xs2)))
        y_ov = max(0, min(max(ys1), max(ys2)) - max(min(ys1), min(ys2)))
        overlap = x_ov * y_ov

        assert 3.0 < overlap < 4.0, f"Expected ~3.4, got {overlap}"

    # ── needs_review unit ────────────────────────────────────────
    def test_needs_review_unit_exists(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        nr = [u for u in data if u["status"] == "needs_review"]
        assert len(nr) >= 1
        assert nr[0]["unit_id"] == "UNIT-F03-302"

    # ── Rights records ───────────────────────────────────────────
    def test_rights_unique_ids(self):
        data = json.loads(
            (self.out / "demo_rights_records.json").read_text("utf-8")
        )
        ids = [r["right_id"] for r in data]
        assert len(ids) == len(set(ids))

    def test_parking_right_exists(self):
        data = json.loads(
            (self.out / "demo_rights_records.json").read_text("utf-8")
        )
        pr = [r for r in data if r["right_type"] == "parking_right"]
        assert len(pr) >= 1

    def test_utility_easement_exists(self):
        data = json.loads(
            (self.out / "demo_rights_records.json").read_text("utf-8")
        )
        ue = [r for r in data if r["right_type"] == "utility_easement"]
        assert len(ue) >= 1

    def test_lease_exists(self):
        data = json.loads(
            (self.out / "demo_rights_records.json").read_text("utf-8")
        )
        leases = [r for r in data if r["right_type"] == "lease"]
        assert len(leases) >= 1

    # ── Source metadata ──────────────────────────────────────────
    def test_source_coordinate_system(self):
        data = json.loads(
            (self.out / "demo_source_metadata.json").read_text("utf-8")
        )
        assert data["coordinate_system"] == "local_cartesian_metres"

    def test_source_disclaimer_present(self):
        data = json.loads(
            (self.out / "demo_source_metadata.json").read_text("utf-8")
        )
        assert "FICTIONAL" in data["data_disclaimer"]

    # ── Conflict scenarios ───────────────────────────────────────
    def test_three_conflict_scenarios(self):
        data = json.loads(
            (self.out / "demo_conflict_scenarios.json").read_text("utf-8")
        )
        assert len(data) == 3

    def test_overlap_conflict_area(self):
        data = json.loads(
            (self.out / "demo_conflict_scenarios.json").read_text("utf-8")
        )
        overlap = next(
            c for c in data if c["conflict_type"] == "spatial_overlap"
        )
        assert overlap["overlap_area_sqm"] == pytest.approx(3.4, abs=0.5)

    # ── Model-object names present ───────────────────────────────
    def test_model_object_names_non_empty(self):
        data = json.loads(
            (self.out / "demo_spatial_units.json").read_text("utf-8")
        )
        for u in data:
            assert u["model_object_name"], u["unit_id"]
