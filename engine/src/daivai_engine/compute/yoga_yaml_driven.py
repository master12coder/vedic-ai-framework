"""YAML-driven yoga detector — auto-detects yogas from yoga_definitions.yaml.

Reads structured formation rules and evaluates them against ChartData.
Covers yogas not handled by specialized detector modules.

Source: yoga_definitions.yaml (382 definitions, BPHS/Phaladeepika/Saravali).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import (
    KENDRAS,
    SIGN_LORDS,
)
from daivai_engine.models.yoga import YogaResult


def _normalize(name: str) -> str:
    """Normalize yoga name for matching (lowercase, no spaces/underscores/yoga suffix)."""
    return (
        name.lower().replace(" ", "").replace("_", "").replace("-", "").rstrip("yoga").rstrip(" ")
    )


_YOGA_DEFS: dict[str, Any] | None = None
_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
_DUSTHANAS = {6, 8, 12}
_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def _load_yoga_defs() -> dict[str, Any]:
    global _YOGA_DEFS
    if _YOGA_DEFS is None:
        with open(_KNOWLEDGE_DIR / "yoga_definitions.yaml") as f:
            _YOGA_DEFS = yaml.safe_load(f) or {}
    return _YOGA_DEFS


def _planet_in_house(chart: ChartData, planet: str, houses: list[int]) -> bool:
    """Check if planet is in one of the specified houses."""
    p = chart.planets.get(planet)
    return p is not None and p.house in houses


def _planet_dignity(chart: ChartData, planet: str) -> str:
    """Get planet's dignity (exalted/own/debilitated/neutral)."""
    p = chart.planets.get(planet)
    return p.dignity if p else "neutral"


def _is_own_or_exalted(chart: ChartData, planet: str) -> bool:
    d = _planet_dignity(chart, planet)
    return d in ("exalted", "own", "mooltrikona")


def _planets_conjunct(chart: ChartData, p1: str, p2: str) -> bool:
    """Check if two planets are in the same house."""
    a = chart.planets.get(p1)
    b = chart.planets.get(p2)
    return a is not None and b is not None and a.house == b.house


def _house_from_ref(chart: ChartData, planet: str, ref_planet: str) -> int:
    """Get house of planet counted from ref_planet's sign."""
    p = chart.planets.get(planet)
    r = chart.planets.get(ref_planet)
    if not p or not r:
        return 0
    return ((p.sign_index - r.sign_index) % 12) + 1


def _evaluate_sign_condition(
    chart: ChartData,
    planets: list[str],
    sign_cond: str,
    houses: list[int],
) -> bool:
    """Evaluate a sign_condition rule against chart data."""
    if not sign_cond or sign_cond == "none":
        # No sign condition — just check house placement
        return (
            all(_planet_in_house(chart, p.capitalize(), houses) for p in planets)
            if planets and houses
            else True
        )

    sc = sign_cond.lower()

    # Common patterns
    if sc == "own_or_exalted":
        return all(
            _is_own_or_exalted(chart, p.capitalize())
            and _planet_in_house(chart, p.capitalize(), houses)
            for p in planets
        )

    if sc == "exalted":
        return all(_planet_dignity(chart, p.capitalize()) == "exalted" for p in planets)

    if sc == "debilitated":
        return all(_planet_dignity(chart, p.capitalize()) == "debilitated" for p in planets)

    if sc in ("good_dignity", "strong_placement", "own_exalted_or_friendly"):
        return all(
            _planet_dignity(chart, p.capitalize()) in ("exalted", "own", "mooltrikona", "friend")
            for p in planets
        )

    if sc == "conjunction":
        if len(planets) >= 2:
            return _planets_conjunct(chart, planets[0].capitalize(), planets[1].capitalize())
        return False

    if sc == "conjunction_or_mutual_aspect_or_exchange" and len(planets) >= 2:
        p1, p2 = planets[0].capitalize(), planets[1].capitalize()
        return _planets_conjunct(chart, p1, p2) or _is_exchange(chart, p1, p2)

    if sc == "parivartana" and len(planets) >= 2:
        return _is_exchange(chart, planets[0].capitalize(), planets[1].capitalize())

    if sc == "no_planets_adjacent_to_moon":
        moon = chart.planets.get("Moon")
        if not moon:
            return False
        h2 = ((moon.house - 1) % 12) + 1  # house before
        h12 = (moon.house % 12) + 1  # house after
        return not any(p.house in (h2, h12) for name, p in chart.planets.items() if name != "Moon")

    if sc == "all_planets_hemmed_between_rahu_ketu":
        rahu_h = chart.planets.get("Rahu", None)
        ketu_h = chart.planets.get("Ketu", None)
        if not rahu_h or not ketu_h:
            return False
        # All other planets between Rahu and Ketu (in sign order)
        rsi, ksi = rahu_h.sign_index, ketu_h.sign_index
        for name, p in chart.planets.items():
            if name in ("Rahu", "Ketu"):
                continue
            # Check if planet is between rahu and ketu
            if rsi < ksi:
                if not (rsi < p.sign_index < ksi):
                    return False
            else:
                if ksi < p.sign_index < rsi:
                    return False
        return True

    if sc.startswith("benefics_in_6") or sc.startswith("benefics_in_6th_7th_8th"):
        moon = chart.planets.get("Moon")
        if not moon:
            return False
        target = {6, 7, 8}
        benefic_count = sum(
            1 for b in _BENEFICS if b != "Moon" and _house_from_ref(chart, b, "Moon") in target
        )
        if "all_three" in sc:
            return benefic_count >= 3
        if "two" in sc:
            return benefic_count >= 2
        if "one" in sc:
            return benefic_count >= 1
        return benefic_count >= 2

    if sc == "jupiter_in_kendra_from_moon":
        return _house_from_ref(chart, "Jupiter", "Moon") in KENDRAS

    if sc == "dusthana_lord_in_dusthana":
        for h in _DUSTHANAS:
            lord = get_house_lord(chart, h)
            lp = chart.planets.get(lord)
            if lp and lp.house in _DUSTHANAS:
                return True
        return False

    if sc.startswith("benefics_flanking"):
        # Shubh Kartari — benefics in 2nd and 12th from a house
        return False  # Complex, handled by existing kartari code

    if sc.startswith("malefics_flanking"):
        # Papa Kartari
        return False  # Complex, handled by existing kartari code

    # For complex conditions we can't parse, return False (skip)
    return False


def _is_exchange(chart: ChartData, p1: str, p2: str) -> bool:
    """Check if two planets are in parivartana (mutual exchange of signs)."""
    a = chart.planets.get(p1)
    b = chart.planets.get(p2)
    if not a or not b:
        return False
    lord_a = SIGN_LORDS[a.sign_index]
    lord_b = SIGN_LORDS[b.sign_index]
    return lord_a == p2 and lord_b == p1


def detect_yaml_driven_yogas(
    chart: ChartData,
    skip_names: set[str] | None = None,
) -> list[YogaResult]:
    """Detect yogas from YAML definitions that aren't handled by specialized code.

    Args:
        chart: Computed birth chart.
        skip_names: Yoga keys to skip (already detected by specialized modules).

    Returns:
        List of YogaResults for YAML-detected yogas.
    """
    defs = _load_yoga_defs()
    skip_raw = skip_names or set()
    # Normalize skip names for fuzzy matching (code names differ from YAML names)
    skip_norm = {_normalize(s) for s in skip_raw}
    results: list[YogaResult] = []

    for key, ydef in defs.items():
        if not isinstance(ydef, dict):
            continue
        name_en = ydef.get("name_en", key)
        # Skip if already detected (match on normalized key OR name)
        if _normalize(key) in skip_norm or _normalize(name_en) in skip_norm:
            continue

        formation = ydef.get("formation", {})
        if not isinstance(formation, dict):
            continue

        planets = [p.capitalize() for p in formation.get("planets", [])]
        houses = formation.get("houses_required", [])
        sign_cond = formation.get("sign_condition", "")

        # Evaluate the formation rule
        is_present = False

        if planets and houses and not sign_cond:
            # Simple: all planets must be in specified houses
            is_present = all(_planet_in_house(chart, p, houses) for p in planets)
        elif planets and houses and sign_cond:
            # Planet in house WITH sign condition
            is_present = _evaluate_sign_condition(
                chart, [p.lower() for p in planets], sign_cond, houses
            )
        elif planets and sign_cond and not houses:
            # Sign condition without house requirement
            is_present = _evaluate_sign_condition(
                chart, [p.lower() for p in planets], sign_cond, []
            )
        elif not planets and sign_cond:
            # Chart-wide condition (e.g., all_planets_hemmed)
            is_present = _evaluate_sign_condition(chart, [], sign_cond, houses)
        elif planets and not houses and not sign_cond:
            # Just planet presence (rare)
            is_present = all(p in chart.planets for p in planets)

        if is_present:
            # Get houses of involved planets for the result
            involved_houses = []
            for p in planets:
                pd = chart.planets.get(p)
                if pd:
                    involved_houses.append(pd.house)

            effects = ydef.get("effects", {})
            desc = effects.get("general", "")[:200] if isinstance(effects, dict) else ""

            results.append(
                YogaResult(
                    name=ydef.get("name_en", key),
                    name_hindi=ydef.get("name_hi", ""),
                    description=desc,
                    effect=ydef.get("type", "mixed"),
                    is_present=True,
                    planets_involved=planets,
                    houses_involved=involved_houses,
                )
            )

    return results
