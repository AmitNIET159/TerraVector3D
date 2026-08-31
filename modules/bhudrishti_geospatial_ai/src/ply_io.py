"""PLY file I/O utilities — pure-numpy fallback when Open3D is unavailable.

Provides read/write for ASCII PLY point clouds using only numpy.
Prefers Open3D when installed for performance, but falls back gracefully.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

try:
    import open3d as o3d

    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False


def read_ply(path: str) -> np.ndarray:
    """Read a PLY file and return an (N, 3) float64 array of XYZ points."""
    if HAS_OPEN3D:
        pcd = o3d.io.read_point_cloud(str(path))
        return np.asarray(pcd.points)
    return _read_ply_ascii(path)


def write_ply(path: str, points: np.ndarray) -> None:
    """Write an (N, 3) array of XYZ points to an ASCII PLY file."""
    if HAS_OPEN3D:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        o3d.io.write_point_cloud(str(path), pcd, write_ascii=True)
        return
    _write_ply_ascii(path, points)


# ---------------------------------------------------------------------------
# Pure-numpy ASCII PLY reader / writer
# ---------------------------------------------------------------------------


def _read_ply_ascii(path: str) -> np.ndarray:
    """Parse an ASCII PLY file into (N, 3) float64 array."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"PLY file not found: {path}")

    with open(p, "r", encoding="utf-8", errors="replace") as fh:
        # --- header ---------------------------------------------------------
        line = fh.readline().strip()
        if line != "ply":
            raise ValueError(f"Not a PLY file (first line: '{line}')")

        vertex_count = 0
        in_header = True
        x_idx, y_idx, z_idx = 0, 1, 2
        prop_index = 0

        while in_header:
            line = fh.readline()
            if not line:
                raise ValueError("Unexpected end of file in PLY header")
            line = line.strip()
            if line.startswith("element vertex"):
                vertex_count = int(line.split()[-1])
            elif line.startswith("property"):
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[-1].lower()
                    if name == "x":
                        x_idx = prop_index
                    elif name == "y":
                        y_idx = prop_index
                    elif name == "z":
                        z_idx = prop_index
                prop_index += 1
            elif line == "end_header":
                in_header = False

        if vertex_count == 0:
            return np.empty((0, 3), dtype=np.float64)

        # --- data -----------------------------------------------------------
        points = np.empty((vertex_count, 3), dtype=np.float64)
        for i in range(vertex_count):
            parts = fh.readline().split()
            points[i, 0] = float(parts[x_idx])
            points[i, 1] = float(parts[y_idx])
            points[i, 2] = float(parts[z_idx])

    return points


def _write_ply_ascii(path: str, points: np.ndarray) -> None:
    """Write an ASCII PLY file from (N, 3) array."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    n = len(points)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("ply\n")
        fh.write("format ascii 1.0\n")
        fh.write(f"element vertex {n}\n")
        fh.write("property float x\n")
        fh.write("property float y\n")
        fh.write("property float z\n")
        fh.write("end_header\n")
        for row in points:
            fh.write(f"{row[0]:.6f} {row[1]:.6f} {row[2]:.6f}\n")
