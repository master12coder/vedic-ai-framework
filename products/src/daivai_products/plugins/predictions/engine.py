"""Predictions plugin engine — dashboard stats, formatting, and report helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from daivai_products.store.predictions import PredictionTracker


if TYPE_CHECKING:
    from daivai_products.plugins.predictions.accuracy import AccuracyMetrics, CredibilityScore
    from daivai_products.plugins.predictions.matcher import DashaEventMatch


def get_dashboard_stats(db_path: str | None = None) -> dict[str, Any]:
    """Get prediction accuracy statistics from the tracker database.

    Args:
        db_path: Optional path to the SQLite database. Uses default if None.

    Returns:
        Dict with keys: categories, overall_accuracy, total_predictions, pending.
    """
    kwargs: dict[str, Any] = {}
    if db_path is not None:
        kwargs["db_path"] = db_path

    tracker = PredictionTracker(**kwargs)
    try:
        return tracker.get_accuracy_dashboard()
    finally:
        tracker.close()


def format_dashboard(stats: dict[str, Any]) -> str:
    """Format dashboard stats into a human-readable string.

    Args:
        stats: Dashboard dict from get_dashboard_stats.

    Returns:
        Formatted multi-line report string.
    """
    lines: list[str] = [
        "Prediction Accuracy Dashboard",
        "=" * 40,
        "",
        f"Total predictions: {stats.get('total_predictions', 0)}",
        f"Pending: {stats.get('pending', 0)}",
        f"Overall accuracy: {stats.get('overall_accuracy', 0.0)}%",
        "",
    ]

    categories = stats.get("categories", {})
    if categories:
        lines.append("By Category:")
        for cat, data in categories.items():
            lines.append(
                f"  {cat}: {data['accuracy']}% "
                f"({data['confirmed']}/{data['total_decided']} confirmed)"
            )

    return "\n".join(lines)


def summarize_matches(matches: list[DashaEventMatch]) -> str:
    """Format dasha-event match results into a human-readable report.

    Args:
        matches: List of dasha-event match results.

    Returns:
        Multi-line formatted report string.
    """
    if not matches:
        return "No event-dasha matches to display."

    lines: list[str] = ["Dasha-Event Match Report", "=" * 40, ""]

    strong = sum(1 for m in matches if m.match_quality == "strong")
    moderate = sum(1 for m in matches if m.match_quality == "moderate")
    weak = sum(1 for m in matches if m.match_quality == "weak")
    lines.append(f"Total matches: {len(matches)}")
    lines.append(f"Strong: {strong} | Moderate: {moderate} | Weak: {weak}")
    lines.append("")

    for m in matches:
        quality_tag = m.match_quality.upper()
        lines.append(f"[{quality_tag}] {m.event} ({m.event_date})")
        lines.append(f"  MD: {m.dasha_lord} | AD: {m.antardasha_lord}")
        if m.relevant_houses:
            lines.append(f"  Relevant houses: {m.relevant_houses}")
        lines.append(f"  {m.explanation}")
        lines.append("")

    return "\n".join(lines)


def format_accuracy_report(
    metrics: AccuracyMetrics,
    credibility: CredibilityScore,
) -> str:
    """Format accuracy metrics and credibility into a readable report.

    Args:
        metrics: Computed accuracy metrics.
        credibility: Computed credibility score.

    Returns:
        Multi-line formatted report string.
    """
    lines: list[str] = [
        "Prediction Accuracy Report",
        "=" * 40,
        "",
        f"Total predictions: {metrics.total_predictions}",
        f"Verified correct: {metrics.verified_correct}",
        f"Verified incorrect: {metrics.verified_incorrect}",
        f"Pending: {metrics.pending}",
        f"Accuracy rate: {metrics.accuracy_rate:.1%}",
        "",
    ]

    if metrics.by_category:
        lines.append("By Category:")
        for cat, rate in sorted(metrics.by_category.items()):
            lines.append(f"  {cat}: {rate:.1%}")
        lines.append("")

    lines.append(f"Credibility: {credibility.level.upper()} ({credibility.score}/100)")
    for factor in credibility.factors:
        lines.append(f"  - {factor}")

    return "\n".join(lines)
