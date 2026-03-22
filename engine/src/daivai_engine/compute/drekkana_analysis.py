"""Drekkana (D3) Analysis for Sibling Significations.

The D3 Drekkana chart divides each sign into three 10° parts, giving
36 Drekkanas across the zodiac. Each Drekkana has:
  - A ruling planet (lord of the corresponding trine sign)
  - A classical nature (human, quadruped, serpent, mixed)
  - Specific sibling indications

Sibling analysis uses:
  1. The 3rd house and its lord in the natal chart
  2. The 3rd house and lord in the D3 chart
  3. The nature of Drekkana occupied by planets in the 3rd house

Sarpa (Serpent) Drekkanas:
  The serpent Drekkanas are those where the D3 position falls in a water
  sign (Karka, Vrischika, Meena) and the planet's natal sign is also
  water. Specifically, the 1st Drekkana of each water sign has serpentine
  energy (BPHS Ch.27).

  Additional Sarpa Drekkanas (from Parashara): 2nd decanate of Mesha,
  1st decanate of Karka, 2nd decanate of Vrischika, 1st decanate of Meena.

Sources: BPHS Ch.27 (Drekkana Sphutha), Ch.12 (Bhratru Bhava),
         Phaladeepika Ch.18, Saravali Ch.41.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import compute_drekkana_sign
from daivai_engine.compute.drekkana_tables import (
    _DREKKANA_NAMES,
    _DREKKANA_NATURE,
    _NATURE_SIBLING_INDICATION,
    DrekkanaAnalysisResult,
    DrekkanaPosition,
    SiblingAnalysis,
)
from daivai_engine.constants import SIGN_LORDS, SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData


__all__ = [
    "DrekkanaAnalysisResult",
    "DrekkanaPosition",
    "SiblingAnalysis",
    "compute_drekkana_analysis",
    "get_drekkana_position",
]


def compute_drekkana_analysis(chart: ChartData) -> DrekkanaAnalysisResult:
    """Compute full Drekkana (D3) analysis with sibling significations.

    Steps:
    1. Compute D3 position for each planet
    2. Classify each Drekkana (nature, name, Sarpa status)
    3. Analyze 3rd house for sibling indications

    Args:
        chart: Natal birth chart.

    Returns:
        DrekkanaAnalysisResult with all D3 positions and sibling analysis.
    """
    positions: list[DrekkanaPosition] = []
    sarpa_planets: list[str] = []

    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for name in planets:
        p = chart.planets[name]
        pos = _compute_planet_drekkana(name, p.longitude, p.sign_index, p.degree_in_sign)
        positions.append(pos)
        if pos.is_sarpa_drekkana:
            sarpa_planets.append(name)

    sibling = _compute_sibling_analysis(chart, positions)

    return DrekkanaAnalysisResult(
        all_positions=positions,
        sibling_analysis=sibling,
        sarpa_drekkana_planets=sarpa_planets,
    )


def get_drekkana_position(longitude: float, planet_name: str = "") -> DrekkanaPosition:
    """Compute Drekkana position for any longitude.

    Useful for computing the Drekkana of lagna or any point.

    Args:
        longitude: Sidereal longitude (0-360).
        planet_name: Optional label.

    Returns:
        DrekkanaPosition with all classical attributes.
    """
    sign_index = int(longitude / 30.0)
    degree_in_sign = longitude - sign_index * 30.0
    return _compute_planet_drekkana(planet_name or "Point", longitude, sign_index, degree_in_sign)


# ── Private helpers ────────────────────────────────────────────────────────


def _compute_planet_drekkana(
    name: str,
    longitude: float,
    sign_index: int,
    degree_in_sign: float,
) -> DrekkanaPosition:
    """Compute Drekkana position for a single planet."""
    part = int(degree_in_sign / 10.0)
    if part > 2:
        part = 2

    d3_sign_idx = compute_drekkana_sign(longitude)
    d3_lord = SIGN_LORDS[d3_sign_idx]
    nature = _DREKKANA_NATURE.get((sign_index, part), "human")
    drek_name = _DREKKANA_NAMES.get(
        (sign_index, part), f"Drekkana {part + 1} of {SIGNS[sign_index]}"
    )
    is_sarpa = _is_sarpa_drekkana(sign_index, part, d3_sign_idx)

    return DrekkanaPosition(
        planet=name,
        natal_sign_index=sign_index,
        natal_sign=SIGNS[sign_index],
        natal_degree=round(degree_in_sign, 4),
        drekkana_part=part,
        d3_sign_index=d3_sign_idx,
        d3_sign=SIGNS[d3_sign_idx],
        d3_sign_en=SIGNS_EN[d3_sign_idx],
        d3_lord=d3_lord,
        drekkana_name=drek_name,
        nature=nature,
        is_sarpa_drekkana=is_sarpa,
        sibling_indication=_NATURE_SIBLING_INDICATION.get(nature, ""),
    )


def _is_sarpa_drekkana(sign_index: int, part: int, d3_sign_idx: int) -> bool:
    """Determine if a Drekkana is a Sarpa (serpent) Drekkana.

    Sarpa Drekkanas per BPHS Ch.27:
    - First Drekkana of each water sign (Karka/3, Vrischika/7, Meena/11)
    - Second Drekkana of Mesha (0, part 1)
    - First and second Drekkana of Vrischika (7, parts 0 and 1)
    - First Drekkana of Meena (11, part 0)
    """
    sarpa_set: set[tuple[int, int]] = {
        (0, 1),  # Mesha 2nd Drekkana
        (2, 2),  # Mithuna 3rd Drekkana
        (3, 0),  # Karka 1st Drekkana (primary water sign Sarpa)
        (7, 0),  # Vrischika 1st Drekkana (primary water sign Sarpa)
        (7, 1),  # Vrischika 2nd Drekkana
        (11, 0),  # Meena 1st Drekkana (primary water sign Sarpa)
    }
    return (sign_index, part) in sarpa_set


def _compute_sibling_analysis(
    chart: ChartData,
    positions: list[DrekkanaPosition],
) -> SiblingAnalysis:
    """Compute sibling-related analysis from natal + D3 chart."""
    # 3rd house lord
    lagna_idx = chart.lagna_sign_index
    third_house_sign = (lagna_idx + 2) % 12
    third_lord = SIGN_LORDS[third_house_sign]

    # Planets in 3rd house (natal)
    third_occupants = [name for name, p in chart.planets.items() if p.house == 3]

    # D3 positions map: planet → d3_sign_index
    d3_map = {pos.planet: pos.d3_sign_index for pos in positions}

    # 3rd lord's D3 position
    third_lord_d3_idx = d3_map.get(third_lord, third_house_sign)
    third_lord_d3_sign = SIGNS[third_lord_d3_idx]

    # D3 third house: count from D3 lagna (if lagna in D3 were available)
    # Use natal lagna D3 as reference
    lagna_lon = chart.lagna_longitude
    lagna_d3_sign = compute_drekkana_sign(lagna_lon)
    d3_third_sign = (lagna_d3_sign + 2) % 12
    d3_third_occupants = [pos.planet for pos in positions if pos.d3_sign_index == d3_third_sign]

    # Check Sarpa in 3rd-house planets' Drekkanas
    third_house_drekkanas = {pos.planet: pos for pos in positions if pos.planet in third_occupants}
    has_sarpa = any(pos.is_sarpa_drekkana for pos in third_house_drekkanas.values())

    # Sibling count indication (rough — from number of planets in 3rd + significations)
    count_ind = _estimate_sibling_count(len(third_occupants), third_lord, chart)

    # Nature from 3rd house drekkanas
    natures = [pos.nature for pos in third_house_drekkanas.values()]
    dominant_nature = max(set(natures), key=natures.count) if natures else "human"
    sibling_nature = _NATURE_SIBLING_INDICATION.get(
        dominant_nature, "Standard sibling relationship."
    )

    # Strength of 3rd house
    strength = _assess_third_house_strength(chart, third_lord)

    return SiblingAnalysis(
        third_house_lord=third_lord,
        third_house_lord_d3_sign=third_lord_d3_sign,
        third_house_occupants=third_occupants,
        d3_third_house_occupants=d3_third_occupants,
        sibling_count_indication=count_ind,
        sibling_nature=sibling_nature,
        has_sarpa_drekkana=has_sarpa,
        strength=strength,
    )


def _estimate_sibling_count(
    occupant_count: int,
    third_lord: str,
    chart: ChartData,
) -> str:
    """Rough sibling count from 3rd house indicators."""
    # Classic rule: number of planets aspecting/occupying 3rd house suggests siblings
    third_lord_planet = chart.planets.get(third_lord)
    if third_lord_planet and third_lord_planet.dignity in ("exalted", "own", "mooltrikona"):
        base = "Multiple siblings indicated (3rd lord strong)."
    elif third_lord_planet and third_lord_planet.dignity == "debilitated":
        base = "Few or no siblings, or estrangement (3rd lord debilitated)."
    elif occupant_count == 0:
        base = "Average sibling count; no planets in 3rd house."
    elif occupant_count == 1:
        base = "One or two siblings indicated."
    else:
        base = f"Several siblings possible ({occupant_count} planets in 3rd house)."
    return base


def _assess_third_house_strength(chart: ChartData, third_lord: str) -> str:
    """Assess strength of 3rd house for sibling matters."""
    third_lord_planet = chart.planets.get(third_lord)
    if not third_lord_planet:
        return "moderate"

    if third_lord_planet.dignity in ("exalted", "own", "mooltrikona"):
        return "strong"
    if third_lord_planet.dignity == "debilitated" or third_lord_planet.is_combust:
        return "weak"
    return "moderate"
