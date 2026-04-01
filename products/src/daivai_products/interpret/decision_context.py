"""Bridge between Decision Engine (Layer 3) and Interpretation (Layer 4).

Runs all Phase 3 decision modules — chart selection, house highlighting,
confidence scoring, cross-chart validation, and (for gemstone queries)
gemstone weight computation — and packages results into a dict suitable
for injection into LLM prompt templates.
"""

from __future__ import annotations

import logging
from typing import Any

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision import (
    compute_confidence,
    compute_gemstone_weights,
    highlight_houses,
    select_charts,
    validate_cross_chart,
)
from daivai_products.decision.models import (
    ChartSelection,
    ConfidenceReport,
    CrossChartValidation,
    GemstoneReport,
    HouseHighlight,
    SectionConfidence,
)


logger = logging.getLogger(__name__)

# Query types that trigger gemstone analysis
_GEMSTONE_QUERY_TYPES = frozenset({"gemstone", "remedy_generation", "remedy", "remedies"})

# Map section template names to decision query types
_SECTION_TO_QUERY: dict[str, str] = {
    "chart_overview": "general",
    "career_analysis": "career",
    "financial_analysis": "wealth",
    "health_analysis": "health",
    "relationship_analysis": "marriage",
    "spiritual_profile": "spiritual",
    "remedy_generation": "gemstone",
    "lal_kitab_remedies": "remedy",
    "timeline_summary": "general",
}


def _map_query_type(query_type: str) -> str:
    """Normalise query type to a decision-engine-compatible key.

    Falls back to 'general' for unknown types so that the pipeline
    never raises on unrecognised sections.
    """
    normalized = query_type.strip().lower()
    return _SECTION_TO_QUERY.get(normalized, normalized)


# ---------------------------------------------------------------------------
# Confidence narrative
# ---------------------------------------------------------------------------


def _confidence_narrative(report: ConfidenceReport) -> str:
    """Convert a ConfidenceReport into a human-readable narrative.

    Produces a paragraph like:
      'High confidence (82/100) overall. Career: 90/100 (strong), ...'
    """
    overall = report.overall_score

    if overall >= 80:
        level = "High"
    elif overall >= 60:
        level = "Moderate"
    elif overall >= 40:
        level = "Low-moderate"
    else:
        level = "Low"

    lines: list[str] = [
        f"{level} confidence ({overall}/100) overall.",
        f"Birth-time quality: {report.birth_time_quality}.",
    ]

    if report.birth_time_caveats:
        lines.append("Caveats: " + "; ".join(report.birth_time_caveats[:3]))

    # Per-section one-liners (top boosters/penalties only)
    for sec in report.sections:
        detail = _section_one_liner(sec)
        lines.append(f"  {sec.section.capitalize()}: {sec.score}/100 — {detail}")

    return "\n".join(lines)


def _section_one_liner(sec: SectionConfidence) -> str:
    """Summarise a single section's confidence in one line."""
    parts: list[str] = []
    if sec.boosters:
        parts.append(sec.boosters[0])
    if sec.penalties:
        parts.append(sec.penalties[0])
    if sec.caveats:
        parts.append(sec.caveats[0])
    return " ".join(parts) if parts else "No notable factors."


# ---------------------------------------------------------------------------
# House highlights narrative
# ---------------------------------------------------------------------------


def _house_highlights_narrative(highlight: HouseHighlight) -> str:
    """Format HouseHighlight for prompt injection."""
    primary_str = ", ".join(f"H{h}" for h in highlight.primary_houses)
    supporting_str = ", ".join(f"H{h}" for h in highlight.supporting_houses)
    karakas_str = ", ".join(highlight.karaka_planets) if highlight.karaka_planets else "none"

    lines = [
        f"Primary houses: {primary_str}",
        f"Supporting houses: {supporting_str}",
        f"Karaka planets: {karakas_str}",
        f"Reasoning: {highlight.reason}",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-chart summary
# ---------------------------------------------------------------------------


def _cross_chart_narrative(validation: CrossChartValidation) -> str:
    """Convert CrossChartValidation into a prompt-ready summary."""
    lines = [validation.summary]

    # Add per-planet details for noteworthy patterns
    for check in validation.checks:
        if check.pattern in ("strong_confirmed", "neech_bhanga_potential", "d1_weakened"):
            lines.append(f"  {check.planet}: {check.explanation}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Chart selection summary
# ---------------------------------------------------------------------------


def _chart_selection_narrative(selection: ChartSelection) -> str:
    """Format ChartSelection for prompt injection."""
    supporting = ", ".join(selection.supporting_charts)
    return (
        f"Primary: {selection.primary_chart}. Supporting: {supporting}. Reason: {selection.reason}"
    )


# ---------------------------------------------------------------------------
# Gemstone summary
# ---------------------------------------------------------------------------


def _gemstone_narrative(report: GemstoneReport) -> str:
    """Format GemstoneReport for prompt injection."""
    lines = [f"Lagna: {report.lagna} | Lord: {report.lagna_lord}"]

    for w in report.weights:
        if w.status == "RECOMMENDED":
            lines.append(
                f"  RECOMMENDED: {w.stone} — {w.recommended_ratti:.1f} ratti for {w.planet}"
            )
        elif w.status == "TEST_WITH_CAUTION":
            lines.append(f"  TEST: {w.stone} — {w.recommended_ratti:.1f} ratti for {w.planet}")
        else:
            alts = ", ".join(w.free_alternatives[:3]) if w.free_alternatives else "none"
            lines.append(f"  PROHIBITED: {w.stone} for {w.planet} — alternatives: {alts}")

    if report.safety_warnings:
        lines.append("Safety warnings:")
        for warn in report.safety_warnings:
            lines.append(f"  - {warn}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_decision_context(
    query_type: str,
    analysis: FullChartAnalysis,
    body_weight_kg: float = 70.0,
) -> dict[str, Any]:
    """Build complete decision context for prompt injection.

    Runs all Phase 3 decision modules and packages results into a dict
    that the renderer can merge into its Jinja2 template context.

    Args:
        query_type: Section name or query category (e.g. 'career_analysis',
                    'gemstone', 'health').
        analysis: Pre-computed FullChartAnalysis from engine.
        body_weight_kg: Native's body weight in kg (used for gemstone ratti).

    Returns:
        Dict with keys: decision_confidence_narrative, decision_house_highlights,
        decision_cross_chart, decision_chart_selection, decision_gemstone (optional).
    """
    mapped = _map_query_type(query_type)
    ctx: dict[str, Any] = {}

    try:
        # 1. Confidence scoring
        confidence_report = compute_confidence(analysis)
        ctx["decision_confidence_narrative"] = _confidence_narrative(confidence_report)
        ctx["decision_confidence_score"] = confidence_report.overall_score

        # 2. House highlighting
        house_highlight = highlight_houses(mapped, analysis)
        ctx["decision_house_highlights"] = _house_highlights_narrative(house_highlight)

        # 3. Cross-chart validation (D1 vs D9)
        cross_validation = validate_cross_chart(analysis)
        ctx["decision_cross_chart"] = _cross_chart_narrative(cross_validation)

        # 4. Chart selection
        chart_selection = select_charts(mapped, analysis)
        ctx["decision_chart_selection"] = _chart_selection_narrative(chart_selection)

        # 5. Gemstone weights (only for remedy/gemstone queries)
        if mapped in _GEMSTONE_QUERY_TYPES:
            gemstone_report = compute_gemstone_weights(analysis, body_weight_kg=body_weight_kg)
            ctx["decision_gemstone"] = _gemstone_narrative(gemstone_report)
        else:
            ctx["decision_gemstone"] = ""

    except Exception:
        logger.exception("Decision context build failed for query_type=%s", query_type)
        ctx.setdefault("decision_confidence_narrative", "Decision context unavailable.")
        ctx.setdefault("decision_house_highlights", "")
        ctx.setdefault("decision_cross_chart", "")
        ctx.setdefault("decision_chart_selection", "")
        ctx.setdefault("decision_gemstone", "")

    return ctx
