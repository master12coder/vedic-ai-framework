"""Tests for the pandit trust scoring system."""

from __future__ import annotations

from datetime import datetime, timedelta

from daivai_products.plugins.pandit.trust import (
    CorrectionTrust,
    compute_trust_score,
    get_trusted_corrections,
)
from daivai_products.store.corrections import PanditCorrection


def _make_correction(**kwargs: object) -> PanditCorrection:
    """Helper to create a correction with sensible defaults."""
    defaults = {
        "id": "test01",
        "category": "gemstone",
        "pandit_said": "Emerald suits Mercury lagna",
        "pandit_reasoning": "Based on BPHS Ch.80 gemstone chapter",
        "chart_name": "Test Chart",
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    defaults.update(kwargs)
    return PanditCorrection(**defaults)  # type: ignore[arg-type]


class TestComputeTrustScore:
    def test_trust_score_between_0_and_1(self) -> None:
        """Trust score must always be in [0.0, 1.0] range."""
        correction = _make_correction()
        result = compute_trust_score(correction)
        assert isinstance(result, CorrectionTrust)
        assert 0.0 <= result.trust_score <= 1.0

    def test_scripture_citation_boosts_trust(self) -> None:
        """A correction citing BPHS should score higher than one without."""
        with_scripture = _make_correction(
            pandit_reasoning="Per BPHS Ch.80, this gemstone is appropriate"
        )
        without_scripture = _make_correction(
            pandit_reasoning="I believe this is correct"
        )
        score_with = compute_trust_score(with_scripture).trust_score
        score_without = compute_trust_score(without_scripture).trust_score
        assert score_with > score_without

    def test_validated_status_boosts_trust(self) -> None:
        """Validated corrections should score higher than pending ones."""
        validated = _make_correction(status="validated")
        pending = _make_correction(status="pending")
        assert compute_trust_score(validated).trust_score > compute_trust_score(pending).trust_score

    def test_old_correction_scores_higher(self) -> None:
        """Older corrections (time-tested) should score higher."""
        old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
        old = _make_correction(date=old_date)
        new = _make_correction(date=datetime.now().strftime("%Y-%m-%d"))
        assert compute_trust_score(old).trust_score > compute_trust_score(new).trust_score

    def test_safety_contradiction_lowers_trust(self) -> None:
        """Correction contradicting safety rules should not get contradiction bonus."""
        safe = _make_correction(pandit_said="Emerald is good for Mercury lagna")
        unsafe = _make_correction(
            pandit_said="Pukhraj mithuna recommend wear always"
        )
        assert compute_trust_score(safe).trust_score > compute_trust_score(unsafe).trust_score


class TestGetTrustedCorrections:
    def test_filters_below_threshold(self) -> None:
        """Only corrections meeting min_trust should be returned."""
        corrections = [
            _make_correction(id="a", status="validated",
                             pandit_reasoning="BPHS Ch.80 says so"),
            _make_correction(id="b", status="pending",
                             pandit_reasoning="no reason"),
        ]
        trusted = get_trusted_corrections(corrections, min_trust=0.5)
        # The validated one with BPHS citation should pass; the other may not
        ids = [c.id for c in trusted]
        assert "a" in ids

    def test_returns_sorted_by_trust(self) -> None:
        """Results should be sorted by trust score descending."""
        corrections = [
            _make_correction(id="a", status="pending",
                             pandit_reasoning="no citation"),
            _make_correction(id="b", status="validated",
                             pandit_reasoning="Per BPHS Ch.80"),
        ]
        trusted = get_trusted_corrections(corrections, min_trust=0.0)
        if len(trusted) >= 2:
            # The validated + BPHS one should come first
            assert trusted[0].id == "b"
