"""Remedies plugin engine — gemstone + Lal Kitab recommendations."""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.lal_kitab import compute_lal_kitab
from daivai_engine.models.chart import ChartData
from daivai_products.interpret.context import build_lordship_context


def get_gemstone_recommendations(chart: ChartData) -> str:
    """Get personalized gemstone recommendations with safety checks.

    Loads lordship rules for the chart's lagna and classifies gemstones into
    RECOMMENDED, TEST WITH CAUTION, and PROHIBITED categories. Maraka planets
    are always flagged with dual-nature warnings per Vedic safety rules.

    Args:
        chart: Computed birth chart.

    Returns:
        Formatted multi-line string with gemstone recommendations.
    """
    ctx = build_lordship_context(chart.lagna_sign)
    if not ctx:
        return f"No lordship rules found for lagna: {chart.lagna_sign}"

    return _format_recommendations(ctx, chart.name, chart.lagna_sign)


def _format_recommendations(
    ctx: dict[str, Any],
    name: str,
    lagna_sign: str,
) -> str:
    """Format lordship context into a gemstone recommendation report.

    Args:
        ctx: Lordship context dict from build_lordship_context.
        name: Native's name.
        lagna_sign: Lagna sign name.

    Returns:
        Formatted multi-line report string.
    """
    lines: list[str] = []
    lines.append(f"Gemstone Recommendations for {name} ({lagna_sign} Lagna)")
    lines.append("=" * 55)
    lines.append("")

    recommended = ctx.get("recommended_stones", [])
    test_stones = ctx.get("test_stones", [])
    prohibited = ctx.get("prohibited_stones", [])

    if recommended:
        lines.append("RECOMMENDED:")
        for s in recommended:
            lines.append(f"  + {s['stone']} ({s['planet']}) — {s['reasoning'][:80]}")
        lines.append("")

    if test_stones:
        lines.append("TEST WITH CAUTION:")
        for s in test_stones:
            lines.append(f"  ? {s['stone']} ({s['planet']}) — {s['reasoning'][:80]}")
        lines.append("")

    if prohibited:
        lines.append("PROHIBITED:")
        for s in prohibited:
            lines.append(f"  X {s['stone']} ({s['planet']}) — {s['reasoning'][:80]}")
        lines.append("")

    maraka = ctx.get("maraka", [])
    if maraka:
        lines.append("MARAKA WARNINGS:")
        for m in maraka:
            lines.append(
                f"  ! {m['planet']} — {m['house_str']} — "
                f"dual-nature: acknowledge both positive and negative effects"
            )

    return "\n".join(lines)


def get_lal_kitab_assessment(chart: ChartData, full_analysis: Any | None = None) -> str:
    """Get Lal Kitab planet assessment, debts, and remedies.

    Computes the full Lal Kitab analysis: Pakka Ghar positions,
    planet strength (5-tier), Rin (debts), and matched remedies.

    Source: Lal Kitab (Pandit Roop Chand Joshi, 1939-1952).

    Args:
        chart: Computed birth chart.
        full_analysis: Optional FullChartAnalysis — uses pre-computed lal_kitab if available.

    Returns:
        Formatted multi-line Lal Kitab report.
    """
    if full_analysis and hasattr(full_analysis, "lal_kitab") and full_analysis.lal_kitab:
        result = full_analysis.lal_kitab
    else:
        result = compute_lal_kitab(chart)
    return _format_lal_kitab(result, chart.name)


def _format_lal_kitab(result: Any, name: str) -> str:
    """Format LalKitabResult into a readable report."""
    lines: list[str] = []
    lines.append(f"Lal Kitab Assessment for {name}")
    lines.append("=" * 50)
    lines.append("")

    lines.append(f"Strongest: {result.strongest_planet}")
    lines.append(f"Weakest: {result.weakest_planet}")
    if result.dormant_planets:
        lines.append(f"Dormant (Soya Hua): {', '.join(result.dormant_planets)}")
    lines.append("")

    if result.rins:
        lines.append("RINS (DEBTS):")
        for r in result.rins:
            lines.append(f"  - {r.rin_type}: {r.severity} — {r.description}")
        lines.append("")

    if result.remedies:
        lines.append("REMEDIES:")
        for r in result.remedies[:10]:
            lines.append(f"  - {r.planet} (H{r.house}): {r.remedy_text}")
        lines.append("")

    if result.summary:
        lines.append(result.summary)

    return "\n".join(lines)
