"""Service adapter for bhudrishti_geospatial_ai module."""
import json
import tempfile
from pathlib import Path
from typing import List
from app.services.module_adapter import ensure_module_path
ensure_module_path()

from modules.bhudrishti_geospatial_ai.src import normalize_geojson, detect_floor_levels

class GeospatialService:
    def normalize(self, geojson_data: dict) -> dict:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".geojson", delete=False) as tmp:
            json.dump(geojson_data, tmp)
            tmp_path = tmp.name
        try:
            return normalize_geojson(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def detect_floors(self, point_cloud_data: List[List[float]], merge_tolerance_m: float = 0.5) -> dict:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ply", delete=False) as tmp:
            num_points = len(point_cloud_data)
            tmp.write("ply\nformat ascii 1.0\nelement vertex {}\nproperty float x\nproperty float y\nproperty float z\nend_header\n".format(num_points))
            for pt in point_cloud_data:
                tmp.write(f"{pt[0]} {pt[1]} {pt[2]}\n")
            tmp_path = tmp.name
        try:
            return detect_floor_levels(tmp_path, merge_tolerance_m=merge_tolerance_m)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
