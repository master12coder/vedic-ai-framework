"""Gem therapy computation — professional-grade Vedic gem therapy engine.

Computes complete gemstone recommendations including:
- Lordship-based stone selection per lagna
- Wearing protocol: finger, metal, day, nakshatra, mantra
- Weight formula per body weight
- Substitute (upratna) and quality specifications
- Pran Pratishtha (activation ritual) data
- Contraindication matrix (which gems must never be worn together)
- Auspicious wearing muhurta computation using Panchang

All computation stays in engine/ — zero AI, zero product imports.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from daivai_engine.compute.panchang import compute_panchang
from daivai_engine.knowledge.loader import (
    load_gem_therapy_rules,
    load_gemstone_logic,
    load_lordship_rules,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.gem_therapy import (
    ContraindicationPair,
    ContraindicationResult,
    GemActivation,
    GemQualitySpec,
    GemTherapyRecommendation,
    GemUpratna,
    WearingMuhurta,
)


# ── Activation mantra count (for Pran Pratishtha ritual) ────────────────────
_ACTIVATION_MANTRA_COUNT = 108  # Standard for all planets

# ── Activation steps (common to all planets) ─────────────────────────────────
_ACTIVATION_STEPS = [
    "Purchase stone on planet's auspicious weekday",
    "Set in prescribed metal with stone touching the skin",
    "Wake before sunrise on wearing day and take a purifying bath",
    "Place ring on raw rice on a clean coloured cloth",
    "Light ghee lamp (diya) and incense appropriate to the planet",
    "Purify with panchamrit (milk, curd, honey, ghee, sugar) and wash with Gangajal",
    "Chant the planet's Vedic mantra the prescribed number of times",
    "Wear on the specified finger during the planet's hora",
    "Touch ring to forehead and offer a prayer of intention",
]

# ── Universal removal conditions ────────────────────────────────────────────
_UNIVERSAL_REMOVAL = [
    "If the stone develops a crack or chip",
    "If the stone's color changes dramatically or becomes cloudy",
    "If severe negative events occur within 3-7 days of wearing",
    "If persistent bad dreams occur for 3 or more consecutive nights",
    "If unexplained physical discomfort appears at the finger",
    "During surgery — remove all metals and stones",
    "After the planet's recommended wearing period (typically 3-7 years)",
]


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

    order = {"recommended": 0, "test_with_caution": 1, "neutral": 2, "prohibited": 3}
    results.sort(key=lambda r: order.get(r.status, 9))
    return results


def check_gem_contraindications(gems: list[str]) -> ContraindicationResult:
    """Check a list of gems (stone names or planet names) for contraindications.

    Args:
        gems: List of stone names (e.g., ["Emerald", "Yellow Sapphire"]) or
              planet names (e.g., ["Mercury", "Jupiter"]).

    Returns:
        ContraindicationResult with all conflicting pairs and safe combinations.
    """
    rules = load_gem_therapy_rules()
    stone_to_planet = rules.get("stone_to_planet", {})
    planet_to_stone = rules.get("planet_to_stone", {})
    pairs_data: list[dict[str, Any]] = rules.get("contraindication_pairs", [])

    # Normalize all inputs to stone names
    normalized: list[str] = []
    for gem in gems:
        if gem in planet_to_stone:
            normalized.append(planet_to_stone[gem])
        elif gem in stone_to_planet:
            normalized.append(gem)
        else:
            normalized.append(gem)

    conflicts: list[ContraindicationPair] = []
    safe_pairs: list[tuple[str, str]] = []

    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            stone_a = normalized[i]
            stone_b = normalized[j]
            conflict = _find_conflict(
                stone_a, stone_b, pairs_data, stone_to_planet, planet_to_stone
            )
            if conflict:
                conflicts.append(conflict)
            else:
                safe_pairs.append((stone_a, stone_b))

    has_absolute = any(c.severity == "absolute" for c in conflicts)
    summary = _build_contraindication_summary(conflicts, normalized)

    return ContraindicationResult(
        gems_checked=normalized,
        conflicts=conflicts,
        safe_pairs=safe_pairs,
        has_absolute_conflict=has_absolute,
        summary=summary,
    )


def compute_wearing_muhurta(
    gem_or_planet: str,
    birth_chart: ChartData,
    start_date: datetime,
    days_to_scan: int = 60,
    max_results: int = 5,
) -> list[WearingMuhurta]:
    """Find auspicious dates for wearing a specific gemstone.

    Scans panchang from start_date for days where:
    - Weekday matches the planet's auspicious day
    - Nakshatra is favorable for the planet
    - Tithi is auspicious (not 4th, 8th, 14th, Amavasya)

    Args:
        gem_or_planet: Stone name (e.g., "Emerald") or planet (e.g., "Mercury").
        birth_chart: Native's birth chart (provides location for panchang).
        start_date: Earliest date to consider.
        days_to_scan: How many days forward to scan (default 60).
        max_results: Maximum number of auspicious dates to return.

    Returns:
        List of WearingMuhurta sorted by score (most auspicious first).
    """
    rules = load_gem_therapy_rules()
    gem_logic = load_gemstone_logic()
    stone_to_planet = rules.get("stone_to_planet", {})
    planet_to_stone = rules.get("planet_to_stone", {})
    wearing_naks = rules.get("wearing_nakshatras", {})
    unfavorable_tithis = set(rules.get("unfavorable_tithis", {}).get("indices", [4, 8, 14, 15, 29]))
    gemstones = gem_logic.get("gemstones", {})

    # Resolve planet name
    if gem_or_planet in planet_to_stone:
        planet = gem_or_planet
        stone_name = planet_to_stone[planet]
    elif gem_or_planet in stone_to_planet:
        planet = stone_to_planet[gem_or_planet]
        stone_name = gem_or_planet
    else:
        planet = gem_or_planet
        stone_name = planet_to_stone.get(planet, gem_or_planet)

    gem_data = gemstones.get(planet, {})
    planet_day = gem_data.get("day", "")  # e.g., "Sunday"
    hora_str = gem_data.get("hora", "")

    nak_data = wearing_naks.get(planet, {})
    primary_naks: set[str] = set(nak_data.get("primary", []))
    secondary_naks: set[str] = set(nak_data.get("secondary", []))

    is_blue_sapphire = stone_name == "Blue Sapphire"

    lat = birth_chart.latitude
    lon = birth_chart.longitude
    tz = birth_chart.timezone_name

    candidates: list[WearingMuhurta] = []
    current = start_date.replace(hour=12, minute=0, second=0, microsecond=0)

    for _ in range(days_to_scan):
        date_str = current.strftime("%d/%m/%Y")
        try:
            panchang = compute_panchang(date_str, lat, lon, tz)
        except Exception:
            current += timedelta(days=1)
            continue

        score, reasons = _score_muhurta(
            panchang, planet_day, primary_naks, secondary_naks, unfavorable_tithis
        )

        if score > 0:
            candidates.append(
                WearingMuhurta(
                    date=date_str,
                    vara=panchang.vara,
                    nakshatra=panchang.nakshatra_name,
                    tithi_name=panchang.tithi_name,
                    paksha=panchang.paksha,
                    score=round(score, 2),
                    reasons=reasons,
                    hora_timing=hora_str or f"{planet} hora after sunrise on {planet_day}",
                    is_trial_date=is_blue_sapphire,
                )
            )

        current += timedelta(days=1)

    candidates.sort(key=lambda m: m.score, reverse=True)
    return candidates[:max_results]


# ── Private helpers ──────────────────────────────────────────────────────────


def _lagna_to_key(lagna_sign: str, rules: dict[str, Any]) -> str:
    """Convert lagna sign name to knowledge key (e.g., 'Gemini' → 'mithuna')."""
    mapping: dict[str, str] = rules.get("lagna_sign_to_key", {})
    return mapping.get(lagna_sign, lagna_sign.lower())


def _get_lordship_gem_recs(lagna_key: str, lordship: dict[str, Any]) -> dict[str, Any]:
    """Extract gemstone_recommendations for the given lagna from lordship_rules."""
    lagnas: dict[str, Any] = lordship.get("lagnas", {})
    lagna_data: dict[str, Any] = lagnas.get(lagna_key, {})
    result: dict[str, Any] = lagna_data.get("gemstone_recommendations", {})
    return result


def _map_recommendation_status(recommendation: str) -> str:
    """Map lordship_rules.yaml recommendation values to canonical status strings."""
    mapping = {
        "wear": "recommended",
        "recommended": "recommended",
        "test": "test_with_caution",
        "test_with_caution": "test_with_caution",
        "avoid": "prohibited",
        "prohibited": "prohibited",
        "neutral": "neutral",
    }
    return mapping.get(recommendation.lower(), "neutral")


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


def _universal_removal() -> list[str]:
    """Return universal gem removal conditions."""
    return list(_UNIVERSAL_REMOVAL)


def _get_special_precaution(stone_name: str, quality_data: dict[str, Any]) -> str | None:
    """Return special_precaution string if one exists for this stone."""
    q = quality_data.get(stone_name, {})
    return q.get("special_precaution") or None


def _find_conflict(
    stone_a: str,
    stone_b: str,
    pairs_data: list[dict[str, Any]],
    stone_to_planet: dict[str, str],
    planet_to_stone: dict[str, str],
) -> ContraindicationPair | None:
    """Check if two stones have a contraindication pair entry."""
    planet_a = stone_to_planet.get(stone_a, stone_a)
    planet_b = stone_to_planet.get(stone_b, stone_b)

    for pair in pairs_data:
        pair_planets: list[str] = pair.get("planets", [])
        if set(pair_planets) == {planet_a, planet_b}:
            return ContraindicationPair(
                planets=pair_planets,
                stones=pair.get("stones", [stone_a, stone_b]),
                severity=pair.get("severity", "moderate"),
                reason=pair.get("reason", "").strip(),
            )
    return None


def _score_muhurta(
    panchang: Any,
    planet_day: str,
    primary_naks: set[str],
    secondary_naks: set[str],
    unfavorable_tithis: set[int],
) -> tuple[float, list[str]]:
    """Score a panchang day for gem wearing auspiciousness.

    Returns (score, reasons). Score ≤ 0 means skip this day.
    """
    score = 0.0
    reasons: list[str] = []

    # Day match is mandatory for primary consideration
    if panchang.vara == planet_day:
        score += 3.0
        reasons.append(f"Auspicious day: {planet_day}")
    else:
        # Day mismatch — still score if nakshatra is exceptionally good
        score -= 1.0

    # Nakshatra scoring
    if panchang.nakshatra_name in primary_naks:
        score += 2.0
        reasons.append(f"Primary nakshatra: {panchang.nakshatra_name}")
    elif panchang.nakshatra_name in secondary_naks:
        score += 1.0
        reasons.append(f"Secondary nakshatra: {panchang.nakshatra_name}")

    # Tithi scoring (1-indexed; panchang tithi_index is 0-indexed)
    tithi_1indexed = panchang.tithi_index + 1
    if tithi_1indexed in unfavorable_tithis:
        score -= 2.5
        reasons.append(f"Unfavorable tithi: {panchang.tithi_name}")
    else:
        score += 0.5
        reasons.append(f"Acceptable tithi: {panchang.tithi_name}")

    # Paksha — Shukla (waxing) preferred
    if panchang.paksha == "Shukla":
        score += 0.5
        reasons.append("Shukla paksha (waxing moon) — auspicious")

    return score, reasons


def _build_contraindication_summary(conflicts: list[ContraindicationPair], gems: list[str]) -> str:
    """Build human-readable summary of contraindication check."""
    if not conflicts:
        return f"No contraindications found among: {', '.join(gems)}. Safe to wear together."
    absolutes = [c for c in conflicts if c.severity == "absolute"]
    if absolutes:
        stone_pairs = [f"{c.stones[0]} + {c.stones[1]}" for c in absolutes]
        return (
            f"CRITICAL: {len(absolutes)} absolute conflict(s) found — "
            f"{'; '.join(stone_pairs)}. These combinations must NEVER be worn together."
        )
    highs = [c for c in conflicts if c.severity == "high"]
    if highs:
        stone_pairs = [f"{c.stones[0]} + {c.stones[1]}" for c in highs]
        return f"High-severity conflict(s): {'; '.join(stone_pairs)}. Strongly advised against."
    stone_pairs = [f"{c.stones[0]} + {c.stones[1]}" for c in conflicts]
    return f"Moderate conflict(s) found: {'; '.join(stone_pairs)}. Consult astrologer before wearing together."
