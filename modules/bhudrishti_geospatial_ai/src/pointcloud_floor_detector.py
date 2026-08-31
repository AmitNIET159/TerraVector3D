"""Point-cloud floor-level detection using histogram, RANSAC and DBSCAN.

Detects candidate horizontal slab elevations, merges near-duplicates,
validates spacing, compares methods, and proposes building levels
(B1, G, F01 ...).  The highest slab is classified as ROOF (not a
cadastral unit level) unless explicitly configured as terrace/air-rights.

A detected horizontal plane is a slab elevation, NOT automatically a
property floor.  All results require authorised human verification.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.signal import find_peaks
from sklearn.cluster import DBSCAN as DBSCAN_Clustering

from .models import (
    DEMO_PARENT_ULPIN,
    PointcloudFloorResult,
    SuggestedLevel,
)
from .ply_io import read_ply, HAS_OPEN3D

if HAS_OPEN3D:
    import open3d as o3d

_MERGE_TOLERANCE_M = 0.5
_MIN_SLAB_GAP_M = 1.5  # minimum credible floor height


def detect_floor_levels(
    ply_path: str,
    merge_tolerance_m: float = _MERGE_TOLERANCE_M,
    include_roof_as_terrace: bool = False,
) -> dict:
    """Detect floor levels from a .PLY point cloud.

    Parameters
    ----------
    ply_path : str
        Path to a .PLY point-cloud file.
    merge_tolerance_m : float
        Tolerance for merging near-duplicate slab elevations.
    include_roof_as_terrace : bool
        If *True*, include the roof slab as a cadastral terrace/air-rights
        level.  Default *False* marks it as non-cadastral.

    Returns
    -------
    dict
        JSON-serialisable floor-detection result.
    """
    path = Path(ply_path)
    if not path.exists():
        raise FileNotFoundError(f"PLY file not found: {ply_path}")

    points = read_ply(str(path))

    if len(points) < 10:
        return PointcloudFloorResult(
            parent_ulpin=DEMO_PARENT_ULPIN,
            coordinate_reference="LOCAL_METERS",
            warnings=["Insufficient points in point cloud (< 10)."],
            human_verification_required=True,
        ).model_dump()

    z_values = points[:, 2]
    methods_attempted: list[str] = ["histogram", "ransac", "dbscan"]
    methods_used: list[str] = []
    all_candidates: dict[str, list[float]] = {}

    # --- Method 1: Z-histogram + find_peaks ---------------------------------
    hist_slabs = _histogram_method(z_values)
    if hist_slabs:
        methods_used.append("histogram")
        all_candidates["histogram"] = hist_slabs

    # --- Method 2: RANSAC horizontal-plane detection ------------------------
    ransac_slabs = _ransac_method(points)
    if ransac_slabs:
        methods_used.append("ransac")
        all_candidates["ransac"] = ransac_slabs

    # --- Method 3: DBSCAN clustering ----------------------------------------
    dbscan_slabs = _dbscan_method(z_values)
    if dbscan_slabs:
        methods_used.append("dbscan")
        all_candidates["dbscan"] = dbscan_slabs

    # --- Method agreement ---------------------------------------------------
    methods_agreed, agreement_score = _compute_method_agreement(all_candidates)

    # --- Merge candidates ---------------------------------------------------
    merged = _merge_slab_candidates(all_candidates, tolerance=merge_tolerance_m)
    merged.sort()

    # --- Validate slab spacing (remove spurious thin gaps) ------------------
    merged = _validate_slab_spacing(merged, min_gap_m=_MIN_SLAB_GAP_M)

    # --- Estimated floor height ---------------------------------------------
    if len(merged) >= 2:
        diffs = np.diff(merged)
        estimated_floor_height = round(float(np.median(diffs)), 2)
    else:
        estimated_floor_height = 3.0

    # --- Warnings -----------------------------------------------------------
    warnings: list[str] = []

    if agreement_score < 0.8:
        warnings.append(
            "Floor-detection methods disagree; manual validation required."
        )

    if len(merged) >= 3:
        diffs = np.diff(merged)
        mean_d = float(np.mean(diffs))
        if mean_d > 0:
            cv = float(np.std(diffs)) / mean_d
            if cv > 0.25:
                warnings.append(
                    f"Inconsistent slab spacing (CV={cv:.2f}). "
                    "Floor heights may be non-uniform or detection is noisy."
                )

    if not methods_used:
        warnings.append("No detection method produced valid slab elevations.")

    # --- Identify roof slab -------------------------------------------------
    roof_slab_z: float | None = None
    if merged:
        roof_slab_z = round(merged[-1], 2)

    # --- Assign levels (roof separated) ------------------------------------
    suggested = _assign_levels(
        merged, z_values, estimated_floor_height, include_roof_as_terrace,
    )

    # --- Split cadastral vs all levels --------------------------------------
    cadastral = [lv for lv in suggested if lv.is_cadastral_unit_level]

    result = PointcloudFloorResult(
        parent_ulpin=DEMO_PARENT_ULPIN,
        coordinate_reference="LOCAL_METERS",
        method_used=methods_used,
        methods_attempted=methods_attempted,
        methods_agreed=methods_agreed,
        method_agreement_score=agreement_score,
        detected_slab_elevations_m=[round(s, 2) for s in merged],
        estimated_floor_height_m=estimated_floor_height,
        roof_slab_z_m=roof_slab_z,
        suggested_levels=suggested,
        suggested_cadastral_levels=cadastral,
        warnings=warnings,
        human_verification_required=True,
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _histogram_method(
    z_values: np.ndarray,
    bin_width: float = 0.2,
) -> list[float]:
    """Detect slab elevations via Z-density histogram + peak finding."""
    z_min, z_max = float(z_values.min()), float(z_values.max())
    n_bins = max(3, int((z_max - z_min) / bin_width) + 1)

    hist, bin_edges = np.histogram(z_values, bins=n_bins)
    centres = (bin_edges[:-1] + bin_edges[1:]) / 2.0

    height_thr = max(hist) * 0.08
    min_distance = max(1, int(2.0 / bin_width))
    peaks, _ = find_peaks(hist, height=height_thr, distance=min_distance)

    return sorted(float(centres[p]) for p in peaks)


def _ransac_method(
    points: np.ndarray,
    max_planes: int = 12,
    min_inliers: int = 50,
) -> list[float]:
    """Detect horizontal planes via iterative RANSAC.

    Uses Open3D when available, otherwise falls back to a simple
    numpy-based RANSAC for horizontal planes.
    """
    if HAS_OPEN3D:
        return _ransac_open3d(points, max_planes, min_inliers)
    return _ransac_numpy(points, max_planes, min_inliers)


def _ransac_open3d(
    points: np.ndarray,
    max_planes: int,
    min_inliers: int,
) -> list[float]:
    """RANSAC via Open3D's segment_plane."""
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    slabs: list[float] = []
    remaining = pcd

    for _ in range(max_planes):
        if len(remaining.points) < min_inliers:
            break
        try:
            plane_model, inliers = remaining.segment_plane(
                distance_threshold=0.15,
                ransac_n=3,
                num_iterations=1000,
            )
        except RuntimeError:
            break

        if len(inliers) < min_inliers:
            break

        a, b, c, d = plane_model
        normal = np.array([a, b, c])
        norm_len = np.linalg.norm(normal)
        if norm_len == 0:
            remaining = remaining.select_by_index(inliers, invert=True)
            continue
        normal /= norm_len

        if abs(normal[2]) > 0.85:  # nearly horizontal
            inlier_pts = np.asarray(remaining.points)[inliers]
            slab_z = float(np.median(inlier_pts[:, 2]))
            slabs.append(slab_z)

        remaining = remaining.select_by_index(inliers, invert=True)

    return sorted(slabs)


def _ransac_numpy(
    points: np.ndarray,
    max_planes: int,
    min_inliers: int,
    distance_threshold: float = 0.15,
    num_iterations: int = 1000,
) -> list[float]:
    """Simple numpy RANSAC for horizontal planes (z = constant)."""
    rng = np.random.default_rng(42)
    remaining = points.copy()
    slabs: list[float] = []

    for _ in range(max_planes):
        if len(remaining) < min_inliers:
            break

        best_z = None
        best_inliers = None
        best_count = 0

        for _ in range(num_iterations):
            idx = rng.integers(0, len(remaining))
            z_candidate = remaining[idx, 2]
            distances = np.abs(remaining[:, 2] - z_candidate)
            inlier_mask = distances < distance_threshold
            count = int(inlier_mask.sum())

            if count > best_count:
                best_count = count
                best_z = z_candidate
                best_inliers = inlier_mask

        if best_count < min_inliers or best_inliers is None:
            break

        slab_z = float(np.median(remaining[best_inliers, 2]))
        slabs.append(slab_z)

        remaining = remaining[~best_inliers]

    return sorted(slabs)


def _dbscan_method(
    z_values: np.ndarray,
    eps: float = 0.4,
    min_samples: int = 20,
) -> list[float]:
    """Cluster Z-values with DBSCAN to find slab elevations."""
    z_col = z_values.reshape(-1, 1)
    clustering = DBSCAN_Clustering(eps=eps, min_samples=min_samples).fit(z_col)
    labels = clustering.labels_

    slabs: list[float] = []
    for label in sorted(set(labels)):
        if label == -1:
            continue
        cluster_z = z_values[labels == label]
        z_spread = float(cluster_z.max() - cluster_z.min())
        if z_spread < 1.0:  # tight horizontal cluster
            slabs.append(float(np.median(cluster_z)))

    return sorted(slabs)


def _merge_slab_candidates(
    all_candidates: dict[str, list[float]],
    tolerance: float = 0.5,
) -> list[float]:
    """Merge near-duplicate slab elevations from all methods."""
    combined: list[float] = []
    for slabs in all_candidates.values():
        combined.extend(slabs)

    if not combined:
        return []

    combined.sort()
    merged = [combined[0]]
    counts = [1]

    for val in combined[1:]:
        if abs(val - merged[-1]) <= tolerance:
            n = counts[-1]
            merged[-1] = (merged[-1] * n + val) / (n + 1)
            counts[-1] = n + 1
        else:
            merged.append(val)
            counts.append(1)

    return merged


def _validate_slab_spacing(
    slabs: list[float],
    min_gap_m: float = 1.5,
) -> list[float]:
    """Remove spurious slabs that create unreasonably thin gaps.

    When two consecutive slabs are closer than *min_gap_m*, they are
    merged by averaging.  This eliminates noise-induced phantom slabs
    that would otherwise produce incorrect extra floor levels.
    """
    if len(slabs) < 3:
        return slabs

    validated = [slabs[0]]
    for s in slabs[1:]:
        if s - validated[-1] >= min_gap_m:
            validated.append(s)
        else:
            # Average with previous — keep the merged value
            validated[-1] = (validated[-1] + s) / 2.0

    return validated


def _compute_method_agreement(
    all_candidates: dict[str, list[float]],
) -> tuple[list[str], float]:
    """Compute which methods agree and an agreement score.

    Returns
    -------
    methods_agreed : list[str]
        Methods whose slab count is within +/- 1 of the median count.
    agreement_score : float
        Proportion of producing methods that agree (0.0 -- 1.0).
    """
    if not all_candidates:
        return [], 0.0

    methods = list(all_candidates.keys())
    if len(methods) < 2:
        return methods, 1.0

    counts = {m: len(slabs) for m, slabs in all_candidates.items()}
    count_vals = sorted(counts.values())
    median_count = count_vals[len(count_vals) // 2]

    agreed = [m for m, c in counts.items() if abs(c - median_count) <= 1]
    score = round(len(agreed) / len(methods), 2)

    return agreed, score


def _assign_levels(
    slab_elevations: list[float],
    z_values: np.ndarray,
    floor_height: float,
    include_roof_as_terrace: bool = False,
) -> list[SuggestedLevel]:
    """Assign level codes (B1, G, F01 ...) to volumes between slabs.

    The **highest** slab is classified as ``ROOF`` with
    ``is_cadastral_unit_level=False`` (unless *include_roof_as_terrace*
    is set).  Cadastral levels are only the volumes between consecutive
    intermediate slabs.
    """
    if len(slab_elevations) < 2:
        return []

    # ---- build volumes between consecutive slabs (excluding the roof) ------
    #   slabs[0 .. -2]  are floor-slab origins
    #   slabs[-1]       is the roof slab
    roof_z = slab_elevations[-1]
    floor_slabs = slab_elevations[:-1]  # slabs that START a floor volume

    volumes: list[dict] = []
    for i in range(len(floor_slabs)):
        z_lo = floor_slabs[i]
        z_hi = slab_elevations[i + 1]  # next slab = ceiling of this volume
        mask = (z_values >= z_lo) & (z_values < z_hi)
        volumes.append({
            "slab_z": round(z_lo, 2),
            "z_min": round(z_lo, 2),
            "z_max": round(z_hi, 2),
            "point_count": int(mask.sum()),
        })

    # ---- find ground level (slab nearest z = 0) ----------------------------
    ground_idx = min(
        range(len(volumes)),
        key=lambda i: abs(volumes[i]["slab_z"]),
    )

    # ---- assign codes ------------------------------------------------------
    suggested: list[SuggestedLevel] = []
    basement_counter = 0
    floor_counter = 0

    for i, vol in enumerate(volumes):
        if i < ground_idx and vol["slab_z"] < 0:
            basement_counter += 1
            code = f"B{basement_counter}"
            ltype = "basement"
        elif i == ground_idx:
            code = "G"
            ltype = "ground"
        else:
            floor_counter += 1
            code = f"F{floor_counter:02d}"
            ltype = "floor"

        pc = vol["point_count"]
        conf = _point_density_confidence(pc)

        lvl_warnings: list[str] = []
        if pc < 50:
            lvl_warnings.append("Low point density in this level volume.")

        suggested.append(
            SuggestedLevel(
                level_code=code,
                level_type=ltype,
                is_cadastral_unit_level=True,
                slab_z_m=vol["slab_z"],
                z_min_m=vol["z_min"],
                z_max_m=vol["z_max"],
                point_count=pc,
                confidence_score=round(conf, 2),
                warnings=lvl_warnings,
                human_verification_required=True,
            )
        )

    # ---- add ROOF entry ----------------------------------------------------
    roof_mask = z_values >= roof_z
    roof_pc = int(roof_mask.sum())

    suggested.append(
        SuggestedLevel(
            level_code="ROOF" if not include_roof_as_terrace else "TERRACE",
            level_type="roof_slab" if not include_roof_as_terrace else "terrace",
            is_cadastral_unit_level=include_roof_as_terrace,
            slab_z_m=round(roof_z, 2),
            z_min_m=round(roof_z, 2),
            z_max_m=round(roof_z, 2),
            point_count=roof_pc,
            confidence_score=round(_point_density_confidence(roof_pc), 2),
            warnings=[],
            human_verification_required=True,
        )
    )

    return suggested


def _point_density_confidence(point_count: int) -> float:
    """Return a confidence score based on point density."""
    if point_count > 500:
        return 0.85
    if point_count > 100:
        return 0.65
    if point_count > 20:
        return 0.40
    return 0.15
