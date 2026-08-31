"""Synthetic point-cloud generator for testing and demonstration.

Generates a realistic multi-floor building point cloud with floor slabs,
walls, and controlled noise.  Output is saved as a .PLY file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np

from .ply_io import write_ply


def generate_synthetic_pointcloud(
    output_path: str,
    num_floors: int = 5,
    include_basement: bool = True,
    floor_height_m: float = 3.0,
    building_footprint: Optional[list[list[float]]] = None,
    points_per_slab: int = 2500,
    noise_m: float = 0.02,
    random_seed: int = 42,
) -> str:
    """Generate a synthetic multi-floor building point cloud.

    Parameters
    ----------
    output_path : str
        Destination path for the .PLY file.
    num_floors : int
        Number of above-ground floors (excluding basement and ground).
    include_basement : bool
        Whether to include a B1 basement level below z=0.
    floor_height_m : float
        Height of each storey in metres.
    building_footprint : list or None
        Rectangle as [[x_min, y_min], [x_max, y_max]].  Defaults to
        [[0, 0], [20, 15]].
    points_per_slab : int
        Number of points to generate per floor slab.
    noise_m : float
        Standard deviation of Gaussian noise added to each point.
    random_seed : int
        Seed for reproducible output.

    Returns
    -------
    str
        Absolute path to the saved .PLY file.
    """
    rng = np.random.default_rng(random_seed)

    if building_footprint is None:
        building_footprint = [[0.0, 0.0], [20.0, 15.0]]

    x_min, y_min = building_footprint[0]
    x_max, y_max = building_footprint[1]

    # --- compute slab elevations --------------------------------------------
    slab_elevations: list[float] = []
    if include_basement:
        slab_elevations.append(-floor_height_m)  # B1 slab
    slab_elevations.append(0.0)  # Ground slab
    for i in range(1, num_floors + 1):
        slab_elevations.append(i * floor_height_m)
    # top slab (roof)
    slab_elevations.append((num_floors + 1) * floor_height_m)

    all_points: list[np.ndarray] = []

    # --- floor slab points --------------------------------------------------
    for z in slab_elevations:
        xs = rng.uniform(x_min, x_max, points_per_slab)
        ys = rng.uniform(y_min, y_max, points_per_slab)
        zs = np.full(points_per_slab, z)
        slab = np.column_stack([xs, ys, zs])
        slab += rng.normal(0, noise_m, slab.shape)
        all_points.append(slab)

    # --- wall points --------------------------------------------------------
    wall_points_per_edge = points_per_slab // 4
    z_bottom = slab_elevations[0]
    z_top = slab_elevations[-1]

    edges = [
        (x_min, y_min, x_max, y_min),  # south
        (x_max, y_min, x_max, y_max),  # east
        (x_max, y_max, x_min, y_max),  # north
        (x_min, y_max, x_min, y_min),  # west
    ]
    for x0, y0, x1, y1 in edges:
        t = rng.uniform(0, 1, wall_points_per_edge)
        xs = x0 + t * (x1 - x0)
        ys = y0 + t * (y1 - y0)
        zs = rng.uniform(z_bottom, z_top, wall_points_per_edge)
        wall = np.column_stack([xs, ys, zs])
        wall += rng.normal(0, noise_m, wall.shape)
        all_points.append(wall)

    points = np.vstack(all_points)

    # --- save PLY -----------------------------------------------------------
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_ply(str(out), points)

    return str(out.resolve())


def get_expected_slab_elevations(
    num_floors: int = 5,
    include_basement: bool = True,
    floor_height_m: float = 3.0,
) -> list[float]:
    """Return the deterministic slab elevations for testing."""
    elevations: list[float] = []
    if include_basement:
        elevations.append(-floor_height_m)
    elevations.append(0.0)
    for i in range(1, num_floors + 1):
        elevations.append(i * floor_height_m)
    elevations.append((num_floors + 1) * floor_height_m)
    return elevations
