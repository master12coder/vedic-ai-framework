"""KP (Krishnamurti Paddhati) Sub-Lord computation.

The zodiac is divided into 243 sub-divisions based on Vimshottari dasha proportions
(27 nakshatras x 9 dasha lords = 243). Each nakshatra (13°20') is divided into 9
sub-parts proportional to dasha years.
"""

from __future__ import annotations

from typing import TypedDict

from daivai_engine.compute.kp_tables import KP_HOUSE_GROUPS
from daivai_engine.constants import (
    DASHA_SEQUENCE,
    DASHA_TOTAL_YEARS,
    DASHA_YEARS,
    NAKSHATRA_LORDS,
    SIGN_LORDS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.kp import KPPosition


__all__ = [
    "KP_HOUSE_GROUPS",
    "check_kp_event_promise",
    "compute_kp_positions",
    "get_kp_position",
    "get_significators",
]


# Pre-compute the 243 sub-divisions (27 nakshatras x 9 sub-lords)
_SUB_TABLE: list[tuple[float, float, str, str, str]] | None = None


def _build_sub_table() -> list[tuple[float, float, str, str, str]]:
    """Build the 243 KP sub-division table.

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

                table.append(
                    (
                        round(ss_start, 6),
                        round(ss_start + ss_span, 6),
                        nak_lord,
                        sub_lord,
                        ss_lord,
                    )
                )
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
        results.append(
            KPPosition(
                name=planet_name,
                longitude=planet_data.longitude,
                sign_lord=SIGN_LORDS[planet_data.sign_index],
                nakshatra_lord=nak_lord,
                sub_lord=sub_lord,
                sub_sub_lord=ss_lord,
                nakshatra=planet_data.nakshatra,
            )
        )
    return results


class _Significators(TypedDict):
    occupies: list[int]
    owns: list[int]
    star_lord_houses: list[int]
    sub_lord_houses: list[int]
    sub_lord: str


def get_significators(chart: ChartData, planet_name: str) -> _Significators:
    """Get house significators for a planet in KP system.

    In KP, a planet signifies houses through (3 levels):
    1. Star Lord level: Houses occupied + owned by the planet's nakshatra lord
    2. Planet level: Houses occupied + owned by the planet itself
    3. Sub Lord level: Houses signified by the planet's sub lord

    Returns:
        Dict with keys 'occupies', 'owns', 'star_lord_houses', 'sub_lord_houses'.
    """
    planet = chart.planets[planet_name]
    star_lord_name = planet.nakshatra_lord
    _, sub_lord_name, _ = get_kp_position(planet.longitude)

    # Houses the star lord occupies and owns
    star_lord = chart.planets.get(star_lord_name)
    star_lord_houses: list[int] = []
    if star_lord:
        star_lord_houses.append(star_lord.house)
        for p in chart.planets.values():
            if p.sign_lord == star_lord_name and p.house not in star_lord_houses:
                star_lord_houses.append(p.house)

    # Houses the planet itself owns
    owns: list[int] = []
    from daivai_engine.compute.chart import get_house_lord

    for h in range(1, 13):
        if get_house_lord(chart, h) == planet_name:
            owns.append(h)

    # Sub lord significators (level 3)
    sub_lord_planet = chart.planets.get(sub_lord_name)
    sub_lord_houses: list[int] = []
    if sub_lord_planet:
        sub_lord_houses.append(sub_lord_planet.house)
        for p in chart.planets.values():
            if p.sign_lord == sub_lord_name and p.house not in sub_lord_houses:
                sub_lord_houses.append(p.house)

    return {
        "occupies": [planet.house],
        "owns": owns,
        "star_lord_houses": sorted(star_lord_houses),
        "sub_lord_houses": sorted(sub_lord_houses),
        "sub_lord": sub_lord_name,
    }


def check_kp_event_promise(
    chart: ChartData,
    event_type: str,
) -> dict:
    """Check KP house groupings to assess if an event is promised in the chart.

    Uses the sub lord of the primary cusp for the event type and checks
    whether it signifies the required houses.

    Args:
        chart: Birth chart.
        event_type: One of the keys in KP_HOUSE_GROUPS.

    Returns:
        Dict with promise_level, sub_lord, significators, and interpretation.
    """
    if event_type not in KP_HOUSE_GROUPS:
        return {
            "event_type": event_type,
            "promise_level": "unknown",
            "error": f"Unknown event type. Use: {list(KP_HOUSE_GROUPS.keys())}",
        }

    group = KP_HOUSE_GROUPS[event_type]
    positive_houses: list[int] = group["positive_houses"]  # type: ignore[assignment]
    negative_houses: list[int] = group["negative_houses"]  # type: ignore[assignment]
    primary_cusp: int = group["primary_cusp"]  # type: ignore[assignment]

    # Find the planet that rules the primary cusp
    cusp_sign = (chart.lagna_sign_index + primary_cusp - 1) % 12
    cusp_lord = SIGN_LORDS[cusp_sign]

    # Get KP position of cusp lord
    cusp_planet = chart.planets.get(cusp_lord)
    if cusp_planet is None:
        return {"event_type": event_type, "promise_level": "low", "note": "Cusp lord unavailable"}

    # Sub lord of the cusp lord's position
    _, sub_lord_name, _ = get_kp_position(cusp_planet.longitude)

    # Get sub lord's significators
    sub_lord_sigs = get_significators(chart, sub_lord_name)
    all_sig_houses = (
        sub_lord_sigs["occupies"] + sub_lord_sigs["owns"] + sub_lord_sigs["star_lord_houses"]
    )
    all_sig_houses = sorted(set(all_sig_houses))

    # Count overlap with positive and negative houses
    positive_overlap = [h for h in positive_houses if h in all_sig_houses]
    negative_overlap = [h for h in negative_houses if h in all_sig_houses]

    # Promise level determination
    if len(positive_overlap) >= 2 and not negative_overlap:
        promise_level = "strong"
    elif len(positive_overlap) >= 1 and len(negative_overlap) <= 1:
        promise_level = "moderate"
    elif len(positive_overlap) >= 1:
        promise_level = "weak"
    else:
        promise_level = "denied"

    return {
        "event_type": event_type,
        "primary_cusp": primary_cusp,
        "cusp_lord": cusp_lord,
        "sub_lord": sub_lord_name,
        "significator_houses": all_sig_houses,
        "positive_houses_matched": positive_overlap,
        "negative_houses_present": negative_overlap,
        "promise_level": promise_level,
        "description": group["description"],
    }
