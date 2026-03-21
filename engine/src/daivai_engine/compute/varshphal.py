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

    # Tri-pataki Chakra: Sun, Moon, and Lagna in the annual chart
    # show 3 distinct areas of life most activated in this solar year
    tri_pataki = compute_tri_pataki(sr_chart, muntha_sign)

    return {
        "year": year,
        "solar_return_date": sr_date.strftime("%Y-%m-%d %H:%M:%S"),
        "solar_return_jd": sr_jd,
        "muntha_sign": muntha_sign,
        "muntha_lord": muntha_lord,
        "year_lord": year_lord,
        "chart": sr_chart,
        "tajaka_yogas": tajaka,
        "tri_pataki": tri_pataki,
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


# ── Tri-pataki Chakra ─────────────────────────────────────────────────────────


def compute_tri_pataki(sr_chart: ChartData, muntha_sign: int) -> dict:
    """Compute the Tri-pataki Chakra for the annual chart.

    The Tri-pataki ("three-stake") Chakra identifies three zones of intense
    annual activity based on the annual chart:
      1. Lagna sector — personal health, body, self-projection
      2. Muntha sector — the progressed ascendant (most critical sign of the year)
      3. Year Lord sector — the planet that owns the weekday of solar return

    Each sector covers the sign itself plus its 5th and 9th (trikona) signs,
    forming a "triangle" of activation. Planets in these triangles become
    especially significant for the year.

    Interpretation:
    - Muntha Trikona planets: govern the primary themes of the year
    - Year Lord Trikona planets: govern timing and triggering events
    - Lagna Trikona planets: govern the native's personal experience

    Source: Tajaka Neelakanthi, Varshphal (Annual Chart) traditions.
    """
    from daivai_engine.constants import SIGNS

    lagna_sign = sr_chart.lagna_sign_index

    # Three stakes (tri-pataki signs = the sign, 5th from it, 9th from it)
    def _trikona(sign: int) -> list[int]:
        return [sign, (sign + 4) % 12, (sign + 8) % 12]

    lagna_trikona = _trikona(lagna_sign)
    muntha_trikona = _trikona(muntha_sign)

    # Year lord's sign for trikona (use year lord's annual chart placement)
    year_lord_name = _sign_lord(lagna_sign)  # The year lord planet
    year_lord_planet = sr_chart.planets.get(year_lord_name)
    year_lord_sign_idx = year_lord_planet.sign_index if year_lord_planet else lagna_sign
    year_lord_trikona = _trikona(year_lord_sign_idx)

    # Find planets activated in each sector
    def _planets_in(trikona: list[int]) -> list[str]:
        return [name for name, p in sr_chart.planets.items() if p.sign_index in trikona]

    lagna_sector_planets = _planets_in(lagna_trikona)
    muntha_sector_planets = _planets_in(muntha_trikona)
    year_lord_sector_planets = _planets_in(year_lord_trikona)

    # Muntha aspects: does any planet aspect the Muntha sign?
    # A planet in 7th from Muntha aspects it directly
    muntha_aspected_by = [
        name for name, p in sr_chart.planets.items() if ((p.sign_index - muntha_sign) % 12) + 1 == 7
    ]

    return {
        "lagna_sector": {
            "anchor_sign": lagna_sign,
            "anchor_sign_name": SIGNS[lagna_sign],
            "trikona_signs": [SIGNS[s] for s in lagna_trikona],
            "activated_planets": lagna_sector_planets,
            "theme": "Personal health, body, and self-expression for the year",
        },
        "muntha_sector": {
            "anchor_sign": muntha_sign,
            "anchor_sign_name": SIGNS[muntha_sign],
            "trikona_signs": [SIGNS[s] for s in muntha_trikona],
            "activated_planets": muntha_sector_planets,
            "aspected_by": muntha_aspected_by,
            "theme": "Primary karmic theme and key events of the year",
        },
        "year_lord_sector": {
            "year_lord": year_lord_name,
            "anchor_sign": year_lord_sign_idx,
            "anchor_sign_name": SIGNS[year_lord_sign_idx],
            "trikona_signs": [SIGNS[s] for s in year_lord_trikona],
            "activated_planets": year_lord_sector_planets,
            "theme": "Timing and triggering of major events through the year",
        },
    }
