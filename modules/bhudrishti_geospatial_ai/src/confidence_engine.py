"""Confidence engine — combines multiple quality signals.

Weights are renormalised to exclude unavailable sources.  Missing data
always reduces reported confidence.  High confidence requires at least
some sources to be present and strong.
"""

from __future__ import annotations

from typing import Optional

from .models import ConfidenceFactorBreakdown, ConfidenceResult

_FACTOR_WEIGHTS = {
    "source_quality": 0.25,
    "image_quality": 0.20,
    "pointcloud_density": 0.25,
    "model_certainty": 0.15,
    "validation_result": 0.15,
}

_LEVEL_HIGH = 0.80
_LEVEL_MEDIUM = 0.50


def calculate_confidence(sources: dict) -> dict:
    """Calculate a combined confidence score.

    Parameters
    ----------
    sources : dict
        Mapping of factor name to score (0.0 -- 1.0).  Omit a key or set
        its value to *None* to mark it as unavailable.

        The special key ``method_agreement_score`` (0.0 -- 1.0) is NOT a
        weighted factor but a structural-agreement signal.  When present
        and below 0.8, confidence is capped at ``"medium"`` regardless of
        the weighted overall score.

    Returns
    -------
    dict
        JSON-serialisable confidence result.
    """
    # --- extract structural-agreement signal --------------------------------
    method_agreement = sources.get("method_agreement_score")
    has_disagreement = (
        method_agreement is not None
        and isinstance(method_agreement, (int, float))
        and method_agreement < 0.8
    )

    available: list[str] = []
    missing: list[str] = []
    breakdown: list[ConfidenceFactorBreakdown] = []

    for factor, weight in _FACTOR_WEIGHTS.items():
        score = sources.get(factor)
        if score is not None and isinstance(score, (int, float)):
            score = float(max(0.0, min(1.0, score)))
            available.append(factor)
            breakdown.append(
                ConfidenceFactorBreakdown(
                    factor=factor,
                    weight=weight,
                    score=round(score, 4),
                    status="available",
                )
            )
        else:
            missing.append(factor)
            breakdown.append(
                ConfidenceFactorBreakdown(
                    factor=factor,
                    weight=weight,
                    score=None,
                    status="not_available",
                )
            )

    # --- renormalise available weights --------------------------------------
    total_available_weight = sum(
        _FACTOR_WEIGHTS[f] for f in available
    )

    if total_available_weight > 0 and available:
        weighted_sum = sum(
            (_FACTOR_WEIGHTS[f] / total_available_weight) * sources[f]
            for f in available
        )
        overall = round(float(weighted_sum), 4)
    else:
        overall = 0.0

    # --- apply missing-data penalty ----------------------------------------
    missing_ratio = len(missing) / len(_FACTOR_WEIGHTS)
    penalty = missing_ratio * 0.15  # up to 15 % penalty when everything missing
    overall = round(max(0.0, overall - penalty), 4)

    # --- never high if everything absent/weak -------------------------------
    if not available:
        overall = 0.0
    elif all(
        (sources.get(f) or 0.0) < 0.3 for f in available
    ):
        overall = min(overall, 0.29)  # cap at low

    # --- classify -----------------------------------------------------------
    if overall >= _LEVEL_HIGH:
        level = "high"
    elif overall >= _LEVEL_MEDIUM:
        level = "medium"
    else:
        level = "low"

    # --- structural disagreement cap ----------------------------------------
    if has_disagreement and level == "high":
        level = "medium"

    # --- explanation --------------------------------------------------------
    parts: list[str] = []
    if has_disagreement:
        parts.append(
            f"Floor-detection methods disagree "
            f"(agreement_score={method_agreement:.2f}). "
            "Confidence capped at 'medium'. "
            "Manual floor-layout validation is required."
        )
    if missing:
        parts.append(
            f"Missing data sources ({', '.join(missing)}) reduce overall "
            f"confidence.  A {missing_ratio:.0%} data-availability penalty "
            f"of {penalty:.2f} was applied."
        )
    if level == "low":
        parts.append(
            "Low confidence: this result MUST be manually reviewed by an "
            "authorised officer before use in any cadastral or ownership "
            "workflow."
        )
    if level == "medium":
        parts.append(
            "Medium confidence: human review is strongly recommended "
            "before acting on these results."
        )
    if level == "high":
        parts.append(
            "High confidence: automated checks passed, but final "
            "authorised human verification is still required."
        )
    explanation = " ".join(parts) if parts else "All sources available."

    warnings: list[str] = []
    if missing:
        warnings.append(
            f"{len(missing)} of {len(_FACTOR_WEIGHTS)} confidence sources "
            f"are unavailable: {', '.join(missing)}."
        )
    if has_disagreement:
        warnings.append(
            "Floor-detection methods disagree; manual validation required."
        )

    result = ConfidenceResult(
        overall_score=overall,
        confidence_level=level,
        factor_breakdown=breakdown,
        available_sources=available,
        missing_sources=missing,
        explanation=explanation,
        warnings=warnings,
        human_verification_required=True,
    )
    return result.model_dump()
