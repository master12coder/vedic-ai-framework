"""Double Transit — Jupiter + Saturn must both aspect a house for major events.

The primary timing technique used by professional astrologers (K.N. Rao school).
For each house, checks if BOTH transiting Jupiter and Saturn aspect it.
When both aspect, that house's significations become active.

Source: Widely used in North Indian tradition, derived from BPHS transit chapter.
"""

from __future__ import annotations

from datetime import date

import swisseph as swe

from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    SPECIAL_ASPECTS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import DoubleTransit


# House significations for event prediction
_HOUSE_EVENTS: dict[int, str] = {
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

# Hindi house names
_HOUSE_HI: dict[int, str] = {
    1: "तनु",
    2: "धन",
    3: "सहज",
    4: "सुख",
    5: "सन्तान",
    6: "रोग",
    7: "जाया",
    8: "मृत्यु",
    9: "भाग्य",
    10: "कर्म",
    11: "लाभ",
    12: "व्यय",
}


def check_double_transit(
    chart: ChartData,
    target_date: date | None = None,
) -> list[DoubleTransit]:
    """Check double transit for all 12 houses.

    Args:
        chart: Natal birth chart.
        target_date: Date to check transits for. Defaults to today.

    Returns:
        List of 12 DoubleTransit results, one per house.
    """
    if target_date is None:
        target_date = date.today()

    # Get current Jupiter and Saturn positions
    jup_sign = _transit_sign("Jupiter", target_date)
    sat_sign = _transit_sign("Saturn", target_date)

    # Jupiter aspects: 1st (conjunction), 5th, 7th, 9th from its position
    jup_aspected = _aspected_houses(jup_sign, chart.lagna_sign_index, "Jupiter")
    sat_aspected = _aspected_houses(sat_sign, chart.lagna_sign_index, "Saturn")

    results: list[DoubleTransit] = []
    for house in range(1, 13):
        j_asp = house in jup_aspected
        s_asp = house in sat_aspected
        is_active = j_asp and s_asp

        results.append(
            DoubleTransit(
                house=house,
                house_name_hi=_HOUSE_HI.get(house, ""),
                jupiter_aspects=j_asp,
                saturn_aspects=s_asp,
                is_active=is_active,
                event_potential=_HOUSE_EVENTS.get(house, ""),
            )
        )
    return results


def _transit_sign(planet: str, target_date: date) -> int:
    """Get the sidereal sign index of a planet on a given date."""
    jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    planet_ids = {
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
    }
    pid = planet_ids[planet]
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    result = swe.calc_ut(jd, pid, flags)
    lon = result[0][0]  # type: ignore[index]
    return int(lon / DEGREES_PER_SIGN) % 12


def _aspected_houses(planet_sign: int, lagna_sign: int, planet_name: str) -> set[int]:
    """Get all natal houses aspected by a transiting planet.

    Every planet aspects the 7th house from itself.
    Special aspects: Mars (4,8), Jupiter (5,9), Saturn (3,10).
    Being IN a house also counts as aspecting it.
    """
    # Convert transit sign to natal house
    transit_house = ((planet_sign - lagna_sign) % 12) + 1

    aspected = {transit_house}  # Planet is IN this house
    aspected.add(((transit_house - 1 + 6) % 12) + 1)  # 7th aspect

    for extra in SPECIAL_ASPECTS.get(planet_name, []):
        aspected.add(((transit_house - 1 + extra - 1) % 12) + 1)

    return aspected
