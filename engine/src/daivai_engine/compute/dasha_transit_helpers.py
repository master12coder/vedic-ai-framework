"""Dasha-Transit helper functions — transit positions, dignity, aspects, double transit.

Internal helpers for dasha_transit.py. Not part of the public API.

Source: BPHS Ch.25, Phaladeepika Ch.26.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.compute.chart import get_house_lord
from daivai_engine.constants import (
    DEBILITATION,
    DEGREES_PER_SIGN,
    EXALTATION,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    OWN_SIGNS,
    SPECIAL_ASPECTS,
    SWE_PLANETS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_transit import DoubleTransitOnDashaHouses


_HOUSE_SIGNIFICATION: dict[int, str] = {
    1: "Health, personality, new beginnings",
    2: "Finances, family, speech",
    3: "Siblings, courage, short travel",
    4: "Home, vehicle, mother, property",
    5: "Children, education, creativity",
    6: "Enemies, disease, service",
    7: "Marriage, partnerships, business",
    8: "Transformation, inheritance, longevity",
    9: "Fortune, dharma, long travel, guru",
    10: "Career, status, authority",
    11: "Gains, income, elder siblings",
    12: "Loss, expenses, foreign land, moksha",
}


def _get_transit_position(planet: str, jd: float) -> tuple[float, bool]:
    """Get sidereal transit longitude and retrograde status.

    Args:
        planet: Planet name.
        jd: Julian day.

    Returns:
        (sidereal_longitude, is_retrograde).
    """
    if planet == "Ketu":
        rahu_lon, _ = _get_transit_position("Rahu", jd)
        return (rahu_lon + 180.0) % 360.0, True

    swe_id = SWE_PLANETS.get(planet)
    if swe_id is None:
        return 0.0, False

    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    result = swe.calc_ut(jd, swe_id, flags)
    lon = result[0][0]  # type: ignore[index]
    speed = result[0][3]  # type: ignore[index]
    return float(lon), speed < 0


def _get_dignity(planet: str, sign_index: int) -> str:
    """Determine planet's dignity in a given sign.

    Args:
        planet: Planet name.
        sign_index: Sign index (0-11).

    Returns:
        Dignity string: "exalted" / "own" / "debilitated" / "neutral".
    """
    if EXALTATION.get(planet) == sign_index:
        return "exalted"
    if DEBILITATION.get(planet) == sign_index:
        return "debilitated"
    if sign_index in OWN_SIGNS.get(planet, []):
        return "own"
    return "neutral"


def _classify_bav(bindus: int) -> str:
    """Classify BAV bindu count into strength category.

    Args:
        bindus: Bindu count (0-8).

    Returns:
        "strong" (5+), "moderate" (3-4), "weak" (0-2).
    """
    if bindus >= 5:
        return "strong"
    if bindus >= 3:
        return "moderate"
    return "weak"


def _get_houses_owned(chart: ChartData, planet: str) -> list[int]:
    """Get all houses owned (lorded) by a planet in this chart.

    Args:
        chart: Natal chart.
        planet: Planet name.

    Returns:
        List of house numbers (1-12) owned by the planet.
    """
    owned: list[int] = []
    for house in range(1, 13):
        if get_house_lord(chart, house) == planet:
            owned.append(house)
    return owned


def _get_relationship(planet1: str, planet2: str) -> str:
    """Determine natural relationship between two planets.

    Source: BPHS Ch.3 — natural friendships and enmities.

    Args:
        planet1: First planet name.
        planet2: Second planet name.

    Returns:
        "friends" / "neutral" / "enemies".
    """
    friends = NATURAL_FRIENDS.get(planet1, [])
    enemies = NATURAL_ENEMIES.get(planet1, [])

    if planet2 in friends:
        return "friends"
    if planet2 in enemies:
        return "enemies"
    return "neutral"


def _check_mutual_aspect(
    sign1: int,
    sign2: int,
    planet1: str,
    planet2: str,
) -> bool:
    """Check if two planets aspect each other in transit.

    Every planet has 7th aspect. Mars/Jupiter/Saturn/Rahu/Ketu have
    special aspects per SPECIAL_ASPECTS.

    Args:
        sign1: Transit sign index of planet1.
        sign2: Transit sign index of planet2.
        planet1: Name of first planet.
        planet2: Name of second planet.

    Returns:
        True if they mutually aspect each other.
    """
    return _aspects(sign1, sign2, planet1) and _aspects(sign2, sign1, planet2)


def _aspects(from_sign: int, to_sign: int, planet: str) -> bool:
    """Check if planet at from_sign aspects to_sign.

    Args:
        from_sign: Sign index of the aspecting planet.
        to_sign: Target sign index.
        planet: Planet name (for special aspects).

    Returns:
        True if the planet aspects the target sign.
    """
    house_diff = ((to_sign - from_sign) % 12) + 1
    # 7th aspect (all planets)
    if house_diff == 7:
        return True
    # Special aspects
    specials = SPECIAL_ASPECTS.get(planet, [])
    return house_diff in specials


def _check_double_transit_on_houses(
    chart: ChartData,
    dasha_houses: set[int],
    jd: float,
) -> list[DoubleTransitOnDashaHouses]:
    """Check Jupiter + Saturn double transit on specific houses.

    Args:
        chart: Natal chart (for lagna sign).
        dasha_houses: Set of house numbers to check.
        jd: Julian day for transit positions.

    Returns:
        List of DoubleTransitOnDashaHouses for each dasha house.
    """
    jup_lon, _ = _get_transit_position("Jupiter", jd)
    sat_lon, _ = _get_transit_position("Saturn", jd)
    jup_sign = int(jup_lon / DEGREES_PER_SIGN) % 12
    sat_sign = int(sat_lon / DEGREES_PER_SIGN) % 12

    lagna = chart.lagna_sign_index
    jup_house = ((jup_sign - lagna) % 12) + 1
    sat_house = ((sat_sign - lagna) % 12) + 1

    jup_aspected = _aspected_houses_from(jup_house, "Jupiter")
    sat_aspected = _aspected_houses_from(sat_house, "Saturn")

    results: list[DoubleTransitOnDashaHouses] = []
    for house in sorted(dasha_houses):
        j_active = house in jup_aspected
        s_active = house in sat_aspected
        results.append(
            DoubleTransitOnDashaHouses(
                house=house,
                house_signification=_HOUSE_SIGNIFICATION.get(house, ""),
                jupiter_activates=j_active,
                saturn_activates=s_active,
                both_activate=j_active and s_active,
            )
        )
    return results


def _aspected_houses_from(transit_house: int, planet: str) -> set[int]:
    """Get all houses aspected by a planet from its transit house.

    Includes the transit house itself (planet is IN that house),
    the 7th aspect, and any special aspects.

    Args:
        transit_house: House number where planet is transiting (1-12).
        planet: Planet name.

    Returns:
        Set of house numbers aspected.
    """
    aspected = {transit_house}
    aspected.add(((transit_house - 1 + 6) % 12) + 1)  # 7th aspect
    for extra in SPECIAL_ASPECTS.get(planet, []):
        aspected.add(((transit_house - 1 + extra - 1) % 12) + 1)
    return aspected
