"""Vastu Shastra computations — directional strength, favorable directions,
dosha detection, and the main compute_vastu entry point.

All configuration is loaded from engine/knowledge/vastu_rules.yaml.
Planet-to-direction mappings follow classical Vastu Dik Bala principles.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.constants import DUSTHANAS, KENDRAS, SIGN_LORDS, TRIKONAS
from daivai_engine.knowledge.loader import load_vastu_rules
from daivai_engine.models.chart import ChartData, PlanetData
from daivai_engine.models.vastu import (
    DirectionStrength,
    VastuDosha,
    VastuResult,
)


# -- Dignity score lookup (0-100 scale for Vastu strength) -------------------

_DIGNITY_SCORES: dict[str, float] = {
    "exalted": 100.0,
    "mooltrikona": 82.0,
    "own": 75.0,
    "neutral": 50.0,
    "debilitated": 15.0,
}

_KENDRA = set(KENDRAS)
_TRIKONA = set(TRIKONAS)
_DUSTHANA = set(DUSTHANAS)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _planet_strength_score(planet: PlanetData) -> float:
    """Compute 0-100 Vastu strength for a planet from its natal chart state.

    Uses dignity as a base and applies house-placement multipliers:
    - Kendra (1/4/7/10): +20%
    - Trikona (1/5/9): +15%
    - Dusthana (6/8/12): -40%
    Retrograde adds 5 %; combustion subtracts 30 %.

    Args:
        planet: A PlanetData object from ChartData.planets.

    Returns:
        Float in [0.0, 100.0].
    """
    base = _DIGNITY_SCORES.get(planet.dignity, 50.0)

    if planet.house in _KENDRA:
        base = min(100.0, base * 1.20)
    elif planet.house in _TRIKONA:
        base = min(100.0, base * 1.15)
    elif planet.house in _DUSTHANA:
        base = max(0.0, base * 0.60)

    if planet.is_retrograde:
        base = min(100.0, base * 1.05)
    if planet.is_combust:
        base = max(0.0, base * 0.70)

    return round(base, 2)


def _direction_description(
    planet_name: str, direction: str, planet: PlanetData, score: float
) -> str:
    """Return a short human-readable description of a direction's strength."""
    level = "Strong" if score >= 75 else "Moderate" if score >= 50 else "Weak"
    retro = " (R)" if planet.is_retrograde else ""
    return (
        f"{planet_name}{retro} — {planet.dignity}, house {planet.house} — "
        f"{direction} is {level} ({score:.0f}/100)"
    )


# ── Public computation functions ──────────────────────────────────────────────


def compute_direction_strengths(chart: ChartData) -> list[DirectionStrength]:
    """Calculate the Vastu strength of each compass direction from the chart.

    Each of the 9 planets rules one direction (Dik Bala). Two planets (Moon
    and Ketu) share North-West; both are evaluated as separate entries so
    callers receive the full picture.

    Args:
        chart: Computed birth chart data.

    Returns:
        List of DirectionStrength objects sorted by strength descending.
    """
    rules: dict[str, Any] = load_vastu_rules()
    planet_dirs: dict[str, str] = rules.get("planet_directions", {})
    direction_hi: dict[str, str] = rules.get("direction_hi", {})

    results: list[DirectionStrength] = []

    for planet_name, direction in planet_dirs.items():
        planet = chart.planets.get(planet_name)
        if planet is None:
            continue

        score = _planet_strength_score(planet)
        results.append(
            DirectionStrength(
                direction=direction,
                direction_hi=direction_hi.get(direction, direction),
                planet=planet_name,
                strength_score=score,
                dignity=planet.dignity,
                house=planet.house,
                is_favorable=score >= 50.0,
                description=_direction_description(planet_name, direction, planet, score),
            )
        )

    results.sort(key=lambda x: (-x.strength_score, x.direction))
    return results


def compute_favorable_directions(chart: ChartData) -> dict[str, str]:
    """Map key house lords to their Vastu directions for personalised guidance.

    Returns a dict with these roles:
    - ``lagna``: Most favorable — lagna lord direction
    - ``home``: 4th lord direction (property and comforts)
    - ``fortune``: 9th lord direction
    - ``career``: 10th lord direction
    - ``maraka_1``: 2nd lord direction — to be treated cautiously
    - ``maraka_2``: 7th lord direction — to be treated cautiously
    - ``dusthana``: 6th lord direction — generally to avoid

    Args:
        chart: Computed birth chart data.

    Returns:
        Dict mapping role string to direction string.
    """
    rules: dict[str, Any] = load_vastu_rules()
    planet_dirs: dict[str, str] = rules.get("planet_directions", {})

    def _lord_dir(house_offset: int) -> str:
        sign_index = (chart.lagna_sign_index + house_offset) % 12
        lord = SIGN_LORDS[sign_index]
        return planet_dirs.get(lord, "Unknown")

    return {
        "lagna": _lord_dir(0),  # 1st lord
        "home": _lord_dir(3),  # 4th lord
        "fortune": _lord_dir(8),  # 9th lord
        "career": _lord_dir(9),  # 10th lord
        "maraka_1": _lord_dir(1),  # 2nd lord
        "maraka_2": _lord_dir(6),  # 7th lord
        "dusthana": _lord_dir(5),  # 6th lord
    }


def detect_vastu_doshas(chart: ChartData) -> list[VastuDosha]:
    """Detect Vastu doshas from natal planetary placements.

    Primarily checks for planets in the 4th house (home/property) that
    create specific structural, elemental, or psychic challenges.

    Args:
        chart: Computed birth chart data.

    Returns:
        List of VastuDosha objects for all defined dosha triggers
        (both present and absent, so callers can inspect all).
    """
    rules: dict[str, Any] = load_vastu_rules()
    dosha_defs: dict[str, Any] = rules.get("vastu_doshas", {})

    doshas: list[VastuDosha] = []

    for _key, defn in dosha_defs.items():
        trigger = defn.get("trigger", {})
        planet_name: str = trigger.get("planet", "")
        trigger_house: int = trigger.get("house", 0)

        if not planet_name or not trigger_house:
            continue

        planet = chart.planets.get(planet_name)
        is_present = planet is not None and planet.house == trigger_house

        doshas.append(
            VastuDosha(
                name=defn.get("name", _key),
                name_hi=defn.get("name_hi", ""),
                is_present=is_present,
                planet=planet_name,
                house=trigger_house,
                severity=defn.get("severity", "mild") if is_present else "none",
                description=defn.get("description", "").strip(),
                remedy_direction=defn.get("remedy_direction", "North-East"),
            )
        )

    return doshas


def _build_summary(
    chart: ChartData,
    lagna_lord: str,
    most_favorable: str,
    active_doshas: list[str],
) -> str:
    """Compose a concise Vastu summary string."""
    dosha_text = (
        f" Active doshas: {', '.join(active_doshas)}."
        if active_doshas
        else " No major Vastu doshas detected."
    )
    return (
        f"{chart.lagna_sign} lagna — lagna lord {lagna_lord} rules "
        f"{most_favorable}, making it the most favorable direction.{dosha_text}"
    )


def compute_vastu(chart: ChartData) -> VastuResult:
    """Compute a complete Vastu Shastra analysis for a natal chart.

    Combines directional strengths, Vastu Purusha Mandala zones, room
    placement recommendations, Ayadi Shadvarga door analysis, and
    dosha detections into a single VastuResult.

    Args:
        chart: Computed birth chart data.

    Returns:
        VastuResult with all Vastu computations populated.
    """
    from daivai_engine.compute.vastu_mandala import (
        analyze_entry_door,
        compute_mandala_zones,
        compute_room_recommendations,
    )

    direction_strengths = compute_direction_strengths(chart)
    favorable_dirs = compute_favorable_directions(chart)
    doshas = detect_vastu_doshas(chart)
    active_doshas = [d.name for d in doshas if d.is_present]

    most_favorable = direction_strengths[0].direction if direction_strengths else "North"
    least_favorable = direction_strengths[-1].direction if direction_strengths else "South"

    lagna_lord = SIGN_LORDS[chart.lagna_sign_index]

    return VastuResult(
        lagna=chart.lagna_sign,
        lagna_lord=lagna_lord,
        direction_strengths=direction_strengths,
        most_favorable_direction=most_favorable,
        least_favorable_direction=least_favorable,
        favorable_directions=favorable_dirs,
        mandala_zones=compute_mandala_zones(chart),
        room_recommendations=compute_room_recommendations(chart),
        door_analysis=analyze_entry_door(chart),
        doshas=doshas,
        active_doshas=active_doshas,
        summary=_build_summary(chart, lagna_lord, most_favorable, active_doshas),
    )
