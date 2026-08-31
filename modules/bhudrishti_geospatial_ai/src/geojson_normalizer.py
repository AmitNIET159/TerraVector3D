"""GeoJSON parcel/building normalisation.

Reads GeoJSON, validates geometry, translates to local-metre coordinates.
Input GeoJSON is used as a local prototype geometry source and is NOT
an official cadastral coordinate record.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shapely.geometry import mapping, shape, Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely import affinity

from .models import DEMO_PARENT_ULPIN, NormalizedParcelResult


def normalize_geojson(geojson_path: str) -> dict:
    """Normalise a GeoJSON parcel/building polygon.

    Parameters
    ----------
    geojson_path : str
        Path to a .geojson file containing Polygon or MultiPolygon geometry.

    Returns
    -------
    dict
        JSON-serialisable normalised parcel result.
    """
    path = Path(geojson_path)
    if not path.exists():
        raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")

    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)

    warnings: list[str] = []

    # --- extract features ---------------------------------------------------
    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    else:
        # bare geometry object
        features = [{"type": "Feature", "geometry": data, "properties": {}}]

    if not features:
        raise ValueError("GeoJSON contains no features.")

    # --- validate & collect polygons ----------------------------------------
    polygons: list[Polygon] = []

    for feat in features:
        geom_json = feat.get("geometry")
        if geom_json is None:
            warnings.append("Feature with null geometry skipped.")
            continue

        geom = shape(geom_json)

        if geom.is_empty:
            warnings.append("Empty geometry skipped.")
            continue

        if not geom.is_valid:
            geom = geom.buffer(0)
            if not geom.is_valid:
                warnings.append("Invalid geometry could not be repaired — skipped.")
                continue
            warnings.append("Invalid geometry repaired using buffer(0).")

        if isinstance(geom, Polygon):
            _validate_polygon(geom, warnings)
            geom = orient(geom, sign=1.0)  # CCW outer ring
            polygons.append(geom)
        elif isinstance(geom, MultiPolygon):
            for part in geom.geoms:
                _validate_polygon(part, warnings)
                part = orient(part, sign=1.0)
                polygons.append(part)
            warnings.append(
                f"MultiPolygon with {len(geom.geoms)} parts preserved."
            )
        else:
            warnings.append(f"Unsupported geometry type '{geom.geom_type}' skipped.")

    if not polygons:
        raise ValueError("No valid polygon geometries found in the input.")

    # --- combine & translate to local origin --------------------------------
    combined: Polygon | MultiPolygon
    if len(polygons) == 1:
        combined = polygons[0]
    else:
        combined = MultiPolygon(polygons)

    min_x, min_y, _, _ = combined.bounds
    translated = affinity.translate(combined, xoff=-min_x, yoff=-min_y)
    t_min_x, t_min_y, t_max_x, t_max_y = translated.bounds

    # --- extract footprint coords -------------------------------------------
    if isinstance(translated, Polygon):
        footprint = _polygon_coords(translated)
    else:
        footprint = [_polygon_coords(p) for p in translated.geoms]

    area_sqm = round(translated.area, 4)

    # --- confidence ----------------------------------------------------------
    confidence = 0.90
    confidence -= 0.03 * len(warnings)
    confidence = round(max(0.10, min(1.0, confidence)), 2)

    result = NormalizedParcelResult(
        parent_ulpin=DEMO_PARENT_ULPIN,
        footprint=footprint,
        area_sqm=area_sqm,
        bounding_box={
            "min_x": round(t_min_x, 4),
            "min_y": round(t_min_y, 4),
            "max_x": round(t_max_x, 4),
            "max_y": round(t_max_y, 4),
        },
        coordinate_reference="LOCAL_METERS",
        source_type="geojson_local_prototype",
        confidence_score=confidence,
        warnings=warnings,
        human_verification_required=True,
    )
    return result.model_dump()


def _polygon_coords(poly: Polygon) -> list[list[float]]:
    """Return exterior-ring coordinates as [[x, y], ...]."""
    return [[round(x, 4), round(y, 4)] for x, y in poly.exterior.coords]


def _validate_polygon(poly: Polygon, warnings: list[str]) -> None:
    """Run validation checks on a single Polygon, appending warnings."""
    coords = list(poly.exterior.coords)

    # closed ring
    if coords[0] != coords[-1]:
        warnings.append("Polygon ring was not closed; auto-closed by Shapely.")

    # minimum unique vertices
    unique = set(coords[:-1]) if len(coords) > 1 else set(coords)
    if len(unique) < 3:
        warnings.append("Polygon has fewer than 3 unique vertices.")

    # self-intersection
    if not poly.is_simple:
        warnings.append("Self-intersecting polygon detected.")

    # degenerate area
    if poly.area <= 0:
        warnings.append("Polygon has zero or negative area.")
