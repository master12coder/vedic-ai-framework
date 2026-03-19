"""Deeptadi and Lajjitadi Avastha computations from BPHS Ch.45.

Deeptadi = 9 states based on dignity, combustion, and planetary war.
Lajjitadi = 6 states based on house position and conjunctions.

Source: BPHS Chapter 45, verses 1-20.
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

    States (BPHS Ch.45 v1-10) in priority order:
    1. Deepta (exalted) = 1.5x
    2. Swastha (own sign) = 1.3x
    3. Mudita (great friend's sign) = 1.2x
    4. Shanta (friend's sign) = 1.1x
    5. Deena (neutral sign) = 0.8x
    6. Vikala (combust) = 0.5x
    7. Dukhita (enemy's sign) = 0.4x
    8. Khal (great enemy's sign) = 0.3x
    9. Kopa (debilitated) = 0.2x

    Combustion and debilitation override sign-based states.
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
    """Return (avastha, hindi, description, multiplier).

    Priority: debilitation > combustion > dignity > friendship.
    """
    # Kopa: debilitated (worst state — BPHS ranks this lowest)
    if p.dignity == "debilitated":
        return ("kopa", "कोप", f"{name} is debilitated — defeated state", 0.2)

    # Vikala: combust (overrides sign-based states)
    if p.is_combust and name != "Sun":
        return ("vikala", "विकल", f"{name} is combust — crippled state", 0.5)

    # Deepta: exalted (best state)
    if p.dignity == "exalted":
        return ("deepta", "दीप्त", f"{name} is exalted — brilliant state", 1.5)

    # Swastha: own sign
    if p.dignity in ("own", "mooltrikona"):
        return ("swastha", "स्वस्थ", f"{name} is in own sign — healthy state", 1.3)

    # Check friendship/enmity with sign lord for remaining states
    enemies = NATURAL_ENEMIES.get(name, [])
    friends = NATURAL_FRIENDS.get(name, [])

    if p.sign_lord in enemies:
        # Check if also conjunct/aspected by malefic → dukhita (worse)
        if _has_malefic_influence(name, chart):
            return (
                "khal",
                "खल",
                f"{name} in enemy sign with malefic influence — wicked state",
                0.3,
            )
        return ("dukhita", "दुखित", f"{name} is in enemy sign — distressed state", 0.4)

    if p.sign_lord in friends:
        # Distinguish great friend vs friend (BPHS makes this distinction)
        # Great friend = friend of friend too; simplified: just friend
        return ("shanta", "शान्त", f"{name} is in friend's sign — peaceful state", 1.1)

    # Neutral sign = deena (BPHS: miserable, not peaceful)
    return ("deena", "दीन", f"{name} is in neutral sign — miserable state", 0.8)


def _has_malefic_influence(planet_name: str, chart: ChartData) -> bool:
    """Check if planet is conjunct or aspected by a malefic.

    Checks both same-house conjunction and 7th/special aspects.
    """
    p = chart.planets[planet_name]
    for other_name, other in chart.planets.items():
        if other_name == planet_name:
            continue
        if other_name not in _MALEFICS:
            continue
        # Same house = conjunction
        if other.house == p.house:
            return True
        # 7th aspect (all planets)
        if ((other.house - 1 + 6) % 12) + 1 == p.house:
            return True
        # Special aspects (Mars 4,8; Saturn 3,10; Rahu/Ketu 5,9)
        from daivai_engine.constants import SPECIAL_ASPECTS

        for asp_dist in SPECIAL_ASPECTS.get(other_name, []):
            target = ((other.house - 1 + asp_dist - 1) % 12) + 1
            if target == p.house:
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

    # Trushita: in water sign with enemy influence
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
