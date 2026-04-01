"""Tests for the pandit 6-layer validation pipeline."""

from __future__ import annotations

from datetime import datetime

from daivai_products.plugins.pandit.validation import ValidationResult, validate_correction
from daivai_products.store.corrections import PanditCorrection


def _make_correction(**kwargs: object) -> PanditCorrection:
    """Helper to create a correction with sensible defaults."""
    defaults = {
        "id": "val01",
        "category": "gemstone",
        "pandit_said": "Emerald should be worn on Wednesday morning",
        "pandit_reasoning": "Per BPHS Ch.80 gemstone chapter, Mercury remedies work best on Wednesday",
        "chart_name": "Test Chart",
        "lagna": "Mithuna",
        "status": "validated",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    defaults.update(kwargs)
    return PanditCorrection(**defaults)  # type: ignore[arg-type]


class TestValidateCorrection:
    def test_valid_correction_passes_all_layers(self) -> None:
        """A well-formed, safe correction should pass all 6 layers."""
        correction = _make_correction()
        result = validate_correction(correction, min_trust=0.0)
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.passed_layers == [1, 2, 3, 4, 5, 6]
        assert result.failed_layer is None
        assert result.failure_reason == ""

    def test_missing_fields_fails_layer_1(self) -> None:
        """Correction with empty pandit_said should fail format check."""
        correction = _make_correction(pandit_said="", pandit_reasoning="some reason")
        result = validate_correction(correction, min_trust=0.0)
        assert result.is_valid is False
        assert result.failed_layer == 1
        assert "pandit_said" in result.failure_reason

    def test_missing_category_fails_layer_1(self) -> None:
        """Correction with empty category should fail format check."""
        correction = _make_correction(category="")
        result = validate_correction(correction, min_trust=0.0)
        assert result.is_valid is False
        assert result.failed_layer == 1
        assert "category" in result.failure_reason

    def test_invalid_scripture_fails_layer_2(self) -> None:
        """Citing a chapter without a recognised scripture should fail layer 2."""
        correction = _make_correction(
            pandit_reasoning="Chapter 42 of the unknown text says so"
        )
        result = validate_correction(correction, min_trust=0.0)
        assert result.is_valid is False
        assert result.failed_layer == 2
        assert "chapter reference" in result.failure_reason.lower()

    def test_safety_violation_fails_layer_4(self) -> None:
        """Recommending Pukhraj for Mithuna lagna should fail safety check."""
        correction = _make_correction(
            pandit_said="Recommend wear Pukhraj for Mithuna lagna always",
            pandit_reasoning="I think Jupiter is good here",
            lagna="Mithuna",
        )
        result = validate_correction(correction, min_trust=0.0)
        assert result.is_valid is False
        assert result.failed_layer == 4
        assert "SAFETY VIOLATION" in result.failure_reason

    def test_trust_threshold_enforcement(self) -> None:
        """Correction below trust threshold should fail layer 6."""
        correction = _make_correction(
            status="pending",
            pandit_reasoning="Just my opinion, no source",
            pandit_name="unknown",
        )
        result = validate_correction(correction, min_trust=0.99)
        assert result.is_valid is False
        assert result.failed_layer == 6
        assert "Trust score" in result.failure_reason

    def test_result_always_has_trust_score(self) -> None:
        """ValidationResult must always include a trust_score field."""
        correction = _make_correction()
        result = validate_correction(correction, min_trust=0.0)
        assert 0.0 <= result.trust_score <= 1.0
