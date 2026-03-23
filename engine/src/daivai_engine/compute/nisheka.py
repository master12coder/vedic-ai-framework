"""Nisheka (conception) chart computation from birth chart.

The Nisheka / Adhana chart estimates the moment of conception using BPHS Ch.4
rules. The approximate gestation period is ~273 days (10 lunar months), refined
by the Moon's position in the birth chart.

Verification rule: The Nisheka lagna should be the Moon sign of the birth chart,
OR the birth lagna should be the Moon sign of the Nisheka chart.

Source: BPHS Ch.4.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    SIGNS_EN,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.nisheka import NishekaResult


# Base gestation period in days (10 lunar months x 27.3 days ≈ 273)
_BASE_GESTATION_DAYS = 273.0


def _moon_degrees_in_sign(chart: ChartData) -> float:
    """Return the Moon's degree within its sign (0-30).

    Args:
        chart: The computed birth chart.

    Returns:
        Moon's degree within its current sign.
    """
    moon = chart.planets["Moon"]
    return moon.degree_in_sign


def _moon_house(chart: ChartData) -> int:
    """Return the Moon's house (1-12) in the birth chart.

    Args:
        chart: The computed birth chart.

    Returns:
        House number (1-12).
    """
    return chart.planets["Moon"].house


def _compute_conception_jd(chart: ChartData) -> float:
    """Compute the approximate Julian Day of conception.

    BPHS rule:
    - If Moon is in visible half (houses 7-12): subtract Moon's degrees
      in sign from 273
    - If Moon is in invisible half (houses 1-6): add Moon's degrees
      in sign to 273

    Args:
        chart: The computed birth chart.

    Returns:
        Approximate Julian Day of conception.
    """
    moon_deg = _moon_degrees_in_sign(chart)
    moon_h = _moon_house(chart)

    if moon_h >= 7:
        # Visible half: subtract degrees
        gestation_days = _BASE_GESTATION_DAYS - moon_deg
    else:
        # Invisible half: add degrees
        gestation_days = _BASE_GESTATION_DAYS + moon_deg

    return chart.julian_day - gestation_days


def _compute_sidereal_lagna(jd: float, lat: float, lon: float) -> tuple[float, int]:
    """Compute the sidereal ascendant at a given moment and location.

    Args:
        jd: Julian Day (UT).
        lat: Geographic latitude.
        lon: Geographic longitude.

    Returns:
        Tuple of (sidereal_longitude, sign_index).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    ayanamsha = swe.get_ayanamsa_ut(jd)
    sidereal_asc = (ascmc[0] - ayanamsha) % FULL_CIRCLE_DEG
    sign_index = int(sidereal_asc / DEGREES_PER_SIGN)
    return sidereal_asc, sign_index


def _compute_sidereal_moon(jd: float) -> tuple[float, int]:
    """Compute the sidereal Moon position at a given Julian Day.

    Args:
        jd: Julian Day (UT).

    Returns:
        Tuple of (sidereal_longitude, sign_index).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd)
    result = swe.calc_ut(jd, swe.MOON)
    tropical_lon = result[0][0]
    sidereal_lon = (tropical_lon - ayanamsha) % FULL_CIRCLE_DEG
    sign_index = int(sidereal_lon / DEGREES_PER_SIGN)
    return sidereal_lon, sign_index


def _jd_to_date_str(jd: float) -> str:
    """Convert Julian Day to DD/MM/YYYY string.

    Args:
        jd: Julian Day number.

    Returns:
        Date string in DD/MM/YYYY format.
    """
    year, month, day, _hour = swe.revjul(jd)
    return f"{int(day):02d}/{int(month):02d}/{int(year):04d}"


def compute_nisheka(chart: ChartData) -> NishekaResult:
    """Compute the Nisheka (conception) chart from a birth chart.

    Estimates the conception moment using BPHS Ch.4 gestation formula,
    computes the ascendant and Moon at that moment, and verifies against
    the birth chart using the classical cross-check rule.

    Args:
        chart: A computed birth chart with planet positions.

    Returns:
        NishekaResult with conception date, Nisheka lagna/Moon, and
        verification flags.
    """
    # Step 1: Compute conception Julian Day
    conception_jd = _compute_conception_jd(chart)
    days_before = chart.julian_day - conception_jd

    # Step 2: Compute Nisheka lagna (ascendant at conception)
    _nisheka_asc_lon, nisheka_lagna_sign_idx = _compute_sidereal_lagna(
        conception_jd, chart.latitude, chart.longitude
    )

    # Step 3: Compute Moon at conception
    _nisheka_moon_lon, nisheka_moon_sign_idx = _compute_sidereal_moon(conception_jd)

    # Step 4: Verification
    birth_moon_sign_idx = chart.planets["Moon"].sign_index
    birth_lagna_sign_idx = chart.lagna_sign_index

    nisheka_lagna_matches_birth_moon = nisheka_lagna_sign_idx == birth_moon_sign_idx
    birth_lagna_matches_nisheka_moon = birth_lagna_sign_idx == nisheka_moon_sign_idx
    verification_passed = nisheka_lagna_matches_birth_moon or birth_lagna_matches_nisheka_moon

    # Step 5: Build result
    conception_date_str = _jd_to_date_str(conception_jd)
    nisheka_lagna_sign = SIGNS_EN[nisheka_lagna_sign_idx]
    nisheka_moon_sign = SIGNS_EN[nisheka_moon_sign_idx]

    verification_note = (
        "Verification passed"
        if verification_passed
        else "Verification failed — birth time may need rectification"
    )
    summary = (
        f"Conception approx. {days_before:.0f} days before birth "
        f"({conception_date_str}). "
        f"Nisheka Lagna: {nisheka_lagna_sign}, "
        f"Nisheka Moon: {nisheka_moon_sign}. "
        f"{verification_note}."
    )

    return NishekaResult(
        conception_jd=conception_jd,
        conception_date=conception_date_str,
        conception_approx_days_before_birth=round(days_before, 2),
        nisheka_lagna_sign_index=nisheka_lagna_sign_idx,
        nisheka_lagna_sign=nisheka_lagna_sign,
        nisheka_moon_sign_index=nisheka_moon_sign_idx,
        nisheka_moon_sign=nisheka_moon_sign,
        nisheka_lagna_matches_birth_moon=nisheka_lagna_matches_birth_moon,
        birth_lagna_matches_nisheka_moon=birth_lagna_matches_nisheka_moon,
        verification_passed=verification_passed,
        summary=summary,
    )
