"""Gem therapy core recommendation logic."""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.functional_nature import get_shadow_planet_nature
from daivai_engine.compute.gem_therapy_utils import (
    _ACTIVATION_MANTRA_COUNT,
    _ACTIVATION_STEPS,
    _UNIVERSAL_REMOVAL,
    _get_lordship_gem_recs,
    _get_special_precaution,
    _lagna_to_key,
    _map_recommendation_status,
    _universal_removal,
)
from daivai_engine.knowledge.loader import (
    load_gem_therapy_rules,
    load_gemstone_logic,
    load_lordship_rules,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.gem_therapy import (
    GemActivation,
    GemQualitySpec,
    GemTherapyRecommendation,
    GemUpratna,
)


def compute_gem_recommendation(chart: ChartData) -> list[GemTherapyRecommendation]:
    """Compute complete gem therapy recommendations for all 9 planets.

    Args:
        chart: Computed birth chart containing lagna and planetary data.

    Returns:
        List of GemTherapyRecommendation — one per planet, sorted:
        recommended → test_with_caution → neutral → prohibited.
    """
    rules = load_gem_therapy_rules()
    gem_logic = load_gemstone_logic()
    lordship = load_lordship_rules()

    lagna_sign = chart.lagna_sign  # e.g., "Gemini"
    lagna_key = _lagna_to_key(lagna_sign, rules)
    gem_recommendations = _get_lordship_gem_recs(lagna_key, lordship)

    gemstones = gem_logic.get("gemstones", {})
    quality_data = rules.get("quality_parameters", {})
    upratna_data = rules.get("upratna", {})
    activation_data = rules.get("pran_pratishtha", {}).get("per_planet_details", {})
    removal_data = rules.get("removal_conditions", {})
    planet_to_stone = rules.get("planet_to_stone", {})

    results: list[GemTherapyRecommendation] = []
    planets = list(planet_to_stone.keys())

    for planet in planets:
        stone_name = planet_to_stone.get(planet, "")
        gem_data = gemstones.get(planet, {})
        primary = gem_data.get("primary", {})
        stone_name_hi = primary.get("name_hi", stone_name)

        rec = gem_recommendations.get(planet, {})
        status = _map_recommendation_status(rec.get("recommendation", "neutral"))
        lordship_reason = rec.get("reasoning", "").strip()

        # Prohibited — skip therapy details, return minimal entry
        if status == "prohibited":
            results.append(
                GemTherapyRecommendation(
                    planet=planet,
                    stone_name=stone_name,
                    stone_name_hi=stone_name_hi,
                    status="prohibited",
                    lordship_reason=lordship_reason,
                    finger=gem_data.get("finger", ""),
                    hand=gem_data.get("hand", "Right"),
                    metal=gem_data.get("metal", ""),
                    day=gem_data.get("day", ""),
                    hora=gem_data.get("hora", ""),
                    mantra=gem_data.get("mantra", ""),
                    mantra_count=gem_data.get("mantra_count", 0) or 1,
                    weight_formula=gem_data.get("weight_formula", ""),
                    removal_conditions=_universal_removal(),
                    prohibition_reason=lordship_reason[:200]
                    if lordship_reason
                    else f"{planet} stone is prohibited for this lagna",
                )
            )
            continue

        quality = _build_quality(stone_name, quality_data)
        upratna = _build_upratna(planet, upratna_data)
        activation = _build_activation(planet, gem_data, activation_data)
        removal = _build_removal_conditions(stone_name, removal_data)
        special = _get_special_precaution(stone_name, quality_data)

        results.append(
            GemTherapyRecommendation(
                planet=planet,
                stone_name=stone_name,
                stone_name_hi=stone_name_hi,
                status=status,
                lordship_reason=lordship_reason,
                finger=gem_data.get("finger", ""),
                hand=gem_data.get("hand", "Right"),
                metal=gem_data.get("metal", ""),
                day=gem_data.get("day", ""),
                hora=gem_data.get("hora", ""),
                mantra=gem_data.get("mantra", ""),
                mantra_count=gem_data.get("mantra_count", 0) or 1,
                weight_formula=gem_data.get("weight_formula", ""),
                upratna=upratna,
                quality=quality,
                activation=activation,
                removal_conditions=removal,
                special_precaution=special,
            )
        )

    # Rashyadhipati: resolve Rahu/Ketu via sign lord's functional nature.
    # lordship_rules.yaml has no Rahu/Ketu entries, so they default to "neutral".
    # BPHS: shadow planets give results of the lord of the sign they occupy.
    results = _resolve_shadow_planets(results, chart)

    order = {"recommended": 0, "test_with_caution": 1, "neutral": 2, "prohibited": 3}
    results.sort(key=lambda r: order.get(r.status, 9))
    return results


_SAFETY_TO_STATUS = {
    "safe": "recommended",
    "test_with_caution": "test_with_caution",
    "unsafe": "prohibited",
}


def _resolve_shadow_planets(
    results: list[GemTherapyRecommendation], chart: ChartData
) -> list[GemTherapyRecommendation]:
    """Override neutral Rahu/Ketu recommendations using rashyadhipati analysis."""
    resolved: list[GemTherapyRecommendation] = []
    for rec in results:
        if rec.planet in ("Rahu", "Ketu") and rec.status == "neutral":
            shadow = get_shadow_planet_nature(rec.planet, chart)
            new_status = _SAFETY_TO_STATUS.get(shadow.gemstone_safety, "neutral")
            resolved.append(
                rec.model_copy(
                    update={
                        "status": new_status,
                        "lordship_reason": shadow.reasoning,
                    }
                )
            )
        else:
            resolved.append(rec)
    return resolved


def _build_quality(stone_name: str, quality_data: dict[str, Any]) -> GemQualitySpec | None:
    """Build GemQualitySpec from gem_therapy_rules.yaml quality_parameters."""
    q = quality_data.get(stone_name)
    if not q:
        return None
    return GemQualitySpec(
        color=q.get("color", ""),
        clarity=q.get("clarity", ""),
        min_weight_ratti=float(q.get("min_weight_ratti", 3.0)),
        min_weight_carat=float(q.get("min_weight_carat", 2.7)),
        origin_preferred=q.get("origin_preferred", []),
        origin_acceptable=q.get("origin_acceptable", []),
        avoid_if=q.get("avoid_if", []),
        treatment_caution=q.get("treatment_caution", []),
    )


def _build_upratna(planet: str, upratna_data: dict[str, Any]) -> GemUpratna | None:
    """Build GemUpratna (substitute stone) from gem_therapy_rules.yaml."""
    u = upratna_data.get(planet)
    if not u:
        return None
    return GemUpratna(
        name=u.get("substitute", ""),
        name_hi=u.get("substitute_hi", ""),
        effectiveness_percent=int(u.get("effectiveness_percent", 60)),
        when_to_prefer=u.get("when_to_prefer", []),
        color_match=u.get("color_match", ""),
        metal=u.get("metal", ""),
        caution=u.get("caution", ""),
    )


def _build_activation(
    planet: str, gem_data: dict[str, Any], activation_data: dict[str, Any]
) -> GemActivation | None:
    """Build GemActivation from per-planet activation details."""
    act = activation_data.get(planet, {})
    if not act:
        return None
    return GemActivation(
        cloth_color=act.get("cloth_color", ""),
        incense=act.get("incense", ""),
        flower=act.get("flower", ""),
        diya_type=act.get("diya_type", "Ghee lamp"),
        offering=act.get("offering", ""),
        mantra=gem_data.get("mantra", ""),
        mantra_count=_ACTIVATION_MANTRA_COUNT,
        activation_steps=_ACTIVATION_STEPS,
    )


def _build_removal_conditions(stone_name: str, removal_data: dict[str, Any]) -> list[str]:
    """Combine universal and stone-specific removal conditions."""
    conditions = list(_UNIVERSAL_REMOVAL)
    per_stone = removal_data.get("per_planet", {})
    stone_specific = per_stone.get(stone_name, [])
    conditions.extend(stone_specific)
    return conditions
