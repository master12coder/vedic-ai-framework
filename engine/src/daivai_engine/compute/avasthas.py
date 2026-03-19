"""Deeptadi and Lajjitadi Avastha computations from BPHS Ch.45.

Deeptadi = 9 states based on dignity, combustion, and planetary war.
Lajjitadi = 6 states based on house position and conjunctions.
"""

from __future__ import annotations

from daivai_engine.constants import (
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    SIGN_ELEMENTS,
)
from daivai_engine.models.avastha import DeeptadiAvastha, LajjitadiAvastha
from daivai_engine.models.chart import ChartData, PlanetData


_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
_DEEPTADI_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


def compute_deeptadi_avasthas(chart: ChartData) -> list[DeeptadiAvastha]:
    """Compute 9-state Deeptadi Avastha for each planet.

    States (BPHS Ch.45 v1-10):
    1. Deepta = exalted
    2. Swastha = own sign
    3. Mudita = friend's sign
    4. Shanta = benefic vargas (mooltrikona)
    5. Deena = enemy's sign
    6. Vikala = combust
    7. Dukhita = in malefic sign with malefic aspect/conjunction
    8. Kala = debilitated
    9. Kopa = defeated in planetary war (checked externally)

    Priority: combustion and debilitation override friendship/enmity.
    """
    results: list[DeeptadiAvastha] = []
    for name in _DEEPTADI_PLANETS:
        p = chart.planets[name]
        avastha, hi, desc, mult = _classify_deeptadi(name, p, chart)
        results.append(
            DeeptadiAvastha(
                planet=name,
                avastha=avastha,
                avastha_hi=hi,
                description=desc,
                strength_multiplier=mult,
            )
        )
    return results


def _classify_deeptadi(name: str, p: PlanetData, chart: ChartData) -> tuple[str, str, str, float]:
    """Return (avastha, hindi, description, multiplier)."""
    # Combustion takes high priority (BPHS: vikala overrides most)
    if p.is_combust and name != "Sun":
        return ("vikala", "विकल", f"{name} is combust — crippled state", 0.25)

    match p.dignity:
        case "exalted":
            return ("deepta", "दीप्त", f"{name} is exalted — brilliant state", 1.5)
        case "debilitated":
            return ("kala", "कल", f"{name} is debilitated — dead state", 0.1)
        case "own":
            return ("swastha", "स्वस्थ", f"{name} is in own sign — healthy state", 1.25)
        case "mooltrikona":
            return ("shanta", "शान्त", f"{name} is in mooltrikona — peaceful state", 1.2)

    # Check friendship/enmity with sign lord
    enemies = NATURAL_ENEMIES.get(name, [])
    friends = NATURAL_FRIENDS.get(name, [])

    if p.sign_lord in friends:
        return ("mudita", "मुदित", f"{name} is in friend's sign — delighted state", 1.0)

    if p.sign_lord in enemies:
        # Check if also aspected/conjunct with malefics → dukhita
        has_malefic = _has_malefic_influence(name, chart)
        if has_malefic:
            return (
                "dukhita",
                "दुखित",
                f"{name} is in enemy sign with malefic influence — distressed",
                0.3,
            )
        return ("deena", "दीन", f"{name} is in enemy's sign — miserable state", 0.5)

    # Neutral
    return ("shanta", "शान्त", f"{name} is in neutral/benefic position — peaceful state", 0.9)


def _has_malefic_influence(planet_name: str, chart: ChartData) -> bool:
    """Check if planet is conjunct or in same house as a malefic."""
    p = chart.planets[planet_name]
    for other_name, other in chart.planets.items():
        if other_name == planet_name:
            continue
        if other_name in _MALEFICS and other.house == p.house:
            return True
    return False


def compute_lajjitadi_avasthas(chart: ChartData) -> list[LajjitadiAvastha]:
    """Compute 6-state Lajjitadi Avastha for each planet.

    States (BPHS Ch.45 v11-20):
    1. Lajjita = in 5th house with Rahu/Ketu/Saturn/Mars
    2. Garvita = in exaltation or mooltrikona
    3. Kshudhita = in enemy sign or conjunct enemy
    4. Trushita = in water sign aspected by enemy (not aspected by friend)
    5. Mudita = conjunct friend or in friend's sign
    6. Kshobhita = conjunct Sun and aspected by malefic
    """
    results: list[LajjitadiAvastha] = []
    for name in _DEEPTADI_PLANETS:
        p = chart.planets[name]
        avastha, hi, desc, pos = _classify_lajjitadi(name, p, chart)
        results.append(
            LajjitadiAvastha(
                planet=name,
                avastha=avastha,
                avastha_hi=hi,
                description=desc,
                is_positive=pos,
            )
        )
    return results


def _classify_lajjitadi(name: str, p: PlanetData, chart: ChartData) -> tuple[str, str, str, bool]:
    """Return (avastha, hindi, description, is_positive)."""
    housemates = {n for n, o in chart.planets.items() if o.house == p.house and n != name}

    # Lajjita: in 5th house with Rahu/Ketu/Saturn/Mars
    if p.house == 5 and housemates & {"Rahu", "Ketu", "Saturn", "Mars"}:
        return (
            "lajjita",
            "लज्जित",
            f"{name} in 5th with malefic — ashamed state",
            False,
        )

    # Garvita: exaltation or mooltrikona
    if p.dignity in ("exalted", "mooltrikona"):
        return ("garvita", "गर्वित", f"{name} exalted/mooltrikona — proud state", True)

    # Kshobhita: conjunct Sun and aspected by malefic
    if name != "Sun" and "Sun" in housemates and _has_malefic_influence(name, chart):
        return (
            "kshobhita",
            "क्षोभित",
            f"{name} conjunct Sun with malefic aspect — agitated",
            False,
        )

    # Kshudhita: in enemy sign or conjunct enemy
    enemies = NATURAL_ENEMIES.get(name, [])
    if p.sign_lord in enemies:
        return (
            "kshudhita",
            "क्षुधित",
            f"{name} in enemy sign — hungry state",
            False,
        )
    if housemates & set(enemies):
        return (
            "kshudhita",
            "क्षुधित",
            f"{name} conjunct enemy — hungry state",
            False,
        )

    # Trushita: in water sign aspected by enemy, not by friend
    element = SIGN_ELEMENTS[p.sign_index]
    if element == "Water" and any(e in enemies for e in housemates):
        return (
            "trushita",
            "तृषित",
            f"{name} in water sign with enemy — thirsty state",
            False,
        )

    # Mudita: conjunct friend or in friend's sign
    friends = NATURAL_FRIENDS.get(name, [])
    if p.sign_lord in friends or (housemates & set(friends)):
        return ("mudita", "मुदित", f"{name} with friend — happy state", True)

    # Default: mudita (neutral-positive)
    return ("mudita", "मुदित", f"{name} in neutral/friendly position — content", True)
