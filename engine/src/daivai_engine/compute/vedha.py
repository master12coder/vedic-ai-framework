"""Vedha (transit obstruction) — blocks transit benefits.

When a planet transits a favorable house from natal Moon, another planet
in the vedha position cancels the good result.

Vedha pairs from Moon:
  1 ↔ 5, 2 ↔ 12, 3 ↔ 9, 4 ↔ 10, 6 ↔ 8
  (7 and 11 have no vedha — benefits always active)

Source: Phaladeepika transit chapter.
"""

from __future__ import annotations

from daivai_engine.models.chart import ChartData
from daivai_engine.models.special import VedhaPoint


# Vedha pairs: house -> its vedha house (from Moon)
_VEDHA_PAIRS: dict[int, int] = {
    1: 5,
    5: 1,
    2: 12,
    12: 2,
    3: 9,
    9: 3,
    4: 10,
    10: 4,
    6: 8,
    8: 6,
}


def check_vedha(
    chart: ChartData,
    transit_planet: str,
    transit_sign: int,
) -> list[VedhaPoint]:
    """Check vedha for a transiting planet.

    Args:
        chart: Natal chart.
        transit_planet: Name of transiting planet.
        transit_sign: Sign index (0-11) where planet is transiting.

    Returns:
        List of VedhaPoint for houses that have vedha pairs.
    """
    moon_sign = chart.planets["Moon"].sign_index
    transit_house = ((transit_sign - moon_sign) % 12) + 1

    # Get vedha house for this transit position
    vedha_house = _VEDHA_PAIRS.get(transit_house)
    if vedha_house is None:
        # No vedha for houses 7 and 11
        return []

    # Check if any planet occupies the vedha house (from Moon)
    vedha_sign = (moon_sign + vedha_house - 1) % 12
    blocker = None
    for name, p in chart.planets.items():
        if name == transit_planet:
            continue
        if p.sign_index == vedha_sign:
            blocker = name
            break

    return [
        VedhaPoint(
            benefic_house=transit_house,
            vedha_house=vedha_house,
            is_blocked=blocker is not None,
            blocking_planet=blocker,
        )
    ]
