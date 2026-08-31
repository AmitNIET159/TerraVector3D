"""Floor-plan image analysis using classical OpenCV techniques.

Detects preliminary room/unit-boundary candidates from a floor-plan image.
All detected boundaries are proposals — never legally valid property
boundaries. Every result requires authorised human confirmation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from .models import DEMO_PARENT_ULPIN, FloorPlanResult, ProposedUnit


def analyze_floor_plan(
    image_path: str,
    metres_per_pixel: Optional[float] = None,
) -> dict:
    """Analyse a floor-plan image and propose room/unit boundaries.

    Parameters
    ----------
    image_path : str
        Path to a PNG or JPG floor-plan image.
    metres_per_pixel : float or None
        Optional scale calibration.  When *None*, metric areas are not
        computed and a warning is emitted.

    Returns
    -------
    dict
        JSON-serialisable floor-plan analysis result.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Cannot decode image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2,
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(
        morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
    )

    img_area = float(img.shape[0] * img.shape[1])
    min_area = img_area * 0.005
    max_area = img_area * 0.80

    proposed_units: list[ProposedUnit] = []

    for idx, cnt in enumerate(contours):
        area_px = cv2.contourArea(cnt)
        if area_px < min_area or area_px > max_area:
            continue

        epsilon = 0.02 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        if len(approx) < 3:
            continue

        # --- geometry metrics ------------------------------------------------
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area_px / hull_area if hull_area > 0 else 0.0

        x, y, w, h = cv2.boundingRect(cnt)
        aspect = min(w, h) / max(w, h) if max(w, h) > 0 else 0.0
        rel_area = area_px / img_area

        # --- confidence ------------------------------------------------------
        confidence = 0.40
        confidence += 0.20 * solidity
        confidence += 0.10 * aspect
        confidence += 0.05 * min(1.0, rel_area * 10)
        if metres_per_pixel is not None:
            confidence += 0.10  # calibration bonus
        confidence = round(min(0.95, max(0.10, confidence)), 2)

        # --- metric area -----------------------------------------------------
        unit_warnings: list[str] = []
        if metres_per_pixel is not None:
            area_sqm: Optional[float] = round(area_px * metres_per_pixel ** 2, 2)
            metric_available = True
        else:
            area_sqm = None
            metric_available = False
            unit_warnings.append(
                "Scale calibration is required before metric area can be used."
            )

        boundary = approx.reshape(-1, 2).tolist()

        proposed_units.append(
            ProposedUnit(
                proposed_unit_code=f"UNIT_{idx + 1:03d}",
                proposed_boundary=boundary,
                area_px=round(area_px, 1),
                area_sqm=area_sqm,
                metric_area_available=metric_available,
                confidence_score=confidence,
                label_suggestion=f"proposed_unit_candidate_{idx + 1}",
                warnings=unit_warnings,
                human_verification_required=True,
            )
        )

    overall_warnings: list[str] = []
    if not proposed_units:
        overall_warnings.append(
            "No unit-boundary candidates detected in the floor-plan image."
        )
    if metres_per_pixel is None:
        overall_warnings.append(
            "No scale calibration provided; all areas are in pixels only."
        )

    result = FloorPlanResult(
        parent_ulpin=DEMO_PARENT_ULPIN,
        coordinate_reference="LOCAL_METERS",
        image_path=str(path),
        metres_per_pixel=metres_per_pixel,
        proposed_units=proposed_units,
        warnings=overall_warnings,
        human_verification_required=True,
    )
    return result.model_dump()
