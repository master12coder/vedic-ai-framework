"""Bhava Chalit chart computation using Placidus house cusps.

Computes sidereal Placidus house cusps and determines which Bhava (house)
each planet falls in, comparing with whole-sign Rashi placement to flag
any "bhava shift" planets whose house assignment differs between systems.
"""

from __future__ import annotations

import swisseph as swe

from jyotish.utils.constants import PLANETS
from jyotish.domain.models.chart import ChartData
from jyotish.domain.models.bhava_chalit import BhavaChalitResult, BhavaPlanet


def _normalize(deg: float) -> float:
    """Normalize a degree value to the 0-360 range."""
    return deg % 360.0


def _angular_distance(a: float, b: float) -> float:
    """Shortest angular distance from a to b (always positive, 0-180)."""
    diff = abs(a - b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff


def _longitude_in_range(lon: float, start: float, end: float) -> bool:
    """Check if longitude falls in the arc from start to end (going forward).

    Handles the 360/0 degree wrap-around correctly.
    """
    lon = _normalize(lon)
    start = _normalize(start)
    end = _normalize(end)

    if start <= end:
        return start <= lon < end
    else:
        # Wraps around 0 degrees
        return lon >= start or lon < end


def _find_bhava_house(lon: float, cusps: list[float]) -> int:
    """Determine which Bhava house (1-12) a longitude falls in.

    The planet belongs to house N if its longitude falls between
    cusp[N-1] and cusp[N] (with cusp indices wrapping at 12).
    """
    lon = _normalize(lon)
    for i in range(12):
        cusp_start = cusps[i]
        cusp_end = cusps[(i + 1) % 12]
        if _longitude_in_range(lon, cusp_start, cusp_end):
            return i + 1

    # Fallback: find nearest cusp (should not normally reach here)
    min_dist = 999.0
    nearest = 1
    for i in range(12):
        dist = _angular_distance(lon, cusps[i])
        if dist < min_dist:
            min_dist = dist
            nearest = i + 1
    return nearest


def _nearest_cusp(lon: float, cusps: list[float]) -> float:
    """Return the longitude of the cusp nearest to the given longitude."""
    lon = _normalize(lon)
    min_dist = 999.0
    nearest_cusp_lon = cusps[0]
    for cusp in cusps:
        dist = _angular_distance(lon, cusp)
        if dist < min_dist:
            min_dist = dist
            nearest_cusp_lon = cusp
    return nearest_cusp_lon


def compute_bhava_chalit(chart: ChartData) -> BhavaChalitResult:
    """Compute Bhava Chalit chart from a birth chart.

    Uses Placidus house cusps from Swiss Ephemeris, converted to sidereal
    by subtracting the Lahiri ayanamsha.  Each planet is placed in the
    Bhava it falls in based on cusp ranges, and compared against its
    whole-sign (Rashi) house for bhava-shift detection.

    Args:
        chart: A fully computed ChartData instance.

    Returns:
        BhavaChalitResult with 12 sidereal cusps and per-planet placements.
    """
    jd = chart.julian_day
    lat = chart.latitude
    lon = chart.longitude

    # Set ayanamsha for sidereal conversion
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    # Compute Placidus cusps (tropical) — swe.houses returns (cusps, ascmc)
    # cusps is a tuple of 12 values (indices 0-11 for houses 1-12)
    tropical_cusps, _ = swe.houses(jd, lat, lon, b'P')

    # Convert to sidereal
    sidereal_cusps: list[float] = []
    for i in range(12):
        sid_cusp = _normalize(tropical_cusps[i] - ayanamsha)
        sidereal_cusps.append(round(sid_cusp, 4))

    # Determine Bhava house for each planet
    planets: dict[str, BhavaPlanet] = {}

    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        planet_lon = _normalize(p.longitude)

        # Rashi house is the whole-sign house already stored
        rashi_house = p.house

        # Bhava Chalit house from cusp ranges
        bhava_house = _find_bhava_house(planet_lon, sidereal_cusps)

        # Detect bhava shift
        has_shift = rashi_house != bhava_house

        # Find nearest cusp longitude
        nearest = _nearest_cusp(planet_lon, sidereal_cusps)

        planets[planet_name] = BhavaPlanet(
            name=planet_name,
            rashi_house=rashi_house,
            bhava_house=bhava_house,
            has_bhava_shift=has_shift,
            cusp_longitude=round(nearest, 4),
        )

    return BhavaChalitResult(cusps=sidereal_cusps, planets=planets)


def get_bhava_shifted_planets(chart: ChartData) -> list[BhavaPlanet]:
    """Return only planets whose Bhava house differs from Rashi house."""
    result = compute_bhava_chalit(chart)
    return [bp for bp in result.planets.values() if bp.has_bhava_shift]


def get_planets_in_bhava(chart: ChartData, house_num: int) -> list[BhavaPlanet]:
    """Return all planets in a specific Bhava Chalit house."""
    result = compute_bhava_chalit(chart)
    return [bp for bp in result.planets.values() if bp.bhava_house == house_num]
