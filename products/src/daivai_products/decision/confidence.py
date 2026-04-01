"""Confidence scoring for chart analysis sections.

Assigns a 0-100 confidence score to each life-area section (career, marriage,
health, etc.) based on planetary strength, dignity, house placement, yogas,
vargottam status, and birth-time quality. Higher scores indicate more reliable
predictions for that area.

Source: BPHS Ch.27 (Shadbala minimums), BPHS Ch.16-17 (Vimshopaka thresholds),
Phala Deepika Ch.2 (dignity and combustion effects).
"""

from __future__ import annotations

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.confidence_helpers import (
    assess_birth_time,
    count_relevant_yogas,
    get_house_lord,
    get_shadbala_strong,
    get_vimshopaka_strong,
    is_dignity_strong,
    planet_in_dusthana,
    planet_in_good_house,
)
from daivai_products.decision.models import ConfidenceReport, SectionConfidence


# ── Section configuration ───────────────────────────────────────────────────
# Maps each section to: (primary_houses, karaka_planets, yoga_keywords)
# primary_houses: houses whose lord strength matters most
# karaka_planets: natural significators for this area
# yoga_keywords: substrings to match in yoga names for relevance

_SECTION_CONFIG: dict[str, tuple[list[int], list[str], list[str]]] = {
    "career": (
        [10, 2, 6, 11],
        ["Saturn", "Sun", "Mercury", "Jupiter"],
        ["raja", "dhana", "budhaditya"],
    ),
    "marriage": (
        [7, 2, 4, 8],
        ["Venus", "Jupiter", "Moon"],
        ["kalatra", "marriage", "parivartana"],
    ),
    "health": ([1, 6, 8], ["Sun", "Mars", "Saturn"], ["arishta", "viparita", "mritu"]),
    "wealth": ([2, 11, 5, 9], ["Jupiter", "Venus", "Mercury"], ["dhana", "lakshmi", "kubera"]),
    "education": (
        [4, 5, 9, 2],
        ["Jupiter", "Mercury", "Moon"],
        ["saraswati", "budhaditya", "vidya"],
    ),
    "spiritual": ([9, 12, 5], ["Jupiter", "Saturn", "Ketu"], ["moksha", "pravrajya", "vairagya"]),
    "children": ([5, 9, 7], ["Jupiter", "Venus", "Moon"], ["putra", "santana", "children"]),
    "longevity": ([1, 8, 3], ["Saturn", "Mars", "Sun"], ["arishta", "longevity", "maraka"]),
    "timing": ([1, 10, 7], ["Saturn", "Jupiter", "Sun"], ["raja", "dasha", "transit"]),
}

# Vimshopaka threshold (shodashavarga_score out of 20)
_VIMSHOPAKA_THRESHOLD = 10.0

# Section weights for overall score (career/marriage/health weighted higher)
_SECTION_WEIGHTS: dict[str, float] = {
    "career": 1.5,
    "marriage": 1.3,
    "health": 1.5,
    "wealth": 1.2,
    "education": 1.0,
    "spiritual": 0.8,
    "children": 1.0,
    "longevity": 1.2,
    "timing": 1.0,
}


def _score_section(
    analysis: FullChartAnalysis,
    section: str,
    primary_houses: list[int],
    karaka_planets: list[str],
    yoga_keywords: list[str],
    birth_penalty: int,
    vargottam_set: set[str],
) -> SectionConfidence:
    """Compute confidence score for a single life-area section."""
    score = 50
    boosters: list[str] = []
    penalties: list[str] = []
    caveats: list[str] = []
    key_planets: list[str] = list(karaka_planets)

    # --- Lagna lord strength (universal booster) ---
    lagna_lord_name = analysis.lagna_lord
    lagna_planet = analysis.chart.planets.get(lagna_lord_name)
    if lagna_planet and (is_dignity_strong(lagna_planet) or planet_in_good_house(lagna_planet)):
        score += 10
        boosters.append(
            f"Lagna lord {lagna_lord_name} strong ({lagna_planet.dignity}, house {lagna_planet.house})."
        )

    # --- Primary house lord strength ---
    for house_num in primary_houses[:2]:  # Check top 2 most relevant houses
        lord = get_house_lord(analysis, house_num)
        if lord is None:
            continue
        if lord.name not in key_planets:
            key_planets.append(lord.name)
        if is_dignity_strong(lord) or planet_in_good_house(lord):
            score += 10
            boosters.append(
                f"House {house_num} lord {lord.name} strong ({lord.dignity}, house {lord.house})."
            )
            break  # Only one house lord booster
        if planet_in_dusthana(lord):
            score -= 10
            penalties.append(
                f"House {house_num} lord {lord.name} in dusthana (house {lord.house})."
            )
            break

    # --- Supporting yogas ---
    yoga_count = count_relevant_yogas(analysis, yoga_keywords)
    yoga_boost = min(yoga_count * 5, 15)
    if yoga_boost > 0:
        score += yoga_boost
        boosters.append(f"{yoga_count} relevant yoga(s) present (+{yoga_boost}).")

    # --- Vargottam planets involved ---
    relevant_vargottam = [p for p in karaka_planets if p in vargottam_set]
    if relevant_vargottam:
        score += 5
        boosters.append(f"Vargottam: {', '.join(relevant_vargottam)}.")

    # --- Vimshopaka bala for key karaka ---
    for planet_name in karaka_planets[:2]:
        if get_vimshopaka_strong(analysis, planet_name, _VIMSHOPAKA_THRESHOLD):
            score += 5
            boosters.append(f"{planet_name} Vimshopaka above threshold.")
            break

    # --- Shadbala for key karaka ---
    for planet_name in karaka_planets[:2]:
        if get_shadbala_strong(analysis, planet_name):
            score += 5
            boosters.append(f"{planet_name} Shadbala above minimum.")
            break

    # --- Combustion penalty ---
    for planet_name in karaka_planets:
        planet = analysis.chart.planets.get(planet_name)
        if planet and planet.is_combust:
            score -= 10
            penalties.append(f"{planet_name} combust — weakened significations.")
            caveats.append(f"Combustion of {planet_name} weakens this area.")
            break  # Only one combustion penalty per section

    # --- Debilitation penalty ---
    for planet_name in karaka_planets:
        planet = analysis.chart.planets.get(planet_name)
        if planet and planet.dignity == "debilitated":
            score -= 10
            penalties.append(f"{planet_name} debilitated — reduced strength.")
            break

    # --- Malefic affliction (maraka lord aspecting/conjuncting karaka) ---
    maraka_houses = [2, 7]
    for mh in maraka_houses:
        maraka_lord = get_house_lord(analysis, mh)
        if maraka_lord is None:
            continue
        for planet_name in karaka_planets[:2]:
            planet = analysis.chart.planets.get(planet_name)
            if planet and planet.house == maraka_lord.house:
                score -= 5
                penalties.append(f"{planet_name} conjunct maraka lord {maraka_lord.name}.")
                break

    # --- Birth time penalty ---
    if birth_penalty != 0:
        score += birth_penalty  # birth_penalty is already negative

    # --- Retrograde caveat (not score-affecting, just informational) ---
    for planet_name in karaka_planets:
        planet = analysis.chart.planets.get(planet_name)
        if planet and planet.is_retrograde:
            caveats.append(f"Retrograde {planet_name} involved — results may manifest differently.")
            break

    # Clamp to [0, 100]
    score = max(0, min(100, score))

    return SectionConfidence(
        section=section,
        score=score,
        boosters=boosters,
        penalties=penalties,
        caveats=caveats,
        key_planets=key_planets[:5],
    )


def compute_confidence(analysis: FullChartAnalysis) -> ConfidenceReport:
    """Assign confidence scores (0-100) to each life-area section.

    Evaluates career, marriage, health, wealth, education, spiritual,
    children, longevity, and timing based on planetary strength, dignity,
    house placement, yogas, vargottam status, and birth-time quality.

    Args:
        analysis: Pre-computed FullChartAnalysis with all strength data.

    Returns:
        ConfidenceReport with per-section scores and overall weighted average.
    """
    birth_quality, birth_penalty, birth_caveats = assess_birth_time(analysis.chart.tob)
    vargottam_set = set(analysis.vargottam_planets)

    # Add universal caveat if no rectification data available
    all_caveats = list(birth_caveats)
    if birth_quality != "exact":
        all_caveats.append("Birth time unverified — consider KP rectification.")

    sections: list[SectionConfidence] = []
    for section, (houses, karakas, keywords) in _SECTION_CONFIG.items():
        sec = _score_section(
            analysis,
            section,
            houses,
            karakas,
            keywords,
            birth_penalty,
            vargottam_set,
        )
        sections.append(sec)

    # Weighted average for overall score
    total_weight = sum(_SECTION_WEIGHTS.get(s.section, 1.0) for s in sections)
    weighted_sum = sum(s.score * _SECTION_WEIGHTS.get(s.section, 1.0) for s in sections)
    overall = round(weighted_sum / total_weight) if total_weight > 0 else 50
    overall = max(0, min(100, overall))

    return ConfidenceReport(
        sections=sections,
        overall_score=overall,
        birth_time_quality=birth_quality,
        birth_time_caveats=all_caveats,
    )
