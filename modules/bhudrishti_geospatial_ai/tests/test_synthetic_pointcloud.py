"""Tests for synthetic point-cloud generator."""

import numpy as np
import pytest
from pathlib import Path

from src.synthetic_pointcloud_generator import (
    generate_synthetic_pointcloud,
    get_expected_slab_elevations,
)
from src.ply_io import read_ply


class TestSyntheticPointcloud:
    def test_ply_file_created(self, tmp_path):
        ply = tmp_path / "building.ply"
        result = generate_synthetic_pointcloud(str(ply))
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    def test_ply_readable(self, tmp_path):
        ply = tmp_path / "building.ply"
        generate_synthetic_pointcloud(str(ply))
        points = read_ply(str(ply))
        assert len(points) > 0

    def test_deterministic_output(self, tmp_path):
        ply1 = tmp_path / "b1.ply"
        ply2 = tmp_path / "b2.ply"
        generate_synthetic_pointcloud(str(ply1), random_seed=123)
        generate_synthetic_pointcloud(str(ply2), random_seed=123)
        p1 = read_ply(str(ply1))
        p2 = read_ply(str(ply2))
        assert p1.shape == p2.shape
        np.testing.assert_array_almost_equal(p1, p2)

    def test_point_count_reasonable(self, tmp_path):
        ply = tmp_path / "building.ply"
        generate_synthetic_pointcloud(str(ply), points_per_slab=2500)
        points = read_ply(str(ply))
        assert len(points) > 20000

    def test_basement_below_zero(self, tmp_path):
        ply = tmp_path / "building.ply"
        generate_synthetic_pointcloud(str(ply), include_basement=True)
        points = read_ply(str(ply))
        z = points[:, 2]
        assert np.any(z < 0), "Expected some points below z=0 when basement is included"

    def test_no_basement(self, tmp_path):
        ply = tmp_path / "building.ply"
        generate_synthetic_pointcloud(str(ply), include_basement=False, noise_m=0.02)
        points = read_ply(str(ply))
        z = points[:, 2]
        # Allow small noise below zero
        assert np.all(z >= -0.2), "Without basement, no points should be far below z=0"

    def test_expected_slab_elevations(self):
        elev = get_expected_slab_elevations(
            num_floors=5, include_basement=True, floor_height_m=3.0,
        )
        assert elev[0] == -3.0  # B1
        assert elev[1] == 0.0   # G
        assert elev[-1] == 18.0  # roof
        assert len(elev) == 8   # B1, G, F1-F5, roof
