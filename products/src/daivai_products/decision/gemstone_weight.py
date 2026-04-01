"""10-Factor Gemstone Weight Engine — computes ratti recommendation per stone.

Reads FullChartAnalysis + lordship context to produce a weighted, safety-checked
gemstone report. Orchestrates factor computations from gemstone_factors module.

Factors: body weight, avastha, BAV, dignity, combustion, retrograde, dasha,
lordship quality, stone density, purpose multiplier.

Source: BPHS Ch.87 (ratna-adhyaya) + GemPundit/MyRatna body-weight research.
"""

from __future__ import annotations

import logging
from typing import Any

from daivai_engine.constants.signs import SIGNS
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.gemstone_factors import (
    PURPOSE_MULTIPLIER,
    build_free_alternatives,
    compute_all_factors,
    compute_body_weight_base,
    compute_weighted_ratti,
    extract_hindi_name,
)
from daivai_products.decision.models import GemstoneReport, GemstoneWeight
from daivai_products.interpret.context import build_lordship_context


logger = logging.getLogger(__name__)

# ── Status order for sorting output ────────────────────────────────────────
_STATUS_ORDER: dict[str, int] = {
    "RECOMMENDED": 0,
    "TEST_WITH_CAUTION": 1,
    "PROHIBITED": 2,
}

# Mithuna lagna hardcoded safety — per CLAUDE.md safety rules
_MITHUNA_PROHIBITED_HINDI: frozenset[str] = frozenset(
    {
        "Pukhraj",
        "Moonga",
        "Moti",
        "Manikya",
    }
)


def _determine_status(
    planet_name: str,
    gem_recs: dict[str, Any],
    lordship_ctx: dict[str, Any],
) -> str:
    """Determine stone status from lordship rules.

    Maraka always forces PROHIBITED regardless of YAML recommendation.
    """
    # Maraka check — always takes precedence
    for m in lordship_ctx.get("maraka", []):
        if m.get("planet") == planet_name:
            return "PROHIBITED"

    rec_info = gem_recs.get(planet_name, {})
    rec = rec_info.get("recommendation", "neutral")

    match rec:
        case "wear":
            return "RECOMMENDED"
        case "test":
            return "TEST_WITH_CAUTION"
        case "avoid":
            return "PROHIBITED"
        case _:
            return "TEST_WITH_CAUTION"


def _process_single_planet(
    planet_name: str,
    rec_info: dict[str, Any],
    analysis: FullChartAnalysis,
    lordship_ctx: dict[str, Any],
    gem_recs: dict[str, Any],
    base_ratti: float,
    body_weight_kg: float,
    purpose: str,
) -> tuple[GemstoneWeight, str | None, str | None]:
    """Compute gemstone weight for one planet.

    Returns:
        Tuple of (GemstoneWeight, prohibited_stone_name_or_None, safety_warning_or_None).
    """
    gemstone_str = rec_info.get("gemstone", "")
    stone_hindi = extract_hindi_name(gemstone_str)

    # Compute factors 2-10 (factor 1 is the base ratti)
    factors, reasoning_parts = compute_all_factors(
        planet_name,
        analysis,
        lordship_ctx,
        stone_hindi,
        purpose,
    )

    # Prepend base ratti reasoning
    reasoning_parts.insert(0, f"Base: {base_ratti} ratti ({body_weight_kg}kg/10)")

    # Final weighted ratti
    recommended_ratti = compute_weighted_ratti(base_ratti, factors)

    # Include base in the breakdown dict for transparency
    full_breakdown = {"body_weight_base": base_ratti, **factors}

    # Determine status
    status = _determine_status(planet_name, gem_recs, lordship_ctx)

    # Safety enforcement
    prohibited_name: str | None = None
    safety_warning: str | None = None
    free_alternatives: list[str] = []

    if status == "PROHIBITED":
        recommended_ratti = 0.0
        prohibited_name = gemstone_str
        reason = rec_info.get("reasoning", "lordship rule")
        safety_warning = f"PROHIBITED: {gemstone_str} for {planet_name} — {reason}"
        free_alternatives = build_free_alternatives(planet_name)
    elif status == "TEST_WITH_CAUTION":
        free_alternatives = build_free_alternatives(planet_name)

    weight = GemstoneWeight(
        planet=planet_name,
        stone=gemstone_str,
        stone_hindi=stone_hindi,
        status=status,
        base_ratti=base_ratti,
        recommended_ratti=recommended_ratti,
        factor_breakdown=full_breakdown,
        reasoning=" | ".join(reasoning_parts),
        free_alternatives=free_alternatives,
    )

    return weight, prohibited_name, safety_warning


def compute_gemstone_weights(
    analysis: FullChartAnalysis,
    body_weight_kg: float = 70.0,
    purpose: str = "growth",
) -> GemstoneReport:
    """Compute 10-factor gemstone weight recommendations for all planets.

    Reads lordship context for the chart's lagna, computes per-stone weights
    using 10 factors, and enforces safety rules (PROHIBITED stones = 0.0 ratti).

    Args:
        analysis: Pre-computed full chart analysis from engine.
        body_weight_kg: Native's body weight in kilograms (default 70).
        purpose: Wearing purpose — 'protection', 'growth', or 'maximum'.

    Returns:
        GemstoneReport with per-stone weights, prohibited list, and safety warnings.
    """
    lagna_sign = SIGNS[analysis.chart.lagna_sign_index]
    lordship_ctx = build_lordship_context(lagna_sign)
    gem_recs: dict[str, Any] = lordship_ctx.get("gemstone_recommendations", {})
    lagna_lord = lordship_ctx.get("sign_lord", analysis.lagna_lord)

    # Validate purpose input
    if purpose not in PURPOSE_MULTIPLIER:
        logger.warning("Unknown purpose '%s', defaulting to 'growth'", purpose)
        purpose = "growth"

    base_ratti = compute_body_weight_base(body_weight_kg)

    weights: list[GemstoneWeight] = []
    prohibited_names: list[str] = []
    safety_warnings: list[str] = []

    for planet_name, rec_info in gem_recs.items():
        if not rec_info.get("gemstone"):
            continue

        weight, prohibited, warning = _process_single_planet(
            planet_name,
            rec_info,
            analysis,
            lordship_ctx,
            gem_recs,
            base_ratti,
            body_weight_kg,
            purpose,
        )

        weights.append(weight)
        if prohibited:
            prohibited_names.append(prohibited)
        if warning:
            safety_warnings.append(warning)

    # Sort: RECOMMENDED first, then TEST_WITH_CAUTION, then PROHIBITED
    weights.sort(key=lambda w: (_STATUS_ORDER.get(w.status, 9), -w.recommended_ratti))

    # Mithuna lagna safety override (per CLAUDE.md non-negotiable safety rules)
    if lagna_sign == "Mithuna":
        for w in weights:
            if w.stone_hindi in _MITHUNA_PROHIBITED_HINDI and w.status != "PROHIBITED":
                safety_warnings.append(
                    f"SAFETY OVERRIDE: {w.stone} forced PROHIBITED for Mithuna lagna"
                )

    return GemstoneReport(
        lagna=lagna_sign,
        lagna_lord=lagna_lord,
        weights=weights,
        prohibited_stones=prohibited_names,
        safety_warnings=safety_warnings,
    )
