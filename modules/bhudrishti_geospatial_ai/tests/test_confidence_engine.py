"""Tests for confidence engine."""

import pytest

from src.confidence_engine import calculate_confidence


class TestConfidenceEngine:
    def test_all_high_sources(self):
        sources = {
            "source_quality": 0.95,
            "image_quality": 0.90,
            "pointcloud_density": 0.92,
            "model_certainty": 0.88,
            "validation_result": 0.91,
        }
        result = calculate_confidence(sources)
        assert result["confidence_level"] == "high"
        assert result["overall_score"] >= 0.80
        assert result["human_verification_required"] is True

    def test_all_low_sources(self):
        sources = {
            "source_quality": 0.10,
            "image_quality": 0.10,
            "pointcloud_density": 0.10,
            "model_certainty": 0.10,
            "validation_result": 0.10,
        }
        result = calculate_confidence(sources)
        assert result["confidence_level"] == "low"
        assert result["overall_score"] < 0.50

    def test_mixed_sources(self):
        sources = {
            "source_quality": 0.90,
            "image_quality": 0.30,
            "pointcloud_density": 0.70,
            "model_certainty": 0.50,
            "validation_result": 0.60,
        }
        result = calculate_confidence(sources)
        assert result["overall_score"] > 0.0
        assert result["confidence_level"] in ("medium", "high", "low")

    def test_missing_sources(self):
        sources = {
            "source_quality": 0.80,
            "image_quality": 0.75,
        }
        result = calculate_confidence(sources)
        assert len(result["missing_sources"]) == 3
        assert len(result["available_sources"]) == 2
        assert len(result["warnings"]) >= 1

    def test_all_missing(self):
        result = calculate_confidence({})
        assert result["overall_score"] == 0.0
        assert result["confidence_level"] == "low"
        assert len(result["missing_sources"]) == 5

    def test_all_weak_capped(self):
        sources = {
            "source_quality": 0.20,
            "image_quality": 0.15,
            "pointcloud_density": 0.25,
            "model_certainty": 0.10,
            "validation_result": 0.20,
        }
        result = calculate_confidence(sources)
        assert result["overall_score"] <= 0.29
        assert result["confidence_level"] == "low"

    def test_human_verification_required(self):
        result = calculate_confidence({"source_quality": 0.99})
        assert result["human_verification_required"] is True

    def test_renormalization(self):
        # Only one source provided -- should still produce a valid score
        result = calculate_confidence({"source_quality": 1.0})
        assert result["overall_score"] > 0.0
        assert "source_quality" in result["available_sources"]
        assert len(result["missing_sources"]) == 4


class TestDisagreementCap:
    """Confidence must be capped at 'medium' when methods disagree."""

    def test_disagreement_caps_at_medium(self):
        """Even with all high factor scores, disagreement caps at medium."""
        sources = {
            "source_quality": 0.95,
            "image_quality": 0.90,
            "pointcloud_density": 0.92,
            "model_certainty": 0.88,
            "validation_result": 0.91,
            "method_agreement_score": 0.5,  # disagreement
        }
        result = calculate_confidence(sources)
        assert result["confidence_level"] == "medium", (
            f"Expected 'medium' due to disagreement, got '{result['confidence_level']}'"
        )
        # overall_score is still mathematically high, but level is capped
        assert result["overall_score"] >= 0.80

    def test_disagreement_warning_present(self):
        sources = {
            "source_quality": 0.85,
            "method_agreement_score": 0.33,
        }
        result = calculate_confidence(sources)
        assert any(
            "disagree" in w.lower() for w in result["warnings"]
        ), f"Expected disagreement warning, got {result['warnings']}"

    def test_agreement_does_not_cap(self):
        """When agreement score >= 0.8, high confidence is allowed."""
        sources = {
            "source_quality": 0.95,
            "image_quality": 0.90,
            "pointcloud_density": 0.92,
            "model_certainty": 0.88,
            "validation_result": 0.91,
            "method_agreement_score": 1.0,  # full agreement
        }
        result = calculate_confidence(sources)
        assert result["confidence_level"] == "high"

    def test_no_agreement_key_is_fine(self):
        """Without method_agreement_score, normal rules apply."""
        sources = {
            "source_quality": 0.95,
            "image_quality": 0.90,
            "pointcloud_density": 0.92,
            "model_certainty": 0.88,
            "validation_result": 0.91,
        }
        result = calculate_confidence(sources)
        assert result["confidence_level"] == "high"

    def test_disagreement_explanation_mentions_cap(self):
        sources = {
            "source_quality": 0.90,
            "method_agreement_score": 0.67,
        }
        result = calculate_confidence(sources)
        assert "capped" in result["explanation"].lower() or "disagree" in result["explanation"].lower()
