"""Decision context prompt fragment — injected into all interpretation prompts.

When the interpretation renderer has Phase 3 decision context available,
this template is rendered and appended to the system prompt so the LLM
has structured guidance about confidence, relevant houses, cross-chart
consistency, and (when applicable) gemstone ratti recommendations.
"""

from __future__ import annotations

from typing import Any


DECISION_CONTEXT_TEMPLATE = """\
## Analysis Confidence
{confidence_narrative}

## Relevant Charts for {query_type}
{chart_selection}

## Relevant Houses for {query_type}
{house_highlights}

## Cross-Chart Validation (D1 vs D9)
{cross_chart_summary}

## Gemstone Guidance (if applicable)
{gemstone_summary}
"""


def render_decision_fragment(
    query_type: str,
    decision_ctx: dict[str, Any],
) -> str:
    """Render the decision context template fragment.

    Args:
        query_type: Human-readable query category ('career', 'health', etc.).
        decision_ctx: Dict produced by build_decision_context().

    Returns:
        Rendered template string ready for injection into the system prompt.
        Returns empty string if decision context is empty or missing.
    """
    confidence = decision_ctx.get("decision_confidence_narrative", "")
    if not confidence:
        return ""

    gemstone = decision_ctx.get("decision_gemstone", "")
    gemstone_block = gemstone if gemstone else "Not applicable for this query type."

    return DECISION_CONTEXT_TEMPLATE.format(
        confidence_narrative=confidence,
        query_type=query_type,
        chart_selection=decision_ctx.get("decision_chart_selection", "N/A"),
        house_highlights=decision_ctx.get("decision_house_highlights", "N/A"),
        cross_chart_summary=decision_ctx.get("decision_cross_chart", "N/A"),
        gemstone_summary=gemstone_block,
    )
