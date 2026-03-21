"""Varshphal (Annual Chart / Solar Return / Tajaka system).

Computes the chart for the exact moment the transiting Sun returns to
its natal sidereal longitude in a given year. Used for annual predictions.

Source: Tajaka Neelakanthi, Dr. B.V. Raman's Varshphal.
"""

from __future__ import annotations

from datetime import UTC, datetime

import swisseph as swe

from daivai_engine.compute.chart import compute_chart
from daivai_engine.compute.tajaka_yogas import TajakaYoga, detect_all_tajaka_yogas
from daivai_engine.constants import DAY_PLANET
from daivai_engine.models.chart import ChartData


def compute_varshphal(
    birth_chart: ChartData,
    year: int,
) -> dict:
    """Compute Varshphal (annual chart) for a given year.

    Steps:
    1. Find exact moment Sun returns to natal longitude in the given year
    2. Compute chart for that moment at birth place
    3. Compute Muntha sign
    4. Determine Year Lord (day of week of solar return)

    Args:
        birth_chart: Original birth chart.
        year: Calendar year for the annual chart (e.g. 2026).

    Returns:
        Dict with solar_return_date, muntha, year_lord, chart, tajaka_yogas.
    """
    natal_sun_lon = birth_chart.planets["Sun"].longitude

    # Find solar return Julian Day via binary search
    sr_jd = _find_solar_return(natal_sun_lon, year)
    sr_date = _jd_to_datetime(sr_jd)

    # Compute chart for that moment
    sr_dob = sr_date.strftime("%d/%m/%Y")
    sr_tob = sr_date.strftime("%H:%M")
    sr_chart = compute_chart(
        name=f"{birth_chart.name} Varshphal {year}",
        dob=sr_dob,
        tob=sr_tob,
        lat=birth_chart.latitude,
        lon=birth_chart.longitude,
        tz_name=birth_chart.timezone_name,
        gender=birth_chart.gender,
    )

    # Muntha: (year - birth_year) signs forward from birth lagna
    birth_year = int(birth_chart.dob.split("/")[2])
    age = year - birth_year
    muntha_sign = (birth_chart.lagna_sign_index + age) % 12
    muntha_lord = _sign_lord(muntha_sign)

    # Year lord: based on day of week of solar return
    weekday = sr_date.weekday()  # Monday=0, Sunday=6
    # Convert to our DAY_PLANET mapping (Sunday=0, Monday=1...)
    day_idx = (weekday + 1) % 7
    year_lord = DAY_PLANET.get(day_idx, "Sun")

    # Full 16 Tajaka yoga detection using tajaka_yogas module
    tajaka: list[TajakaYoga] = detect_all_tajaka_yogas(sr_chart)

    return {
        "year": year,
        "solar_return_date": sr_date.strftime("%Y-%m-%d %H:%M:%S"),
        "solar_return_jd": sr_jd,
        "muntha_sign": muntha_sign,
        "muntha_lord": muntha_lord,
        "year_lord": year_lord,
        "chart": sr_chart,
        "tajaka_yogas": tajaka,
    }


def _find_solar_return(natal_sun_lon: float, year: int) -> float:
    """Find the Julian Day when Sun returns to natal longitude in given year.

    Uses coarse scan + binary search on Swiss Ephemeris sidereal Sun longitude.
    The Sun moves ~1°/day, completing 360° in ~365.25 days.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Start search from Jan 1 of the year, end Dec 31
    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year, 12, 31, 23.99)

    # Coarse scan: find day when Sun's absolute longitude crosses natal lon
    # Use raw longitude difference (not wrapped) to detect the REAL crossing
    jd = jd_start
    prev_lon = _sun_lon(jd)
    while jd < jd_end:
        jd += 1.0
        cur_lon = _sun_lon(jd)
        # Check if natal_sun_lon falls between prev_lon and cur_lon
        # Handle the 360→0 wrap: if prev > 350 and cur < 10, Sun crossed 0°
        crossed = False
        if prev_lon <= cur_lon:
            # Normal: no wrap
            crossed = prev_lon <= natal_sun_lon < cur_lon
        else:
            # Wrapped: prev > cur (crossed 360°)
            crossed = natal_sun_lon >= prev_lon or natal_sun_lon < cur_lon
        if crossed:
            # Binary search within this day
            lo, hi = jd - 1.0, jd
            for _ in range(50):
                mid = (lo + hi) / 2.0
                mid_diff = _sun_diff(mid, natal_sun_lon)
                if mid_diff < 0:
                    lo = mid
                else:
                    hi = mid
            sr_jd: float = (lo + hi) / 2.0
            return sr_jd
        prev_lon = cur_lon

    # Fallback: return approximate birthday JD
    fallback: float = swe.julday(year, 3, 13, 12.0)
    return fallback


def _sun_lon(jd: float) -> float:
    """Get sidereal Sun longitude at a Julian Day."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    result = swe.calc_ut(jd, swe.SUN, flags)
    lon: float = result[0][0]  # type: ignore[index]
    return lon


def _sun_diff(jd: float, target_lon: float) -> float:
    """Signed difference between current Sun longitude and target (-180..+180)."""
    sun_lon = _sun_lon(jd)
    diff = sun_lon - target_lon
    if diff > 180:
        diff -= 360
    if diff < -180:
        diff += 360
    return diff


def _jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to datetime (UTC)."""
    year, month, day, hour = swe.revjul(jd)
    h = int(hour)
    m = int((hour - h) * 60)
    return datetime(year, month, day, h, m, tzinfo=UTC)


def _sign_lord(sign_idx: int) -> str:
    """Get lord of a sign by index."""
    from daivai_engine.constants import SIGN_LORDS

    return SIGN_LORDS.get(sign_idx, "Sun")
