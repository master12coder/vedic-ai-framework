"""Advanced Transit Analysis — Sadesati detailed, Jupiter transit, Rahu-Ketu transit.

Extends basic transit with phase-level analysis for Saturn, Jupiter, and nodes.

Source: BPHS transit chapters, Phaladeepika.
"""

from __future__ import annotations

from datetime import date

import swisseph as swe
from pydantic import BaseModel

from daivai_engine.constants import DEGREES_PER_SIGN
from daivai_engine.models.chart import ChartData


class SadesatiDetail(BaseModel):
    """Detailed Sade Sati (7.5 year Saturn transit) analysis."""

    is_active: bool
    phase: int | None  # 1=Rising, 2=Peak, 3=Setting, None=not active
    phase_name: str  # "Rising" / "Peak" / "Setting" / "None"
    phase_name_hi: str
    moon_sign_hi: str
    saturn_sign_hi: str
    intensity: str  # mild / moderate / severe
    description: str


class JupiterTransitResult(BaseModel):
    """Jupiter transit analysis from Moon sign."""

    is_favorable: bool
    transit_house_from_moon: int  # 1-12
    transit_sign_hi: str
    description: str


class RahuKetuTransitResult(BaseModel):
    """Rahu-Ketu transit analysis from Moon/Lagna."""

    rahu_house_from_moon: int
    ketu_house_from_moon: int
    rahu_house_from_lagna: int
    ketu_house_from_lagna: int
    rahu_sign_hi: str
    ketu_sign_hi: str
    karmic_focus: str


# Favorable Jupiter transit houses from Moon — Phaladeepika Ch.26
_JUPITER_FAVORABLE = {2, 5, 7, 9, 11}


def compute_sadesati_detailed(chart: ChartData, target_date: date | None = None) -> SadesatiDetail:
    """Compute detailed Sade Sati phase analysis.

    Sade Sati = Saturn transiting 12th, 1st, or 2nd from Moon sign.
    Each phase lasts ~2.5 years. Total ~7.5 years.

    Source: Phaladeepika Ch.26, widely used.
    """
    if target_date is None:
        target_date = date.today()

    moon_sign = chart.planets["Moon"].sign_index
    from daivai_engine.constants import SIGNS_HI

    sat_sign = _get_transit_sign("Saturn", target_date)

    # Phase detection
    offset = (sat_sign - moon_sign) % 12
    if offset == 11:  # 12th from Moon = Rising
        phase, phase_name, phase_hi = 1, "Rising", "आरोहण"
    elif offset == 0:  # Over Moon sign = Peak
        phase, phase_name, phase_hi = 2, "Peak", "शिखर"
    elif offset == 1:  # 2nd from Moon = Setting
        phase, phase_name, phase_hi = 3, "Setting", "अवरोहण"
    else:
        return SadesatiDetail(
            is_active=False,
            phase=None,
            phase_name="None",
            phase_name_hi="नहीं",
            moon_sign_hi=SIGNS_HI[moon_sign],
            saturn_sign_hi=SIGNS_HI[sat_sign],
            intensity="none",
            description="Sade Sati not active",
        )

    # Intensity based on Saturn's transit sign dignity — BPHS
    if sat_sign in (6, 9, 10):  # Libra(exalted), Capricorn, Aquarius(own)
        intensity = "mild"
    elif sat_sign in (0, 3):  # Aries(debilitated), Cancer
        intensity = "severe"
    else:
        intensity = "moderate"

    return SadesatiDetail(
        is_active=True,
        phase=phase,
        phase_name=phase_name,
        phase_name_hi=phase_hi,
        moon_sign_hi=SIGNS_HI[moon_sign],
        saturn_sign_hi=SIGNS_HI[sat_sign],
        intensity=intensity,
        description=f"Sade Sati Phase {phase} ({phase_name}) — Saturn in {SIGNS_HI[sat_sign]}",
    )


def compute_jupiter_transit(
    chart: ChartData, target_date: date | None = None
) -> JupiterTransitResult:
    """Analyze Jupiter's transit from Moon sign.

    Jupiter in 2/5/7/9/11 from Moon = favorable (Phaladeepika).

    Source: Phaladeepika Ch.26.
    """
    if target_date is None:
        target_date = date.today()

    from daivai_engine.constants import SIGNS_HI

    moon_sign = chart.planets["Moon"].sign_index
    jup_sign = _get_transit_sign("Jupiter", target_date)
    house = ((jup_sign - moon_sign) % 12) + 1
    is_fav = house in _JUPITER_FAVORABLE

    return JupiterTransitResult(
        is_favorable=is_fav,
        transit_house_from_moon=house,
        transit_sign_hi=SIGNS_HI[jup_sign],
        description=f"Jupiter in house {house} from Moon — {'favorable' if is_fav else 'challenging'}",
    )


def compute_rahu_ketu_transit(
    chart: ChartData, target_date: date | None = None
) -> RahuKetuTransitResult:
    """Analyze Rahu-Ketu transit from Moon and Lagna.

    Rahu's transit house indicates area of karmic focus.

    Source: BPHS transit chapter.
    """
    if target_date is None:
        target_date = date.today()

    from daivai_engine.constants import SIGNS_HI

    moon_sign = chart.planets["Moon"].sign_index
    lagna_sign = chart.lagna_sign_index
    rahu_sign = _get_transit_sign("Rahu", target_date)
    ketu_sign = (rahu_sign + 6) % 12

    r_from_moon = ((rahu_sign - moon_sign) % 12) + 1
    k_from_moon = ((ketu_sign - moon_sign) % 12) + 1
    r_from_lagna = ((rahu_sign - lagna_sign) % 12) + 1
    k_from_lagna = ((ketu_sign - lagna_sign) % 12) + 1

    karmic = _karmic_focus(r_from_moon, k_from_moon)

    return RahuKetuTransitResult(
        rahu_house_from_moon=r_from_moon,
        ketu_house_from_moon=k_from_moon,
        rahu_house_from_lagna=r_from_lagna,
        ketu_house_from_lagna=k_from_lagna,
        rahu_sign_hi=SIGNS_HI[rahu_sign],
        ketu_sign_hi=SIGNS_HI[ketu_sign],
        karmic_focus=karmic,
    )


def _get_transit_sign(planet: str, target_date: date) -> int:
    """Get sidereal sign index of a planet on a date."""
    jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    pid_map = {"Jupiter": swe.JUPITER, "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE}
    pid = pid_map[planet]
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    result = swe.calc_ut(jd, pid, flags)
    lon: float = result[0][0]  # type: ignore[index]
    return int(lon / DEGREES_PER_SIGN) % 12


def _karmic_focus(rahu_house: int, ketu_house: int) -> str:
    """Describe the karmic focus of the Rahu-Ketu axis transit."""
    focus = {
        1: "Self-identity, new beginnings",
        2: "Finances, family values",
        3: "Communication, siblings",
        4: "Home, property, mother",
        5: "Children, creativity, education",
        6: "Health, service, enemies",
        7: "Partnerships, marriage",
        8: "Transformation, inheritance",
        9: "Dharma, fortune, long travel",
        10: "Career, public life",
        11: "Gains, aspirations",
        12: "Spirituality, foreign lands",
    }
    return f"Rahu in {rahu_house}th: {focus.get(rahu_house, '')}, Ketu in {ketu_house}th: {focus.get(ketu_house, '')}"
