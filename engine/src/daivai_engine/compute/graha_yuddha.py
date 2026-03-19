"""Graha Yuddha (Planetary War) detection.

Two planets within 1 degree of each other are in planetary war.
Only Mars, Mercury, Jupiter, Venus, Saturn participate.
The loser's significations and owned houses are damaged.

Source: Surya Siddhanta + BPHS.
"""

from __future__ import annotations

from itertools import combinations

from daivai_engine.constants import OWN_SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import GrahaYuddha


# Only these 5 planets participate in graha yuddha
_WAR_PLANETS = ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
_WAR_THRESHOLD = 1.0  # degrees
_EXACT_THRESHOLD = 10.0 / 60.0  # 10 arc-minutes in degrees


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

        # Winner: planet with higher longitude wins (in direct motion).
        # Some texts give victory to the retrograde planet — we use
        # the standard higher-longitude rule from Surya Siddhanta.
        if p1.longitude >= p2.longitude:
            winner, loser = p1_name, p2_name
        else:
            winner, loser = p2_name, p1_name

        # Loser's owned houses are affected
        affected = OWN_SIGNS.get(loser, [])
        # Convert sign indices to house numbers (from lagna)
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


def _circular_distance(lon1: float, lon2: float) -> float:
    """Minimum angular distance between two longitudes."""
    diff = abs(lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)
