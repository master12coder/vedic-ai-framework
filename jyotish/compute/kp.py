"""KP (Krishnamurti Paddhati) Sub-Lord computation.

The zodiac is divided into 249 sub-divisions based on Vimshottari dasha proportions.
Each nakshatra (13°20') is divided into 9 sub-parts proportional to dasha years.
"""

from __future__ import annotations

from jyotish.utils.constants import (
    NAKSHATRAS, NAKSHATRA_LORDS, SIGN_LORDS,
    DASHA_SEQUENCE, DASHA_YEARS, DASHA_TOTAL_YEARS,
)
from jyotish.domain.models.kp import KPPosition
from jyotish.domain.models.chart import ChartData


# Pre-compute the 249 sub-divisions
_SUB_TABLE: list[tuple[float, float, str, str, str]] | None = None


def _build_sub_table() -> list[tuple[float, float, str, str, str]]:
    """Build the 249 KP sub-division table.

    Returns list of (start_deg, end_deg, nakshatra_lord, sub_lord, sub_sub_lord).
    """
    global _SUB_TABLE
    if _SUB_TABLE is not None:
        return _SUB_TABLE

    nak_span = 360.0 / 27.0  # 13.3333 degrees
    table = []

    for nak_idx in range(27):
        nak_start = nak_idx * nak_span
        nak_lord = NAKSHATRA_LORDS[nak_idx]
        nak_lord_idx = DASHA_SEQUENCE.index(nak_lord)

        # Sub-divisions proportional to dasha years
        sub_start = nak_start
        for sub_offset in range(9):
            sub_lord_idx = (nak_lord_idx + sub_offset) % 9
            sub_lord = DASHA_SEQUENCE[sub_lord_idx]
            sub_span = nak_span * DASHA_YEARS[sub_lord] / DASHA_TOTAL_YEARS

            # Sub-sub divisions within each sub
            ss_start = sub_start
            for ss_offset in range(9):
                ss_lord_idx = (sub_lord_idx + ss_offset) % 9
                ss_lord = DASHA_SEQUENCE[ss_lord_idx]
                ss_span = sub_span * DASHA_YEARS[ss_lord] / DASHA_TOTAL_YEARS

                table.append((
                    round(ss_start, 6),
                    round(ss_start + ss_span, 6),
                    nak_lord,
                    sub_lord,
                    ss_lord,
                ))
                ss_start += ss_span

            sub_start += sub_span

    _SUB_TABLE = table
    return _SUB_TABLE


def get_kp_position(longitude: float) -> tuple[str, str, str]:
    """Get nakshatra lord, sub lord, sub-sub lord for a longitude.

    Args:
        longitude: Sidereal longitude (0-360)

    Returns:
        (nakshatra_lord, sub_lord, sub_sub_lord)
    """
    lon = longitude % 360.0
    table = _build_sub_table()

    # Binary-ish search — the table is sorted by start degree
    for start, end, nak_lord, sub_lord, ss_lord in table:
        if start <= lon < end:
            return nak_lord, sub_lord, ss_lord

    # Fallback for exact 360.0
    last = table[-1]
    return last[2], last[3], last[4]


def compute_kp_positions(chart: ChartData) -> list[KPPosition]:
    """Compute KP sub-lord positions for all planets in a chart.

    Args:
        chart: Computed birth chart

    Returns:
        List of KPPosition for each planet.
    """
    results = []
    for planet_name, planet_data in chart.planets.items():
        nak_lord, sub_lord, ss_lord = get_kp_position(planet_data.longitude)
        results.append(KPPosition(
            name=planet_name,
            longitude=planet_data.longitude,
            sign_lord=SIGN_LORDS[planet_data.sign_index],
            nakshatra_lord=nak_lord,
            sub_lord=sub_lord,
            sub_sub_lord=ss_lord,
            nakshatra=planet_data.nakshatra,
        ))
    return results


def get_significators(chart: ChartData, planet_name: str) -> dict[str, list[int]]:
    """Get house significators for a planet in KP system.

    In KP, a planet signifies houses through:
    1. Houses it occupies (star lord's houses)
    2. Houses it owns
    3. Houses aspected

    Returns:
        Dict with keys 'occupies', 'owns', 'star_lord_houses'.
    """
    planet = chart.planets[planet_name]
    star_lord_name = planet.nakshatra_lord

    # Houses the star lord occupies and owns
    star_lord = chart.planets.get(star_lord_name)
    star_lord_houses = []
    if star_lord:
        star_lord_houses.append(star_lord.house)
        # Add houses owned by star lord
        for p in chart.planets.values():
            if p.sign_lord == star_lord_name:
                if p.house not in star_lord_houses:
                    star_lord_houses.append(p.house)

    # Houses the planet itself owns
    owns = []
    from jyotish.compute.chart import get_house_lord
    for h in range(1, 13):
        if get_house_lord(chart, h) == planet_name:
            owns.append(h)

    return {
        "occupies": [planet.house],
        "owns": owns,
        "star_lord_houses": star_lord_houses,
    }
