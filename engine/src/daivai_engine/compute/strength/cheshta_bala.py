"""Cheshta Bala and Drik Bala — components of Shadbala.

Cheshta Bala: Motional strength based on speed and retrogression.
Drik Bala: Aspectual strength using BPHS graduated aspect percentages.
Also includes Yuddha Bala (planetary war) adjustment.
Source: BPHS Chapter 23.
"""

from __future__ import annotations

from daivai_engine.constants import (
    ASPECT_STRENGTH_DEFAULT,
    ASPECT_STRENGTHS,
)
from daivai_engine.models.chart import ChartData


# Natural benefics and malefics
_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
_MALEFICS = {"Sun", "Mars", "Saturn"}

# Seven classical planets (Rahu/Ketu excluded from traditional Shadbala)
SHADBALA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Dig Bala best houses
_DIG_BEST: dict[str, int] = {
    "Sun": 10,
    "Mars": 10,
    "Jupiter": 1,
    "Mercury": 1,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
}


def compute_dig_bala(chart: ChartData, planet_name: str) -> float:
    """Directional strength: 60 at best house, 0 at worst (opposite)."""
    p = chart.planets[planet_name]
    best = _DIG_BEST.get(planet_name, 1)
    # House distance (circular, 1-12)
    dist = abs(p.house - best)
    if dist > 6:
        dist = 12 - dist
    return round(max(0.0, 60.0 * (1.0 - dist / 6.0)), 2)


def compute_cheshta_bala(chart: ChartData, planet_name: str) -> float:
    """Motional strength based on speed and retrogression.

    Sun and Moon always get 30 (they do not retrograde).
    Retrograde: 60, Stationary (|speed| < 0.1): 45,
    Direct & fast (|speed| > avg): 30, Direct & slow: 15.
    """
    if planet_name in ("Sun", "Moon"):
        return 30.0

    p = chart.planets[planet_name]

    if p.is_retrograde:
        return 60.0

    speed = abs(p.speed)
    if speed < 0.1:
        return 45.0  # Stationary

    # Average daily speeds for comparison (approximate)
    avg_speeds: dict[str, float] = {
        "Mars": 0.524,
        "Mercury": 1.383,
        "Jupiter": 0.083,
        "Venus": 1.2,
        "Saturn": 0.034,
        "Rahu": 0.053,
        "Ketu": 0.053,
    }
    avg = avg_speeds.get(planet_name, 0.5)
    if speed >= avg:
        return 30.0
    return 15.0


def _get_aspect_strength(planet_name: str, planet_house: int, target_house: int) -> float:
    """Return the aspect strength fraction (0.0-1.0) cast by *planet_name*.

    Uses BPHS graduated aspect strengths from ASPECT_STRENGTHS in constants:
      - All planets: 7th house = 1.0 (Poorna Drishti / full aspect)
      - Mars:    4th = 0.75, 8th = 1.0
      - Jupiter: 5th = 0.50, 9th = 1.0
      - Saturn:  3rd = 0.25, 10th = 1.0
      - Rahu/Ketu: 5th = 0.50, 9th = 1.0

    Args:
        planet_name: Name of the aspecting planet.
        planet_house: House (1-12) the planet occupies.
        target_house: House (1-12) being aspected.

    Returns:
        Strength fraction in [0.0, 1.0].
    """
    # "Nth house from planet" — 1-indexed forward count
    which = (target_house - planet_house) % 12 + 1
    strengths = ASPECT_STRENGTHS.get(planet_name, ASPECT_STRENGTH_DEFAULT)
    return strengths.get(which, 0.0)


def compute_drik_bala(chart: ChartData, planet_name: str) -> float:
    """Aspectual strength using BPHS graduated aspect percentages.

    Benefic aspects: +15 x strength_fraction
    Malefic aspects: -15 x strength_fraction
    """
    p = chart.planets[planet_name]
    target_house = p.house
    score = 0.0

    for other_name in SHADBALA_PLANETS:
        if other_name == planet_name:
            continue
        other = chart.planets[other_name]
        strength = _get_aspect_strength(other_name, other.house, target_house)
        if strength > 0.0:
            if other_name in _BENEFICS:
                score += 15.0 * strength
            elif other_name in _MALEFICS:
                score -= 15.0 * strength

    return round(score, 2)


def aspects_house(planet_name: str, planet_house: int, target_house: int) -> bool:
    """Return True if planet casts any aspect on target_house.

    Retained for backward compatibility with code that calls this directly.
    """
    return _get_aspect_strength(planet_name, planet_house, target_house) > 0.0


def compute_yuddha_bala_adjustments(chart: ChartData) -> dict[str, float]:
    """Return Yuddha Bala virupad adjustments keyed by planet name.

    Per BPHS: when two planets are within 1° of each other they are at war.
    The winner gains strength, the loser loses it (60 virupas each).
    Only Mars, Mercury, Jupiter, Venus, Saturn participate in planetary war.

    Args:
        chart: Computed birth chart.

    Returns:
        Dict mapping planet name → adjustment (positive for winner, negative for loser).
    """
    from daivai_engine.compute.graha_yuddha import detect_planetary_war

    adjustments: dict[str, float] = {}
    for war in detect_planetary_war(chart):
        adjustments[war.winner] = adjustments.get(war.winner, 0.0) + 60.0
        adjustments[war.loser] = adjustments.get(war.loser, 0.0) - 60.0
    return adjustments
