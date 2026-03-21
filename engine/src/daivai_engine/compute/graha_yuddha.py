"""Graha Yuddha (Planetary War) detection.

Two planets within 1 degree of each other are in planetary war.
Only Mars, Mercury, Jupiter, Venus, Saturn participate.
The loser's significations and owned houses are damaged.

Winner determination follows Surya Siddhanta / BPHS:
  1. The planet with greater northern (positive) ecliptic latitude wins.
  2. If both are north, the one with higher north latitude wins.
  3. If both are south, the one with LESS south latitude (closer to ecliptic) wins.
  4. If latitudes are equal/unavailable, higher apparent brightness (lower magnitude) wins;
     as a practical fallback we use inherent planetary brightness rank.

Brightness rank (most to least: Venus > Jupiter > Mars > Mercury > Saturn)
is used when Swiss Ephemeris data is unavailable.

Source: Surya Siddhanta Ch.7, BPHS Ch.3 v30-35.
"""

from __future__ import annotations

from itertools import combinations

import swisseph as swe

from daivai_engine.constants import OWN_SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import GrahaYuddha


# Only these 5 planets participate in graha yuddha — BPHS Ch.3 v30
_WAR_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
_WAR_THRESHOLD = 1.0  # degrees
_EXACT_THRESHOLD = 10.0 / 60.0  # 10 arc-minutes

# Inherent brightness rank (brighter = lower value → wins)
# Surya Siddhanta: Venus > Jupiter > Mars > Mercury > Saturn
_BRIGHTNESS_RANK: dict[str, int] = {
    "Venus": 1,
    "Jupiter": 2,
    "Mars": 3,
    "Mercury": 4,
    "Saturn": 5,
}

# SWE planet IDs
_SWE_IDS: dict[str, int] = {
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}


def detect_planetary_war(chart: ChartData) -> list[GrahaYuddha]:
    """Detect all planetary wars in the chart.

    Args:
        chart: Computed birth chart.

    Returns:
        List of GrahaYuddha for each pair in war. Empty if none.
    """
    results: list[GrahaYuddha] = []
    for p1_name, p2_name in combinations(_WAR_PLANETS, 2):
        p1 = chart.planets.get(p1_name)
        p2 = chart.planets.get(p2_name)
        if p1 is None or p2 is None:
            continue

        sep = _circular_distance(p1.longitude, p2.longitude)
        if sep > _WAR_THRESHOLD:
            continue

        winner, loser = _determine_winner(p1_name, p2_name, chart)

        # Loser's owned signs → convert to house numbers from lagna
        affected = OWN_SIGNS.get(loser, [])
        affected_houses = [((si - chart.lagna_sign_index) % 12) + 1 for si in affected]

        results.append(
            GrahaYuddha(
                planet1=p1_name,
                planet2=p2_name,
                separation_degrees=round(sep, 4),
                winner=winner,
                loser=loser,
                is_exact=sep < _EXACT_THRESHOLD,
                affected_houses=sorted(affected_houses),
            )
        )
    return results


def _determine_winner(p1_name: str, p2_name: str, chart: ChartData) -> tuple[str, str]:
    """Determine winner of graha yuddha using ecliptic latitude.

    Rule (Surya Siddhanta Ch.7 / BPHS Ch.3 v33-35):
      The planet with greater northern ecliptic latitude wins.
      If unavailable, use inherent brightness rank.
    """
    lat1 = _get_ecliptic_latitude(p1_name, chart)
    lat2 = _get_ecliptic_latitude(p2_name, chart)

    if lat1 is not None and lat2 is not None:
        if lat1 > lat2:
            return p1_name, p2_name
        if lat2 > lat1:
            return p2_name, p1_name
        # Equal latitudes — fall through to brightness

    # Brightness fallback: lower rank number = brighter = wins
    rank1 = _BRIGHTNESS_RANK.get(p1_name, 5)
    rank2 = _BRIGHTNESS_RANK.get(p2_name, 5)
    if rank1 <= rank2:
        return p1_name, p2_name
    return p2_name, p1_name


def _get_ecliptic_latitude(planet_name: str, chart: ChartData) -> float | None:
    """Retrieve ecliptic latitude for a planet using Swiss Ephemeris.

    Returns latitude in degrees (positive = north, negative = south),
    or None if unavailable.
    """
    swe_id = _SWE_IDS.get(planet_name)
    if swe_id is None:
        return None

    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
        result = swe.calc_ut(chart.julian_day, swe_id, flags)
        # result[0] = (longitude, latitude, distance, speed_lon, speed_lat, speed_dist)
        lat: float = result[0][1]  # type: ignore[index]
        return lat
    except Exception:
        return None


def _circular_distance(lon1: float, lon2: float) -> float:
    """Minimum angular distance between two longitudes."""
    diff = abs(lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)
