"""Upapada Lagna — Jaimini marriage indicator.

Upapada = Arudha of the 12th house. Computed by counting the distance
of the 12th lord from the 12th house, then projecting the same distance
from the lord's position.

Source: Jaimini Sutras, Chapter 1.
"""

from __future__ import annotations

from daivai_engine.constants import SIGN_LORDS, SIGNS_EN, SIGNS_HI
from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import UpapadaLagna


def compute_upapada_lagna(chart: ChartData) -> UpapadaLagna:
    """Compute Upapada Lagna for marriage analysis.

    Steps:
    1. Find 12th house sign from lagna
    2. Find lord of that sign
    3. Count houses from 12th to where its lord sits
    4. Count same distance from the lord → that sign is Upapada
    5. Exception: if count = 1 or 7, use 10th from lord instead

    Args:
        chart: Computed birth chart.

    Returns:
        UpapadaLagna with sign, lord, and marriage indication.
    """
    # 12th house sign index
    twelfth_sign = (chart.lagna_sign_index + 11) % 12
    twelfth_lord = SIGN_LORDS[twelfth_sign]

    # Find where the 12th lord is placed
    lord_planet = chart.planets.get(twelfth_lord)
    if lord_planet is None:
        # Fallback: Rahu/Ketu not in SIGN_LORDS, shouldn't happen
        return _fallback(chart)

    lord_sign = lord_planet.sign_index

    # Count from 12th house to lord's sign (1-based)
    distance = ((lord_sign - twelfth_sign) % 12) + 1

    # Exception: if lord is in 1st or 7th from the house
    if distance in (1, 7):
        # Count 10th from lord instead
        upapada_sign = (lord_sign + 9) % 12
    else:
        # Project same distance from lord
        upapada_sign = (lord_sign + distance - 1) % 12

    # Upapada lord
    up_lord = SIGN_LORDS[upapada_sign]

    # Which natal house is the upapada lord in?
    up_lord_planet = chart.planets.get(up_lord)
    up_lord_house = up_lord_planet.house if up_lord_planet else 1

    # Planets in the upapada sign (same house)
    up_house = ((upapada_sign - chart.lagna_sign_index) % 12) + 1
    planets_there = [name for name, p in chart.planets.items() if p.house == up_house]

    indication = _marriage_indication(up_lord, up_lord_house, planets_there, chart)

    return UpapadaLagna(
        sign_index=upapada_sign,
        sign_hi=SIGNS_HI[upapada_sign],
        sign_en=SIGNS_EN[upapada_sign],
        lord=up_lord,
        lord_house=up_lord_house,
        planets_in_upapada=planets_there,
        marriage_indication=indication,
    )


def _marriage_indication(
    lord: str,
    lord_house: int,
    planets: list[str],
    chart: ChartData,
) -> str:
    """Assess marriage indication from upapada factors."""
    malefics_in = {"Saturn", "Mars", "Rahu", "Ketu"} & set(planets)

    # Lord in kendra (1,4,7,10) or trikona (5,9) = favorable
    if lord_house in (1, 4, 5, 7, 9, 10):
        if not malefics_in:
            return "favorable"
        return "delayed"

    # Lord in dusthana (6,8,12) = challenging
    if lord_house in (6, 8, 12):
        return "challenging"

    if malefics_in:
        return "delayed"

    return "favorable"


def _fallback(chart: ChartData) -> UpapadaLagna:
    """Fallback when 12th lord can't be determined."""
    return UpapadaLagna(
        sign_index=chart.lagna_sign_index,
        sign_hi=SIGNS_HI[chart.lagna_sign_index],
        sign_en=SIGNS_EN[chart.lagna_sign_index],
        lord=SIGN_LORDS[chart.lagna_sign_index],
        lord_house=1,
        planets_in_upapada=[],
        marriage_indication="favorable",
    )
