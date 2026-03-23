"""Shared utilities for transit event computation.

Provides sidereal longitude/speed computation, sign/nakshatra lookup,
angular arithmetic, Julian Day to datetime conversion, and scanning
constants used by transit_finder and eclipse_natal modules.

Source: Surya Siddhanta (astronomical computation principles).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytz
import swisseph as swe

from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    NAKSHATRAS,
    SWE_PLANETS,
)


# ── Constants ────────────────────────────────────────────────────────────────

BINARY_PRECISION = 0.001  # ~1.4 minutes in days
NO_RETROGRADE = {"Sun", "Moon", "Rahu", "Ketu"}

# Step sizes (days) tuned to orbital speed
STEP_SIZES: dict[str, float] = {
    "Moon": 0.25,
    "Mercury": 0.5,
    "Venus": 0.5,
    "Sun": 1.0,
    "Mars": 1.0,
    "Jupiter": 1.0,
    "Saturn": 1.0,
}

ASPECT_NAMES: dict[float, str] = {
    0.0: "conjunction",
    60.0: "sextile",
    90.0: "square",
    120.0: "trine",
    180.0: "opposition",
}


# ── Helpers ──────────────────────────────────────────────────────────────────


def get_swe_id(planet: str) -> int:
    """Return the Swiss Ephemeris planet constant for a given planet name.

    Args:
        planet: Planet name (e.g. "Sun", "Ketu").

    Returns:
        Swiss Ephemeris integer constant.
    """
    if planet == "Ketu":
        return int(SWE_PLANETS["Rahu"])
    return int(SWE_PLANETS[planet])


def sidereal_lon(jd: float, planet: str) -> float:
    """Compute sidereal longitude for *planet* at Julian Day *jd*.

    Args:
        jd: Julian Day (UT).
        planet: Planet name.

    Returns:
        Sidereal longitude in [0, 360).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    swe_id = get_swe_id(planet)
    result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    lon = result[0][0]
    if planet == "Ketu":
        lon = (lon + 180.0) % FULL_CIRCLE_DEG
    # Normalize to [0, 360) — swe can return exactly 360.0 at sign boundaries
    lon = lon % FULL_CIRCLE_DEG
    return float(lon)


def sidereal_speed(jd: float, planet: str) -> float:
    """Compute daily speed (deg/day) for *planet* at Julian Day *jd*.

    Args:
        jd: Julian Day (UT).
        planet: Planet name.

    Returns:
        Speed in degrees per day.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    swe_id = get_swe_id(planet)
    result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    speed = result[0][3]
    if planet == "Ketu":
        speed = -speed
    return float(speed)


def sign_of(lon: float) -> int:
    """Return sign index (0-11) from a sidereal longitude.

    Args:
        lon: Sidereal longitude in degrees.

    Returns:
        Sign index 0 (Aries) through 11 (Pisces).
    """
    return int(lon / DEGREES_PER_SIGN) % 12


def nakshatra_of(lon: float) -> str:
    """Return nakshatra name from sidereal longitude.

    Args:
        lon: Sidereal longitude in degrees.

    Returns:
        Nakshatra name string.
    """
    idx = int(lon / (FULL_CIRCLE_DEG / 27))
    return NAKSHATRAS[min(idx, 26)]


def step_size(planet: str) -> float:
    """Return the scanning step size in days for a planet.

    Args:
        planet: Planet name.

    Returns:
        Step size in days.
    """
    return STEP_SIZES.get(planet, 1.0)


def round_lon(lon: float, decimals: int = 4) -> float:
    """Round a longitude and ensure it stays in [0, 360).

    Args:
        lon: Longitude in degrees.
        decimals: Number of decimal places.

    Returns:
        Rounded longitude in [0, 360).
    """
    return round(lon, decimals) % FULL_CIRCLE_DEG


def angular_diff(a: float, b: float) -> float:
    """Signed shortest-arc difference (a - b) on a 360-degree circle.

    Args:
        a: First longitude in degrees.
        b: Second longitude in degrees.

    Returns:
        Signed difference in [-180, 180).
    """
    d = (a - b) % FULL_CIRCLE_DEG
    if d > 180.0:
        d -= FULL_CIRCLE_DEG
    return d


def jd_to_datetime(jd: float, tz_name: str = "Asia/Kolkata") -> datetime:
    """Convert Julian Day to a timezone-aware datetime.

    Args:
        jd: Julian Day (UT).
        tz_name: IANA timezone name.

    Returns:
        Timezone-aware datetime in the specified zone.
    """
    year, month, day, hour_frac = swe.revjul(jd)
    hours = int(hour_frac)
    remainder = (hour_frac - hours) * 60
    minutes = int(remainder)
    seconds = int((remainder - minutes) * 60)
    utc_dt = datetime(year, month, day, hours, minutes, seconds, tzinfo=UTC)
    tz = pytz.timezone(tz_name)
    return utc_dt.astimezone(tz)
