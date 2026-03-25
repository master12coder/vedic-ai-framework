"""Main interpretation renderer — combines chart data with LLM prompts.

Loads lordship rules, gemstone logic, scripture citations, and Pandit Ji
corrections BEFORE every LLM call so the model has full chart-specific
knowledge context.  Validates LLM output afterwards for safety.

Sub-modules:
    _renderer_context — full chart context builder (build_chart_context)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

from jinja2 import Template

from daivai_engine.models.chart import ChartData
from daivai_products.interpret._renderer_context import build_chart_context
from daivai_products.interpret.factory import LLMBackend, get_backend
from daivai_products.interpret.validator import validate_interpretation


logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


# ---------------------------------------------------------------------------
# Prompt loading / rendering
# ---------------------------------------------------------------------------


def _load_prompt(template_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / template_name
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text()


def _render_prompt(template_name: str, context: dict[str, Any]) -> str:
    """Load and render a Jinja2 prompt template."""
    raw = _load_prompt(template_name)
    template = Template(raw)
    return cast(str, template.render(**context))


# Keep internal alias for callers that may import the private name
_build_chart_context = build_chart_context


# ---------------------------------------------------------------------------
# Public interpretation API
# ---------------------------------------------------------------------------


def interpret_chart(
    chart: ChartData,
    backend: LLMBackend | None = None,
    sections: list[str] | None = None,
    full_analysis: Any | None = None,
) -> dict[str, str]:
    """Generate full chart interpretation using LLM.

    Loads lordship rules, gemstone logic, scripture citations, and Pandit Ji
    corrections before every LLM call.  Validates output afterwards.

    Args:
        chart: Computed chart data
        backend: LLM backend to use (default from config)
        sections: Specific sections to interpret (default: all)
        full_analysis: Optional FullChartAnalysis with Phase 1 data.

    Returns:
        Dictionary of section_name -> interpreted text
    """
    if backend is None:
        backend = get_backend()

    context = build_chart_context(chart, full_analysis=full_analysis)
    lordship_ctx = context.get("lordship", {})
    system_prompt = _render_prompt("system_prompt.md", context)

    all_sections = [
        "chart_overview",
        "career_analysis",
        "financial_analysis",
        "health_analysis",
        "relationship_analysis",
        "spiritual_profile",
        "remedy_generation",
        "lal_kitab_remedies",
        "timeline_summary",
    ]

    if sections:
        all_sections = [s for s in sections if s in all_sections]

    results: dict[str, str] = {}

    for section in all_sections:
        template_name = f"{section}.md"
        try:
            user_prompt = _render_prompt(template_name, context)
            response = backend.generate(system_prompt, user_prompt)

            # Post-generation safety validation
            validated, validation_errors = validate_interpretation(
                response,
                chart.lagna_sign,
                lordship_ctx,
            )
            if validation_errors:
                logger.warning(
                    "Validation errors in %s for %s lagna: %s",
                    section,
                    chart.lagna_sign,
                    validation_errors,
                )
            results[section] = validated

        except FileNotFoundError:
            results[section] = f"[Template {template_name} not found]"
        except Exception as e:
            results[section] = f"[Error generating {section}: {e}]"

    return results


def interpret_with_events(
    chart: ChartData,
    events: list[dict[str, str]],
    backend: LLMBackend | None = None,
) -> str:
    """Interpret chart with life event validation.

    Args:
        chart: Computed chart data
        events: List of {"date": "DD/MM/YYYY", "event": "description"}
        backend: LLM backend
    """
    if backend is None:
        backend = get_backend()

    context = build_chart_context(chart)
    context["life_events"] = events

    system_prompt = _render_prompt("system_prompt.md", context)
    user_prompt = _render_prompt("life_event_validation.md", context)

    return backend.generate(system_prompt, user_prompt)


def get_daily_suggestion(
    chart: ChartData,
    backend: LLMBackend | None = None,
) -> str:
    """Get daily suggestion based on transits."""
    if backend is None:
        backend = get_backend()

    from daivai_engine.compute.transit import compute_transits

    transit_data = compute_transits(chart)

    context = build_chart_context(chart)
    context["transits"] = [
        {
            "name": t.name,
            "sign": t.sign,
            "house": t.natal_house_activated,
            "retrograde": t.is_retrograde,
        }
        for t in transit_data.transits
    ]
    context["major_transits"] = transit_data.major_transits
    context["transit_date"] = transit_data.target_date

    system_prompt = _render_prompt("system_prompt.md", context)
    user_prompt = _render_prompt("daily_suggestion.md", context)

    return backend.generate(system_prompt, user_prompt)
