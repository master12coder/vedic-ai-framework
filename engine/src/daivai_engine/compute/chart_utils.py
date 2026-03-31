"""Chart helper functions — nakshatra, dignity, avastha, combustion, house queries."""

from __future__ import annotations

from daivai_engine.constants import (
    AVASTHAS,
    CAZIMI_LIMIT,
    COMBUSTION_LIMITS,
    COMBUSTION_LIMITS_RETROGRADE,
    DEBILITATION,
    DEFAULT_CONJUNCTION_ORB,
    EXALTATION,
    FULL_CIRCLE_DEG,
    HALF_CIRCLE_DEG,
    MAX_NAKSHATRA_INDEX,
    MOOLTRIKONA,
    NAKSHATRA_SPAN_DEG,
    OWN_SIGNS,
    PADAS_PER_NAKSHATRA,
    SIGN_LORDS,
    SPECIAL_ASPECTS,
)
from daivai_engine.models.chart import ChartData, PlanetData


def get_nakshatra(lon: float) -> tuple[int, int]:
    """Return (nakshatra_index, pada) from sidereal longitude."""
    nak_index = int(lon / NAKSHATRA_SPAN_DEG)
    if nak_index > MAX_NAKSHATRA_INDEX:
        nak_index = MAX_NAKSHATRA_INDEX
    degree_in_nak = lon - nak_index * NAKSHATRA_SPAN_DEG
    pada = int(degree_in_nak / (NAKSHATRA_SPAN_DEG / PADAS_PER_NAKSHATRA)) + 1
    if pada > PADAS_PER_NAKSHATRA:
        pada = PADAS_PER_NAKSHATRA
    return nak_index, pada


def _get_dignity(planet: str, sign_index: int, degree_in_sign: float) -> str:
    """Determine planet's dignity in a sign."""
    if planet in EXALTATION and EXALTATION[planet] == sign_index:
        return "exalted"
    if planet in DEBILITATION and DEBILITATION[planet] == sign_index:
        return "debilitated"
    if planet in MOOLTRIKONA:
        mt_sign, mt_start, mt_end = MOOLTRIKONA[planet]
        if sign_index == mt_sign and mt_start <= degree_in_sign <= mt_end:
            return "mooltrikona"
    if planet in OWN_SIGNS and sign_index in OWN_SIGNS[planet]:
        return "own"
    return "neutral"


def _get_avastha(degree_in_sign: float, sign_index: int) -> str:
    """Determine planetary age state based on degree in sign."""
    # Odd signs: 0-6 Bala, 6-12 Kumara, 12-18 Yuva, 18-24 Vriddha, 24-30 Mruta
    # Even signs: reversed
    segment = int(degree_in_sign / 6.0)
    if segment > 4:
        segment = 4
    if sign_index % 2 == 0:  # Odd signs (0-indexed even = 1st,3rd,5th... signs)
        return AVASTHAS[segment]
    else:  # Even signs — reverse
        return AVASTHAS[4 - segment]


def _check_combustion(
    planet: str, planet_lon: float, sun_lon: float, is_retro: bool
) -> tuple[bool, bool]:
    """Check combustion and cazimi status for a planet.

    Returns:
        Tuple of (is_combust, is_cazimi).
        - is_cazimi: within CAZIMI_LIMIT (17') of Sun — extremely powerful
        - is_combust: within combustion limit but outside cazimi — weakened
        A cazimi planet is NOT combust (is_combust=False when is_cazimi=True).

    Source: Saravali Ch.4; Phaladeepika Ch.2 v.6.
    """
    if planet in ("Sun", "Rahu", "Ketu"):
        return False, False
    limit = COMBUSTION_LIMITS.get(planet)
    if limit is None:
        return False, False
    if is_retro and planet in COMBUSTION_LIMITS_RETROGRADE:
        limit = COMBUSTION_LIMITS_RETROGRADE[planet]
    diff = abs(planet_lon - sun_lon)
    if diff > 180:
        diff = 360 - diff
    if diff < CAZIMI_LIMIT:
        return False, True  # Cazimi — in heart of Sun, not weakened
    return diff < limit, False


def _house_from_lagna(planet_sign: int, lagna_sign: int) -> int:
    """Calculate house number (1-12) from lagna sign (whole sign houses)."""
    return ((planet_sign - lagna_sign) % 12) + 1


def get_house_lord(chart: ChartData, house_num: int) -> str:
    """Get the lord of a specific house (whole sign)."""
    sign_index = (chart.lagna_sign_index + house_num - 1) % 12
    return SIGN_LORDS[sign_index]


def get_planets_in_house(chart: ChartData, house_num: int) -> list[PlanetData]:
    """Get all planets in a specific house."""
    return [p for p in chart.planets.values() if p.house == house_num]


def get_planet_house(chart: ChartData, planet_name: str) -> int:
    """Get the house number of a planet."""
    return chart.planets[planet_name].house


def are_conjunct(
    chart: ChartData, planet1: str, planet2: str, orb: float = DEFAULT_CONJUNCTION_ORB
) -> bool:
    """Check if two planets are conjunct (in same sign or within orb)."""
    p1 = chart.planets[planet1]
    p2 = chart.planets[planet2]
    if p1.sign_index == p2.sign_index:
        return True
    diff = abs(p1.longitude - p2.longitude)
    if diff > HALF_CIRCLE_DEG:
        diff = FULL_CIRCLE_DEG - diff
    return diff <= orb


def has_aspect(chart: ChartData, aspecting_planet: str, target_house: int) -> bool:
    """Check if a planet aspects a given house (including special aspects)."""
    p = chart.planets[aspecting_planet]
    planet_house = p.house

    # Standard 7th aspect
    aspected_house = ((planet_house - 1 + 6) % 12) + 1
    if aspected_house == target_house:
        return True

    # Special aspects
    if aspecting_planet in SPECIAL_ASPECTS:
        for asp in SPECIAL_ASPECTS[aspecting_planet]:
            aspected = ((planet_house - 1 + asp - 1) % 12) + 1
            if aspected == target_house:
                return True

    return False
