"""Prediction accuracy engine — compute metrics and credibility scores.

Tracks prediction outcomes (confirmed / not_occurred / opposite / pending),
computes per-category accuracy rates, and derives an overall credibility
score with leveled tiers from novice to master.
"""

from __future__ import annotations

from daivai_products.plugins.predictions.models import (
    AccuracyMetrics,
    CredibilityLevel,
    CredibilityScore,
)
from daivai_products.store.events import LifeEvent
from daivai_products.store.predictions import Prediction


__all__ = ["AccuracyMetrics", "CredibilityScore", "compute_accuracy", "compute_credibility"]

# ---------------------------------------------------------------------------
# Category mapping — map prediction categories to event types for matching
# ---------------------------------------------------------------------------

# Prediction categories and their corresponding event types for cross-referencing
_CATEGORY_EVENT_MAP: dict[str, list[str]] = {
    "career": ["career"],
    "marriage": ["marriage"],
    "health": ["health"],
    "finance": ["finance", "property"],
    "education": ["education"],
    "travel": ["travel"],
    "spirituality": ["spirituality"],
    "legal": ["legal"],
    "children": ["child"],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _classify_prediction(prediction: Prediction) -> str:
    """Classify a prediction into correct / incorrect / pending.

    Args:
        prediction: A prediction record.

    Returns:
        One of 'correct', 'incorrect', 'pending'.
    """
    match prediction.outcome:
        case "confirmed":
            return "correct"
        case "not_occurred" | "opposite":
            return "incorrect"
        case _:
            return "pending"


def _compute_category_accuracy(
    predictions: list[Prediction],
) -> dict[str, float]:
    """Compute accuracy rate per category.

    Args:
        predictions: List of prediction records.

    Returns:
        Dict mapping category name to accuracy rate (0.0-1.0).
    """
    cat_stats: dict[str, dict[str, int]] = {}

    for pred in predictions:
        cat = pred.category or "unknown"
        if cat not in cat_stats:
            cat_stats[cat] = {"correct": 0, "decided": 0}

        status = _classify_prediction(pred)
        if status != "pending":
            cat_stats[cat]["decided"] += 1
            if status == "correct":
                cat_stats[cat]["correct"] += 1

    result: dict[str, float] = {}
    for cat, stats in cat_stats.items():
        decided = stats["decided"]
        if decided > 0:
            result[cat] = round(stats["correct"] / decided, 4)
        # Skip categories with zero decided predictions

    return result


def _auto_verify_predictions(
    predictions: list[Prediction],
    events: list[LifeEvent],
) -> list[Prediction]:
    """Cross-reference predictions against life events for auto-verification.

    If a prediction is still pending and a life event exists that matches its
    category and falls within a reasonable date window, mark it as confirmed.
    This does NOT mutate the database; it returns a copy of the list with
    adjusted outcomes for scoring purposes only.

    Args:
        predictions: All predictions (may include pending ones).
        events: Known life events.

    Returns:
        Copy of predictions with pending items auto-verified where possible.
    """
    if not events:
        return predictions

    # Build a set of (event_type, event_date) for quick lookup
    event_keys: set[tuple[str, str]] = set()
    for ev in events:
        event_keys.add((ev.event_type, ev.event_date))
        # Also add mapped categories
        for cat, types in _CATEGORY_EVENT_MAP.items():
            if ev.event_type in types:
                event_keys.add((cat, ev.event_date))

    updated: list[Prediction] = []
    for pred in predictions:
        if pred.outcome != "pending":
            updated.append(pred)
            continue

        # Check if any event matches this prediction's category and date
        matched = False
        for ev in events:
            ev_cats = [ev.event_type]
            for cat, types in _CATEGORY_EVENT_MAP.items():
                if ev.event_type in types:
                    ev_cats.append(cat)

            if pred.category in ev_cats and pred.prediction_date == ev.event_date:
                matched = True
                break

        if matched:
            # Create a modified copy with confirmed outcome
            updated.append(
                Prediction(
                    id=pred.id,
                    chart_id=pred.chart_id,
                    prediction_date=pred.prediction_date,
                    category=pred.category,
                    prediction=pred.prediction,
                    confidence=pred.confidence,
                    dasha_lord=pred.dasha_lord,
                    outcome="confirmed",
                    outcome_date=pred.outcome_date,
                    notes="Auto-verified from life event",
                    created_at=pred.created_at,
                )
            )
        else:
            updated.append(pred)

    return updated


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_accuracy(
    predictions: list[Prediction],
    events: list[LifeEvent] | None = None,
) -> AccuracyMetrics:
    """Compute prediction accuracy metrics.

    If life events are provided, pending predictions are cross-referenced
    against them for auto-verification before computing metrics.

    Args:
        predictions: List of prediction records from PredictionTracker.
        events: Optional list of life events for cross-referencing.

    Returns:
        AccuracyMetrics with total, correct, incorrect, pending, and per-category rates.
    """
    if not predictions:
        return AccuracyMetrics()

    working = predictions
    if events:
        working = _auto_verify_predictions(predictions, events)

    correct = 0
    incorrect = 0
    pending = 0

    for pred in working:
        status = _classify_prediction(pred)
        match status:
            case "correct":
                correct += 1
            case "incorrect":
                incorrect += 1
            case _:
                pending += 1

    decided = correct + incorrect
    rate = round(correct / decided, 4) if decided > 0 else 0.0

    by_category = _compute_category_accuracy(working)

    return AccuracyMetrics(
        total_predictions=len(working),
        verified_correct=correct,
        verified_incorrect=incorrect,
        pending=pending,
        accuracy_rate=rate,
        by_category=by_category,
    )


def compute_credibility(metrics: AccuracyMetrics) -> CredibilityScore:
    """Compute overall credibility from accuracy metrics.

    Credibility levels (BPHS-inspired progressive mastery):
    - novice (0-20): fewer than 10 total predictions
    - developing (21-40): accuracy below 50%
    - reliable (41-60): accuracy between 50-70%
    - expert (61-80): accuracy between 70-85%
    - master (81-100): accuracy above 85% with 50+ verified predictions

    Args:
        metrics: Computed accuracy metrics.

    Returns:
        CredibilityScore with numeric score, level label, and contributing factors.
    """
    factors: list[str] = []
    decided = metrics.verified_correct + metrics.verified_incorrect

    # Rule 1: Too few predictions → novice
    if metrics.total_predictions < 10:
        factors.append(f"Only {metrics.total_predictions} predictions logged (need 10+)")
        return CredibilityScore(
            score=max(0, min(20, metrics.total_predictions * 2)),
            level="novice",
            factors=factors,
        )

    accuracy = metrics.accuracy_rate

    # Build factors list
    factors.append(f"Accuracy: {accuracy:.1%} ({metrics.verified_correct}/{decided})")
    factors.append(f"Total predictions: {metrics.total_predictions}")

    if metrics.pending > 0:
        pending_pct = metrics.pending / metrics.total_predictions
        factors.append(f"Pending: {metrics.pending} ({pending_pct:.0%})")

    cat_count = len(metrics.by_category)
    if cat_count > 0:
        factors.append(f"Categories covered: {cat_count}")

    # Determine level and score
    if accuracy > 0.85 and decided >= 50:
        # Master tier: 81-100
        # Scale from 81 at exactly 85% accuracy to 100 at 100% accuracy
        raw = 81 + int((accuracy - 0.85) / 0.15 * 19)
        score = min(100, raw)
        level: CredibilityLevel = "master"
        factors.append("Achieved master level with 50+ verified predictions")
    elif accuracy > 0.70:
        # Expert tier: 61-80
        raw = 61 + int((accuracy - 0.70) / 0.15 * 19)
        score = min(80, raw)
        level = "expert"
        # Bonus for high volume
        if decided >= 50:
            factors.append("Strong prediction volume (50+)")
    elif accuracy >= 0.50:
        # Reliable tier: 41-60
        raw = 41 + int((accuracy - 0.50) / 0.20 * 19)
        score = min(60, raw)
        level = "reliable"
    elif decided > 0:
        # Developing tier: 21-40
        raw = 21 + int(accuracy / 0.50 * 19)
        score = min(40, raw)
        level = "developing"
        factors.append("Accuracy below 50% — review prediction methodology")
    else:
        # No decided predictions yet
        score = 15
        level = "novice"
        factors.append("No outcomes recorded yet")

    return CredibilityScore(score=score, level=level, factors=factors)
