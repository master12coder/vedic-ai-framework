"""KP Ruling Planets and lagna computation for birth time rectification.

Source: BPHS Ch.4, KP system.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.constants import (
    DAY_PLANET,
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN_DEG,
    SIGN_LORDS,
)
from daivai_engine.models.rectification import RulingPlanets


# ── KP Ruling Planets ───────────────────────────────────────────────────────


def _nak_index_from_longitude(lon: float) -> int:
    """Return nakshatra index (0-26) from sidereal longitude."""
    return int(lon / NAKSHATRA_SPAN_DEG) % 27


def _weekday_lord(jd: float) -> str:
    """Return the day lord for a given Julian Day.

    swe.day_of_week returns: 0=Mon, 1=Tue, ..., 6=Sun.
    DAY_PLANET uses: 0=Sun, 1=Mon, 2=Tue, ...
    """
    dow = swe.day_of_week(jd)  # 0=Mon, 6=Sun
    day_idx = (dow + 1) % 7  # Convert: Mon(0)->1, Sun(6)->0
    return DAY_PLANET.get(day_idx, "Sun")


def get_ruling_planets(jd: float, lat: float, lon: float) -> RulingPlanets:
    """Compute the 5 KP ruling planets for a given moment.

    The five rulers are:
    1. Moon's nakshatra lord
    2. Moon's sign lord
    3. Lagna's nakshatra lord
    4. Lagna's sign lord
    5. Day lord

    Args:
        jd: Julian Day (UT).
        lat: Geographic latitude.
        lon: Geographic longitude.

    Returns:
        RulingPlanets with all 5 rulers and deduplicated list.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd)

    # Moon position
    moon_result = swe.calc_ut(jd, swe.MOON)
    moon_trop = moon_result[0][0]
    moon_sid = (moon_trop - ayanamsha) % FULL_CIRCLE_DEG
    moon_sign_idx = int(moon_sid / DEGREES_PER_SIGN)
    moon_nak_idx = _nak_index_from_longitude(moon_sid)

    moon_nak_lord = NAKSHATRA_LORDS[moon_nak_idx]
    moon_sign_lord = SIGN_LORDS[moon_sign_idx]

    # Lagna position
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    lagna_sid = (ascmc[0] - ayanamsha) % FULL_CIRCLE_DEG
    lagna_sign_idx = int(lagna_sid / DEGREES_PER_SIGN)
    lagna_nak_idx = _nak_index_from_longitude(lagna_sid)

    lagna_nak_lord = NAKSHATRA_LORDS[lagna_nak_idx]
    lagna_sign_lord = SIGN_LORDS[lagna_sign_idx]

    # Day lord
    day_lord = _weekday_lord(jd)

    # Deduplicated unique rulers (preserving order of first appearance)
    all_five = [moon_nak_lord, moon_sign_lord, lagna_nak_lord, lagna_sign_lord, day_lord]
    seen: set[str] = set()
    unique: list[str] = []
    for r in all_five:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    return RulingPlanets(
        moon_nak_lord=moon_nak_lord,
        moon_sign_lord=moon_sign_lord,
        lagna_nak_lord=lagna_nak_lord,
        lagna_sign_lord=lagna_sign_lord,
        day_lord=day_lord,
        unique_rulers=unique,
    )


# ── Lagna computation ───────────────────────────────────────────────────────


def _compute_lagna_for_time(
    base_jd: float,
    time_offset_minutes: float,
    lat: float,
    lon: float,
) -> tuple[float, int, float]:
    """Compute sidereal lagna for an offset from base JD.

    Args:
        base_jd: Base Julian Day.
        time_offset_minutes: Offset in minutes from base.
        lat: Geographic latitude.
        lon: Geographic longitude.

    Returns:
        Tuple of (sidereal_asc_longitude, sign_index, degree_in_sign).
    """
    jd = base_jd + time_offset_minutes / 1440.0
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd)
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    sid_asc = (ascmc[0] - ayanamsha) % FULL_CIRCLE_DEG
    sign_idx = int(sid_asc / DEGREES_PER_SIGN)
    deg_in_sign = sid_asc % DEGREES_PER_SIGN
    return sid_asc, sign_idx, deg_in_sign
