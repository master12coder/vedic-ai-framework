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

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.compute.divisional import compute_drekkana_sign
from daivai_engine.constants import SIGN_LORDS, SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData


# Nature classification for each of the 36 Drekkanas
# Indexed as (sign_index, part): 0=first 10°, 1=second 10°, 2=third 10°
# Nature: "human" / "quadruped" / "serpent" / "mixed"
# Source: BPHS Ch.27 v1-36 (Drekkana forms), Saravali commentary
_DREKKANA_NATURE: dict[tuple[int, int], str] = {
    # Mesha (0)
    (0, 0): "human",  # 1st: male with weapon (Agni)
    (0, 1): "serpent",  # 2nd: serpentine Naga form
    (0, 2): "human",  # 3rd: woman on throne
    # Vrishabha (1)
    (1, 0): "human",  # 1st: farmer/cultivator
    (1, 1): "serpent",  # 2nd: serpent form
    (1, 2): "quadruped",  # 3rd: bull form
    # Mithuna (2)
    (2, 0): "human",  # 1st: couple (man+woman)
    (2, 1): "human",  # 2nd: woman playing veena
    (2, 2): "serpent",  # 3rd: serpent/Naga (commonly cited)
    # Karka (3)
    (3, 0): "serpent",  # 1st: serpent/crab (water sign Sarpa)
    (3, 1): "human",  # 2nd: woman with flowers
    (3, 2): "human",  # 3rd: horse rider
    # Simha (4)
    (4, 0): "quadruped",  # 1st: lion
    (4, 1): "human",  # 2nd: man in forest
    (4, 2): "quadruped",  # 3rd: elephant
    # Kanya (5)
    (5, 0): "human",  # 1st: woman
    (5, 1): "human",  # 2nd: man with bow
    (5, 2): "human",  # 3rd: man with scales
    # Tula (6)
    (6, 0): "human",  # 1st: merchant with scales
    (6, 1): "human",  # 2nd: vulture / eagle form
    (6, 2): "human",  # 3rd: man with armor
    # Vrischika (7)
    (7, 0): "serpent",  # 1st: serpent (water sign Sarpa)
    (7, 1): "serpent",  # 2nd: scorpion/serpent form
    (7, 2): "human",  # 3rd: woman with lotus
    # Dhanu (8)
    (8, 0): "human",  # 1st: archer on horseback
    (8, 1): "quadruped",  # 2nd: horse form
    (8, 2): "human",  # 3rd: man with gold ornaments
    # Makara (9)
    (9, 0): "mixed",  # 1st: half animal / Makara (sea creature)
    (9, 1): "human",  # 2nd: woman adorned
    (9, 2): "quadruped",  # 3rd: goat form
    # Kumbha (10)
    (10, 0): "human",  # 1st: man with pot
    (10, 1): "human",  # 2nd: woman
    (10, 2): "human",  # 3rd: man with chains (karma)
    # Meena (11)
    (11, 0): "serpent",  # 1st: serpent/fish (water sign Sarpa)
    (11, 1): "human",  # 2nd: man swimming
    (11, 2): "mixed",  # 3rd: fish form
}

# Drekkana classical names (partial — most notable ones)
# From Parashara's 36-Drekkana descriptions
_DREKKANA_NAMES: dict[tuple[int, int], str] = {
    (0, 0): "Agni Drekkana",
    (0, 1): "Naga Drekkana",
    (0, 2): "Yaksha Drekkana",
    (1, 0): "Bhumi Drekkana",
    (1, 1): "Sarpa Drekkana",
    (1, 2): "Vrisha Drekkana",
    (2, 0): "Mithuna Drekkana",
    (2, 1): "Vana Drekkana",
    (2, 2): "Naga Drekkana",
    (3, 0): "Sarpa Drekkana",
    (3, 1): "Jala Drekkana",
    (3, 2): "Vaja Drekkana",
    (4, 0): "Simha Drekkana",
    (4, 1): "Aranya Drekkana",
    (4, 2): "Gaja Drekkana",
    (5, 0): "Kanya Drekkana",
    (5, 1): "Dhanu Drekkana",
    (5, 2): "Tula Drekkana",
    (6, 0): "Vanija Drekkana",
    (6, 1): "Shyena Drekkana",
    (6, 2): "Kavachi Drekkana",
    (7, 0): "Sarpa Drekkana",
    (7, 1): "Vrishchika Drekkana",
    (7, 2): "Padma Drekkana",
    (8, 0): "Chakra Drekkana",
    (8, 1): "Turaga Drekkana",
    (8, 2): "Swarna Drekkana",
    (9, 0): "Makara Drekkana",
    (9, 1): "Nari Drekkana",
    (9, 2): "Chaga Drekkana",
    (10, 0): "Kumbha Drekkana",
    (10, 1): "Jala Drekkana",
    (10, 2): "Bandha Drekkana",
    (11, 0): "Sarpa Drekkana",
    (11, 1): "Jala Drekkana",
    (11, 2): "Matsya Drekkana",
}

# Sibling indication per Drekkana nature
_NATURE_SIBLING_INDICATION: dict[str, str] = {
    "human": "Strong human qualities in sibling; intellectual or artistic nature.",
    "quadruped": "Sibling may be sturdy, hardworking, connected to land/animals.",
    "serpent": "Complex sibling relationship; secrecy or hidden aspects; possible estrangement.",
    "mixed": "Mixed relationship; sibling has dual nature or unconventional path.",
}


class DrekkanaPosition(BaseModel):
    """A planet's Drekkana (D3) position with classical attributes."""

    model_config = ConfigDict(frozen=True)

    planet: str
    natal_sign_index: int = Field(ge=0, le=11)
    natal_sign: str
    natal_degree: float
    drekkana_part: int = Field(ge=0, le=2)  # 0=first 10°, 1=second 10°, 2=third 10°
    d3_sign_index: int = Field(ge=0, le=11)
    d3_sign: str
    d3_sign_en: str
    d3_lord: str  # Lord of the D3 sign
    drekkana_name: str  # Classical name
    nature: str  # human/quadruped/serpent/mixed
    is_sarpa_drekkana: bool
    sibling_indication: str


class SiblingAnalysis(BaseModel):
    """3rd-house and D3-based sibling analysis."""

    model_config = ConfigDict(frozen=True)

    third_house_lord: str  # Lord of 3rd house in natal chart
    third_house_lord_d3_sign: str  # Where 3rd lord is in D3
    third_house_occupants: list[str]  # Planets in 3rd house (natal)
    d3_third_house_occupants: list[str]  # Planets in 3rd in D3
    sibling_count_indication: str  # Based on 3rd house indicators
    sibling_nature: str  # From drekkana analysis
    has_sarpa_drekkana: bool  # Any planet in 3rd in Sarpa Drekkana
    strength: str  # strong/moderate/weak (for sibling matters)


class DrekkanaAnalysisResult(BaseModel):
    """Complete D3 Drekkana analysis for all planets."""

    model_config = ConfigDict(frozen=True)

    all_positions: list[DrekkanaPosition]
    sibling_analysis: SiblingAnalysis
    sarpa_drekkana_planets: list[str]  # Planets in Sarpa Drekkanas


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
