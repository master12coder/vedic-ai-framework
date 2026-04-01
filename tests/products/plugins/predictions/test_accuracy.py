"""Tests for the prediction accuracy engine."""

from __future__ import annotations

from daivai_products.plugins.predictions.accuracy import (
    AccuracyMetrics,
    CredibilityScore,
    compute_accuracy,
    compute_credibility,
)
from daivai_products.plugins.predictions.engine import format_accuracy_report
from daivai_products.store.events import LifeEvent
from daivai_products.store.predictions import Prediction


def _make_predictions(
    count: int,
    confirmed: int = 0,
    not_occurred: int = 0,
    category: str = "career",
) -> list[Prediction]:
    """Build a list of prediction records for testing."""
    preds: list[Prediction] = []
    idx = 0
    for _ in range(confirmed):
        preds.append(
            Prediction(
                id=idx,
                prediction_date="2025-01-01",
                category=category,
                prediction=f"Prediction {idx}",
                confidence=0.8,
                outcome="confirmed",
            )
        )
        idx += 1
    for _ in range(not_occurred):
        preds.append(
            Prediction(
                id=idx,
                prediction_date="2025-01-01",
                category=category,
                prediction=f"Prediction {idx}",
                confidence=0.6,
                outcome="not_occurred",
            )
        )
        idx += 1
    remaining = count - confirmed - not_occurred
    for _ in range(remaining):
        preds.append(
            Prediction(
                id=idx,
                prediction_date="2025-01-01",
                category=category,
                prediction=f"Prediction {idx}",
                confidence=0.5,
                outcome="pending",
            )
        )
        idx += 1
    return preds


class TestComputeAccuracy:
    def test_accuracy_rate_computed(self) -> None:
        """Accuracy rate should reflect confirmed / total decided."""
        preds = _make_predictions(count=10, confirmed=7, not_occurred=3)
        metrics = compute_accuracy(preds)
        assert metrics.total_predictions == 10
        assert metrics.verified_correct == 7
        assert metrics.verified_incorrect == 3
        assert metrics.pending == 0
        assert metrics.accuracy_rate == 0.7

    def test_zero_predictions_returns_defaults(self) -> None:
        """Empty predictions list should return zero-filled metrics."""
        metrics = compute_accuracy([])
        assert metrics.total_predictions == 0
        assert metrics.accuracy_rate == 0.0
        assert metrics.by_category == {}

    def test_all_pending_has_zero_accuracy(self) -> None:
        """All pending predictions should yield 0% accuracy."""
        preds = _make_predictions(count=5, confirmed=0, not_occurred=0)
        metrics = compute_accuracy(preds)
        assert metrics.pending == 5
        assert metrics.accuracy_rate == 0.0

    def test_by_category_computed(self) -> None:
        """Per-category accuracy should be computed correctly."""
        preds = _make_predictions(
            count=4, confirmed=3, not_occurred=1, category="career"
        ) + _make_predictions(count=2, confirmed=1, not_occurred=1, category="health")
        metrics = compute_accuracy(preds)
        assert "career" in metrics.by_category
        assert "health" in metrics.by_category
        assert metrics.by_category["career"] == 0.75
        assert metrics.by_category["health"] == 0.5

    def test_auto_verify_with_matching_events(self) -> None:
        """Pending predictions matching life events should be auto-verified."""
        preds = [
            Prediction(
                id=0,
                prediction_date="2025-06-15",
                category="career",
                prediction="Job change expected",
                outcome="pending",
            ),
        ]
        events = [
            LifeEvent(
                chart_id=1,
                event_date="2025-06-15",
                event_type="career",
                description="Got new job",
            ),
        ]
        metrics = compute_accuracy(preds, events=events)
        assert metrics.verified_correct == 1
        assert metrics.pending == 0


class TestComputeCredibility:
    def test_zero_predictions_is_novice(self) -> None:
        """Zero predictions should give novice level."""
        metrics = AccuracyMetrics()
        cred = compute_credibility(metrics)
        assert cred.level == "novice"
        assert cred.score <= 20

    def test_few_predictions_is_novice(self) -> None:
        """Fewer than 10 predictions should remain novice."""
        metrics = AccuracyMetrics(
            total_predictions=5,
            verified_correct=4,
            verified_incorrect=1,
            accuracy_rate=0.8,
        )
        cred = compute_credibility(metrics)
        assert cred.level == "novice"
        assert cred.score <= 20

    def test_low_accuracy_is_developing(self) -> None:
        """Below 50% accuracy with enough predictions should be developing."""
        metrics = AccuracyMetrics(
            total_predictions=20,
            verified_correct=6,
            verified_incorrect=14,
            accuracy_rate=0.3,
        )
        cred = compute_credibility(metrics)
        assert cred.level == "developing"
        assert 21 <= cred.score <= 40

    def test_moderate_accuracy_is_reliable(self) -> None:
        """50-70% accuracy should be reliable."""
        metrics = AccuracyMetrics(
            total_predictions=30,
            verified_correct=18,
            verified_incorrect=12,
            accuracy_rate=0.6,
        )
        cred = compute_credibility(metrics)
        assert cred.level == "reliable"
        assert 41 <= cred.score <= 60

    def test_high_accuracy_is_expert(self) -> None:
        """70-85% accuracy should be expert."""
        metrics = AccuracyMetrics(
            total_predictions=40,
            verified_correct=30,
            verified_incorrect=10,
            accuracy_rate=0.75,
        )
        cred = compute_credibility(metrics)
        assert cred.level == "expert"
        assert 61 <= cred.score <= 80

    def test_master_requires_volume(self) -> None:
        """Master level requires >85% accuracy AND 50+ verified predictions."""
        metrics = AccuracyMetrics(
            total_predictions=60,
            verified_correct=55,
            verified_incorrect=5,
            accuracy_rate=0.9167,
        )
        cred = compute_credibility(metrics)
        assert cred.level == "master"
        assert cred.score >= 81

    def test_high_accuracy_low_volume_is_expert(self) -> None:
        """90% accuracy but only 20 decided → expert, not master."""
        metrics = AccuracyMetrics(
            total_predictions=20,
            verified_correct=18,
            verified_incorrect=2,
            accuracy_rate=0.9,
        )
        cred = compute_credibility(metrics)
        # Not enough decided predictions (need 50) so should NOT be master
        assert cred.level == "expert"

    def test_format_accuracy_report(self) -> None:
        """format_accuracy_report should produce a readable string."""
        metrics = AccuracyMetrics(
            total_predictions=20,
            verified_correct=14,
            verified_incorrect=6,
            pending=0,
            accuracy_rate=0.7,
            by_category={"career": 0.8, "health": 0.6},
        )
        cred = CredibilityScore(score=65, level="expert", factors=["Accuracy: 70.0%"])
        report = format_accuracy_report(metrics, cred)
        assert "Prediction Accuracy Report" in report
        assert "70.0%" in report
        assert "EXPERT" in report
        assert "career" in report
