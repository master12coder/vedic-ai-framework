"""Ayurvedic Tridosha balance computation from birth chart (Vaidya Jyotish).

Derives Vata / Pitta / Kapha constitution from planetary placements and dignity.
All weights and planet assignments loaded from knowledge/medical_rules.yaml.

Source: K.S. Charak "Ayurvedic Astrology" Ch.2;
        Classical Jyotish-Ayurveda synthesis texts.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from daivai_engine.models.chart import ChartData
from daivai_engine.models.medical import TridoshaBalance


_RULES_FILE = Path(__file__).parent.parent / "knowledge" / "medical_rules.yaml"


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    """Load medical rules YAML (cached after first call)."""
    with _RULES_FILE.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)  # type: ignore[no-any-return]


def _dignity_modifier(planet_data) -> float:  # type: ignore[no-untyped-def]
    """Return dignity-based weight modifier for tridosha scoring.

    Exalted/own planets strongly express their dosha quality;
    debilitated/combust planets suppress it.
    Source: medical_rules.yaml tridosha_dignity_modifiers.
    """
    rules = _load_rules()
    modifiers: dict[str, float] = rules["tridosha_dignity_modifiers"]

    dignity = planet_data.dignity  # exalted/mooltrikona/own/neutral/debilitated
    base = modifiers.get(dignity, 1.0)

    if planet_data.is_combust:
        base = min(base, modifiers.get("combust", 0.7))
    if planet_data.is_retrograde:
        base = max(base, modifiers.get("retrograde", 1.2))

    return base


def compute_tridosha(chart: ChartData) -> TridoshaBalance:
    """Compute Ayurvedic Tridosha balance from a birth chart.

    Algorithm:
      1. Load planet weights from medical_rules.yaml.
      2. For each planet, compute effective score = base_weight x dignity_modifier.
      3. Accumulate Vata, Pitta, Kapha totals.
      4. Convert to percentages and determine constitution type.

    Args:
        chart: Fully computed birth chart.

    Returns:
        TridoshaBalance with scores, percentages, dominant dosha, and description.
    """
    rules = _load_rules()
    weights: dict = rules["tridosha_weights"]

    vata_score = 0.0
    pitta_score = 0.0
    kapha_score = 0.0

    vata_planets: list[str] = []
    pitta_planets: list[str] = []
    kapha_planets: list[str] = []

    for dosha, config in weights.items():
        primary: dict[str, float] = config.get("primary", {})
        secondary_weights: dict[str, float] = config.get("secondary", {})

        for planet_name, base_weight in {**primary, **secondary_weights}.items():
            planet_data = chart.planets.get(planet_name)
            if planet_data is None:
                continue

            modifier = _dignity_modifier(planet_data)
            effective = base_weight * modifier

            if dosha == "vata":
                vata_score += effective
                if effective > 0 and planet_name not in vata_planets:
                    vata_planets.append(planet_name)
            elif dosha == "pitta":
                pitta_score += effective
                if effective > 0 and planet_name not in pitta_planets:
                    pitta_planets.append(planet_name)
            elif dosha == "kapha":
                kapha_score += effective
                if effective > 0 and planet_name not in kapha_planets:
                    kapha_planets.append(planet_name)

    total = vata_score + pitta_score + kapha_score
    if total == 0.0:
        total = 1.0  # Guard against division by zero

    vata_pct = round(vata_score / total * 100, 1)
    pitta_pct = round(pitta_score / total * 100, 1)
    kapha_pct = round(kapha_score / total * 100, 1)

    # Determine dominant and secondary
    scores = {"Vata": vata_score, "Pitta": pitta_score, "Kapha": kapha_score}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    dominant = ranked[0][0]
    secondary = ranked[1][0]

    # Constitution type: if top two are within 15% of total, they are dual
    # If all three are within 20% each (roughly equal) → Tridoshic
    max_score = ranked[0][1]
    secondary_score = ranked[1][1]
    third_score = ranked[2][1]

    if third_score / max_score >= 0.75:
        constitution_type = "Tridoshic"
    elif secondary_score / max_score >= 0.80:
        constitution_type = f"{dominant}-{secondary}"
    else:
        constitution_type = dominant

    # Imbalance risk: if dominant > 55% → high, 45-55% → moderate, else low
    dominant_pct = ranked[0][1] / total * 100
    if dominant_pct > 55:
        imbalance_risk = "high"
    elif dominant_pct > 45:
        imbalance_risk = "moderate"
    else:
        imbalance_risk = "low"

    description = (
        f"Constitution: {constitution_type}. "
        f"Vata {vata_pct}% (Saturn/Rahu dominant), "
        f"Pitta {pitta_pct}% (Sun/Mars/Ketu dominant), "
        f"Kapha {kapha_pct}% (Moon/Jupiter/Venus dominant). "
        f"Imbalance risk: {imbalance_risk}."
    )

    return TridoshaBalance(
        vata_score=round(vata_score, 3),
        pitta_score=round(pitta_score, 3),
        kapha_score=round(kapha_score, 3),
        vata_percentage=vata_pct,
        pitta_percentage=pitta_pct,
        kapha_percentage=kapha_pct,
        dominant_dosha=dominant,
        secondary_dosha=secondary,
        vata_planets=vata_planets,
        pitta_planets=pitta_planets,
        kapha_planets=kapha_planets,
        constitution_type=constitution_type,
        imbalance_risk=imbalance_risk,
        description=description,
    )
