"""Kundali report orchestrator — 18-section report builder."""
from __future__ import annotations

import logging
from typing import Any

from jyotish_engine.models.chart import ChartData
from jyotish_engine.compute.dasha import compute_mahadashas, find_current_dasha
from jyotish_engine.compute.yoga import detect_all_yogas
from jyotish_engine.compute.dosha import detect_all_doshas
from jyotish_engine.compute.ashtakavarga import compute_ashtakavarga
from jyotish_engine.compute.chart import get_house_lord
from jyotish_products.plugins.kundali.diamond import render_diamond_text, render_chart_summary

logger = logging.getLogger(__name__)

# The 18 sections of a complete kundali report
REPORT_SECTIONS = [
    "chart_summary",
    "diamond_chart",
    "planetary_positions",
    "house_lords",
    "yogas",
    "doshas",
    "mahadasha_timeline",
    "current_dasha",
    "ashtakavarga",
    "personality",
    "career",
    "finances",
    "relationships",
    "health",
    "spirituality",
    "remedies",
    "gemstones",
    "timeline_summary",
]


def generate_report(
    chart: ChartData,
    sections: list[str] | None = None,
    llm_backend: str = "none",
) -> str:
    """Generate a complete kundali report.

    Args:
        chart: Computed birth chart.
        sections: Specific sections to include (None = all 18).
        llm_backend: LLM backend for interpretation sections.

    Returns:
        Complete report as formatted text.
    """
    active_sections = sections or REPORT_SECTIONS
    parts: list[str] = []

    for section in active_sections:
        try:
            content = _render_section(chart, section, llm_backend)
            if content:
                parts.append(content)
        except Exception as e:
            logger.warning("Error rendering section '%s': %s", section, e)
            parts.append(f"[Section '{section}' unavailable: {e}]")

    return "\n\n".join(parts)


def _render_section(chart: ChartData, section: str, llm_backend: str) -> str:
    """Render a single report section."""
    match section:
        case "chart_summary":
            return render_chart_summary(chart)

        case "diamond_chart":
            return render_diamond_text(chart)

        case "planetary_positions":
            return _section_planets(chart)

        case "house_lords":
            return _section_house_lords(chart)

        case "yogas":
            return _section_yogas(chart)

        case "doshas":
            return _section_doshas(chart)

        case "mahadasha_timeline":
            return _section_mahadasha(chart)

        case "current_dasha":
            return _section_current_dasha(chart)

        case "ashtakavarga":
            return _section_ashtakavarga(chart)

        case "gemstones":
            return _section_gemstones(chart)

        case _:
            if llm_backend != "none":
                return f"[LLM section: {section} — requires --llm flag]"
            return f"[Section: {section} — computation only, use --llm for interpretation]"


def _section_planets(chart: ChartData) -> str:
    """Planetary positions section."""
    lines = ["═══ Planetary Positions ═══"]
    for p in chart.planets.values():
        flags = []
        if p.is_retrograde:
            flags.append("R")
        if p.is_combust:
            flags.append("C")
        flag_str = f" [{','.join(flags)}]" if flags else ""
        lines.append(
            f"  {p.name:<10} {p.sign} (House {p.house}) — "
            f"{p.degree_in_sign:.1f}° {p.nakshatra} Pada {p.pada} | "
            f"{p.dignity}{flag_str}"
        )
    return "\n".join(lines)


def _section_house_lords(chart: ChartData) -> str:
    """House lords section."""
    lines = ["═══ House Lords ═══"]
    for h in range(1, 13):
        lord = get_house_lord(chart, h)
        lord_data = chart.planets.get(lord)
        if lord_data:
            lines.append(
                f"  House {h:>2}: {lord:<10} in {lord_data.sign} (House {lord_data.house})"
            )
    return "\n".join(lines)


def _section_yogas(chart: ChartData) -> str:
    """Yogas section."""
    yogas = detect_all_yogas(chart)
    if not yogas:
        return "═══ Yogas ═══\n  No significant yogas detected."

    lines = ["═══ Yogas ═══"]
    for y in yogas:
        icon = "✅" if y.effect == "benefic" else "⚠️" if y.effect == "mixed" else "❌"
        lines.append(f"  {icon} {y.name} ({y.name_hindi}) — {y.description}")
    return "\n".join(lines)


def _section_doshas(chart: ChartData) -> str:
    """Doshas section."""
    doshas = detect_all_doshas(chart)
    if not doshas:
        return "═══ Doshas ═══\n  No doshas detected."

    lines = ["═══ Doshas ═══"]
    for d in doshas:
        icon = "⚠️" if d.is_present else "✅"
        lines.append(f"  {icon} {d.name} — {d.description}")
    return "\n".join(lines)


def _section_mahadasha(chart: ChartData) -> str:
    """Mahadasha timeline."""
    dashas = compute_mahadashas(chart)
    lines = ["═══ Vimshottari Mahadasha Timeline ═══"]

    from datetime import datetime
    now = datetime.now(tz=dashas[0].start.tzinfo) if dashas else datetime.now()

    for md in dashas:
        marker = " ← CURRENT" if md.start <= now <= md.end else ""
        lines.append(
            f"  {md.lord:>8}  {md.start.strftime('%Y-%m-%d')} to "
            f"{md.end.strftime('%Y-%m-%d')}{marker}"
        )
    return "\n".join(lines)


def _section_current_dasha(chart: ChartData) -> str:
    """Current dasha period details."""
    dashas = compute_mahadashas(chart)
    current = find_current_dasha(dashas)
    if not current:
        return "═══ Current Dasha ═══\n  Unable to determine current dasha."

    lines = [
        "═══ Current Dasha Period ═══",
        f"  Mahadasha Lord: {current.lord}",
        f"  Period: {current.start.strftime('%Y-%m-%d')} to {current.end.strftime('%Y-%m-%d')}",
    ]
    return "\n".join(lines)


def _section_ashtakavarga(chart: ChartData) -> str:
    """Ashtakavarga summary."""
    try:
        avk = compute_ashtakavarga(chart)
        lines = ["═══ Ashtakavarga (Sarva) ═══"]
        from jyotish_engine.constants import SIGNS
        for i, bindus in enumerate(avk.sarva):
            sign = SIGNS[i]
            bar = "█" * (bindus // 3) + "░" * ((8 - bindus) // 3)
            lines.append(f"  {sign:<12} {bindus:>2} bindus {bar}")
        lines.append(f"  Total: {sum(avk.sarva)}")
        return "\n".join(lines)
    except Exception as e:
        return f"═══ Ashtakavarga ═══\n  [Error: {e}]"


def _section_gemstones(chart: ChartData) -> str:
    """Gemstone recommendations from lordship rules."""
    try:
        from jyotish_products.interpret.context import build_lordship_context
        ctx = build_lordship_context(chart.lagna_sign)

        lines = ["═══ Gemstone Recommendations ═══"]
        lines.append(f"  Lagna: {chart.lagna_sign} ({chart.lagna_sign_en})")
        lines.append("")

        for s in ctx.get("recommended_stones", []):
            lines.append(f"  ✅ RECOMMENDED: {s['stone']} ({s['planet']}) — {s['reasoning'][:80]}")

        for s in ctx.get("test_stones", []):
            lines.append(f"  ⚠️ TEST WITH CAUTION: {s['stone']} ({s['planet']})")

        for s in ctx.get("prohibited_stones", []):
            lines.append(f"  ❌ PROHIBITED: {s['stone']} ({s['planet']}) — {s['reasoning'][:80]}")

        maraka = ctx.get("maraka", [])
        if maraka:
            lines.append("")
            lines.append("  MARAKA planets (7th/2nd lords):")
            for m in maraka:
                lines.append(f"    ⚠️ {m['planet']} — {m['house_str']}")

        return "\n".join(lines)
    except Exception as e:
        return f"═══ Gemstones ═══\n  [Error: {e}]"
