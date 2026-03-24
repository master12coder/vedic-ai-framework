"""Daily companion plugin — 3 levels of guidance."""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.daily import DailySuggestion, compute_daily_suggestion
from daivai_engine.compute.dasha import find_current_dasha


logger = logging.getLogger(__name__)


class DailyLevel(StrEnum):
    """Output detail level for daily guidance."""

    SIMPLE = "simple"
    MEDIUM = "medium"
    DETAILED = "detailed"


def format_simple(suggestion: DailySuggestion) -> str:
    """One-line format: rating | color | mantra | avoid time.

    Example: "7/10 | Green | ओम् बुधाय नमः x 11 | Avoid 3-4:30 PM"
    """
    rating = suggestion.day_rating
    color = suggestion.recommended_color.split(",")[0].strip()
    mantra = suggestion.recommended_mantra.split("(")[0].strip()
    rahu = suggestion.rahu_kaal

    return f"{rating}/10 | {color} | {mantra} x 11 | Avoid {rahu}"


def format_medium(suggestion: DailySuggestion, chart: ChartData) -> str:
    """5-7 line format with key info for WhatsApp/Telegram."""
    lines: list[str] = []

    # Line 1: Rating + Day
    stars = "⭐" * suggestion.day_rating + "☆" * (10 - suggestion.day_rating)
    lines.append(f"📅 {suggestion.date} — {suggestion.vara}")
    lines.append(f"Rating: {stars} ({suggestion.day_rating}/10)")
    lines.append("")

    # Line 2: Color + Mantra
    lines.append(f"🎨 Color: {suggestion.recommended_color}")
    mantra = suggestion.recommended_mantra.split("(")[0].strip()
    lines.append(f"🙏 Mantra: {mantra} x 11")
    lines.append("")

    # Line 3: Good/Avoid
    if suggestion.good_for:
        lines.append(f"✅ Good: {'; '.join(suggestion.good_for[:3])}")
    if suggestion.avoid:
        lines.append(f"❌ Avoid: {'; '.join(suggestion.avoid[:2])}")

    # Line 4: Rahu Kaal
    lines.append(f"⏰ Rahu Kaal: {suggestion.rahu_kaal}")

    # Line 5: Health
    if suggestion.health_focus:
        lines.append(f"💪 Health: {suggestion.health_focus}")

    return "\n".join(lines)


def format_detailed(
    suggestion: DailySuggestion, chart: ChartData, full_analysis: Any | None = None
) -> str:
    """Full detailed report with transit analysis."""
    lines: list[str] = []

    # Header
    lines.append(f"═══ Daily Guidance for {chart.name} ═══")
    lines.append(f"📅 {suggestion.date} | {suggestion.vara}")
    lines.append(f"🌟 Nakshatra: {suggestion.nakshatra} | Tithi: {suggestion.tithi}")
    lines.append("")

    # Rating
    stars = "⭐" * suggestion.day_rating
    lines.append(f"Day Rating: {stars} ({suggestion.day_rating}/10)")
    lines.append("")

    # Color + Mantra
    lines.append(f"🎨 Recommended Color: {suggestion.recommended_color}")
    lines.append(f"🙏 Mantra: {suggestion.recommended_mantra}")
    lines.append("")

    # Transit impacts
    if suggestion.transit_impacts:
        lines.append("═══ Transit Analysis ═══")
        for t in suggestion.transit_impacts:
            icon = "🟢" if t.is_favorable else "🔴"
            lines.append(
                f"{icon} {t.planet} in {t.transit_sign} → "
                f"House {t.natal_house} ({t.bindus} bindus) — {t.description}"
            )
        lines.append("")

    # Good for / Avoid
    if suggestion.good_for:
        lines.append("═══ Good For Today ═══")
        for item in suggestion.good_for:
            lines.append(f" ✅ {item}")
        lines.append("")

    if suggestion.avoid:
        lines.append("═══ Avoid Today ═══")
        for item in suggestion.avoid:
            lines.append(f" ❌ {item}")
        lines.append("")

    # Rahu Kaal + Health
    lines.append(f"⏰ Rahu Kaal: {suggestion.rahu_kaal}")
    if suggestion.health_focus:
        lines.append(f"💪 Health Focus: {suggestion.health_focus}")

    # Dasha context (use pre-computed if available)
    try:
        if full_analysis and hasattr(full_analysis, "current_md"):
            md = full_analysis.current_md
        else:
            md, _ad, _pd = find_current_dasha(chart)
        if md:
            lines.append("")
            lines.append(f"📿 Current Dasha: {md.lord} Mahadasha")
    except Exception:
        pass

    return "\n".join(lines)


def run_daily(
    chart: ChartData,
    level: DailyLevel = DailyLevel.MEDIUM,
    full_analysis: Any | None = None,
) -> str:
    """Generate daily guidance at the specified level.

    Args:
        chart: Computed birth chart.
        level: Output detail level (simple/medium/detailed).
        full_analysis: Optional FullChartAnalysis — uses pre-computed data if available.

    Returns:
        Formatted daily guidance string.
    """
    suggestion = compute_daily_suggestion(chart)

    match level:
        case DailyLevel.SIMPLE:
            return format_simple(suggestion)
        case DailyLevel.MEDIUM:
            return format_medium(suggestion, chart)
        case DailyLevel.DETAILED:
            return format_detailed(suggestion, chart, full_analysis)
