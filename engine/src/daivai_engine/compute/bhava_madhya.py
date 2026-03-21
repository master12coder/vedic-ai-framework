"""Sripati Paddhati — Bhava Madhya (house centers) and Sandhi (boundaries).

In Sripati Paddhati, the Ascendant IS the midpoint (Madhya) of Bhava 1,
not the start of Bhava 1. This is the key distinction from whole-sign
and Placidus systems. The Midheaven (MC) is the Madhya of Bhava 10.

Algorithm:
1. ASC → Bhava 1 Madhya, MC → Bhava 10 Madhya
2. IC (MC+180°) → Bhava 4 Madhya, DSC (ASC+180°) → Bhava 7 Madhya
3. Trisect each quadrant arc to find the remaining 8 Madhyas:
   - MC→ASC arc: Bhava 11 at 1/3, Bhava 12 at 2/3
   - ASC→IC arc: Bhava 2 at 1/3, Bhava 3 at 2/3
   - IC→DSC arc: Bhava 5 at 1/3, Bhava 6 at 2/3
   - DSC→MC arc: Bhava 8 at 1/3, Bhava 9 at 2/3
4. Sandhi between Bhava N and N+1 = zodiacal midpoint of Madhya_N and Madhya_N+1
5. Planet is "in sandhi" if within SANDHI_THRESHOLD (3°20') of any Sandhi point

Source: Sripati Paddhati (Sripati, ~1039 CE); BPHS Ch.27 commentary.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.constants import (
    FULL_CIRCLE_DEG,
    HALF_CIRCLE_DEG,
    PLANETS,
)
from daivai_engine.models.bhava_madhya import (
    BhavaMadhya,
    PlanetSandhiStatus,
    SripatiBhavaMadhyaResult,
)
from daivai_engine.models.chart import ChartData


# Planet is in sandhi if within this many degrees of a house boundary.
# 3°20' = 3.333° = 1 navamsha (traditional threshold from Phaladeepika).
SANDHI_THRESHOLD: float = 10.0 / 3.0  # exactly 3°20'


def _arc_forward(start: float, end: float) -> float:
    """Forward zodiacal arc from start to end (0° to <360°)."""
    return (end - start) % FULL_CIRCLE_DEG


def _zodiacal_point(start: float, arc: float, fraction: float) -> float:
    """Point at `fraction` of `arc` ahead of `start` in zodiacal direction."""
    return (start + arc * fraction) % FULL_CIRCLE_DEG


def _zodiacal_midpoint(a: float, b: float) -> float:
    """Zodiacal midpoint between a and b, going forward from a."""
    arc = _arc_forward(a, b)
    return _zodiacal_point(a, arc, 0.5)


def _circular_distance(a: float, b: float) -> float:
    """Shortest angular distance between two longitudes (0-180 degrees)."""
    diff = abs(a - b) % FULL_CIRCLE_DEG
    if diff > HALF_CIRCLE_DEG:
        diff = FULL_CIRCLE_DEG - diff
    return diff


def compute_sripati_madhyas(chart: ChartData) -> dict[int, float]:
    """Compute the 12 Bhava Madhya longitudes using Sripati Paddhati.

    Args:
        chart: A fully computed ChartData instance.

    Returns:
        Dict mapping house number (1-12) to Madhya longitude (sidereal).
    """
    jd = chart.julian_day
    lat = chart.latitude
    lon_geo = chart.longitude

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    # Whole-sign houses (b"W") gives us ASC/MC in ascmc array
    _, ascmc = swe.houses_ex(jd, lat, lon_geo, b"W")
    tropical_asc: float = ascmc[0]
    tropical_mc: float = ascmc[1]

    # Convert angles to sidereal
    asc = (tropical_asc - ayanamsha) % FULL_CIRCLE_DEG
    mc = (tropical_mc - ayanamsha) % FULL_CIRCLE_DEG
    ic = (mc + HALF_CIRCLE_DEG) % FULL_CIRCLE_DEG
    dsc = (asc + HALF_CIRCLE_DEG) % FULL_CIRCLE_DEG

    madhyas: dict[int, float] = {
        1: asc,
        4: ic,
        7: dsc,
        10: mc,
    }

    # Trisect each quadrant arc
    # MC → ASC: houses 11 (1/3) and 12 (2/3)
    arc_mc_asc = _arc_forward(mc, asc)
    madhyas[11] = _zodiacal_point(mc, arc_mc_asc, 1.0 / 3.0)
    madhyas[12] = _zodiacal_point(mc, arc_mc_asc, 2.0 / 3.0)

    # ASC → IC: houses 2 (1/3) and 3 (2/3)
    arc_asc_ic = _arc_forward(asc, ic)
    madhyas[2] = _zodiacal_point(asc, arc_asc_ic, 1.0 / 3.0)
    madhyas[3] = _zodiacal_point(asc, arc_asc_ic, 2.0 / 3.0)

    # IC → DSC: houses 5 (1/3) and 6 (2/3)
    arc_ic_dsc = _arc_forward(ic, dsc)
    madhyas[5] = _zodiacal_point(ic, arc_ic_dsc, 1.0 / 3.0)
    madhyas[6] = _zodiacal_point(ic, arc_ic_dsc, 2.0 / 3.0)

    # DSC → MC: houses 8 (1/3) and 9 (2/3)
    arc_dsc_mc = _arc_forward(dsc, mc)
    madhyas[8] = _zodiacal_point(dsc, arc_dsc_mc, 1.0 / 3.0)
    madhyas[9] = _zodiacal_point(dsc, arc_dsc_mc, 2.0 / 3.0)

    return madhyas


def compute_sripati_bhava_madhya(chart: ChartData) -> SripatiBhavaMadhyaResult:
    """Compute Sripati Paddhati Bhava Madhyas and Sandhis for a chart.

    The 12 Bhava Madhyas (house centers) are computed from the Ascendant
    and Midheaven by trisecting the four quadrant arcs.  The Sandhi between
    adjacent houses is the zodiacal midpoint of their Madhyas.  Each planet
    is classified as "in sandhi" if within 3°20' of any house boundary.

    Args:
        chart: A fully computed ChartData instance.

    Returns:
        SripatiBhavaMadhyaResult with all Madhyas, Sandhis, and planet statuses.
    """
    madhyas = compute_sripati_madhyas(chart)

    # Compute arc_span and sandhi for each house
    bhavas: dict[int, BhavaMadhya] = {}
    sandhis: dict[int, float] = {}  # sandhis[n] = sandhi between house n and n+1

    for h in range(1, 13):
        next_h = (h % 12) + 1
        sandhi_lon = _zodiacal_midpoint(madhyas[h], madhyas[next_h])
        sandhis[h] = sandhi_lon

    for h in range(1, 13):
        prev_h = ((h - 2) % 12) + 1
        # arc_span = arc from sandhi of (prev_h→h) to sandhi of (h→next_h)
        sandhi_start = sandhis[prev_h]
        sandhi_end = sandhis[h]
        arc_span = _arc_forward(sandhi_start, sandhi_end)

        bhavas[h] = BhavaMadhya(
            house=h,
            madhya_longitude=round(madhyas[h], 4),
            sandhi_longitude=round(sandhis[h], 4),
            arc_span=round(arc_span, 4),
        )

    # Build ordered list of sandhis for planet assignment
    # sandhi_list[i] = (longitude, house_before, house_after)
    sandhi_list: list[tuple[float, int, int]] = []
    for h in range(1, 13):
        next_h = (h % 12) + 1
        sandhi_list.append((sandhis[h], h, next_h))

    # Classify each planet
    planet_status: dict[str, PlanetSandhiStatus] = {}
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        p_lon = p.longitude % FULL_CIRCLE_DEG

        # Find which Bhava this planet belongs to:
        # It belongs to house H if it falls between sandhi(H-1→H) and sandhi(H→H+1)
        assigned_house = _find_sripati_house(p_lon, sandhis)

        # Distance to this Bhava's Madhya
        dist_madhya = _circular_distance(p_lon, madhyas[assigned_house])

        # Distance to nearest Sandhi
        min_sandhi_dist = FULL_CIRCLE_DEG
        for sandhi_lon, _h_before, _h_after in sandhi_list:
            d = _circular_distance(p_lon, sandhi_lon)
            if d < min_sandhi_dist:
                min_sandhi_dist = d

        prev_h = ((assigned_house - 2) % 12) + 1
        next_h = (assigned_house % 12) + 1

        planet_status[planet_name] = PlanetSandhiStatus(
            name=planet_name,
            bhava=assigned_house,
            distance_to_madhya=round(dist_madhya, 4),
            distance_to_sandhi=round(min_sandhi_dist, 4),
            is_in_sandhi=min_sandhi_dist < SANDHI_THRESHOLD,
            prev_house=prev_h,
            next_house=next_h,
        )

    return SripatiBhavaMadhyaResult(
        bhavas=bhavas,
        planet_status=planet_status,
    )


def _find_sripati_house(p_lon: float, sandhis: dict[int, float]) -> int:
    """Find which Sripati Bhava a longitude falls in.

    A planet falls in house H if it is between sandhi(H-1, H) and sandhi(H, H+1),
    measured in the forward zodiacal direction.

    Args:
        p_lon: Sidereal longitude (0-360) of the planet.
        sandhis: Dict mapping house N → sandhi longitude between house N and N+1.

    Returns:
        House number 1-12.
    """
    for h in range(1, 13):
        prev_h = ((h - 2) % 12) + 1
        start_sandhi = sandhis[prev_h]
        end_sandhi = sandhis[h]
        arc = _arc_forward(start_sandhi, end_sandhi)
        dist_from_start = _arc_forward(start_sandhi, p_lon)
        if dist_from_start < arc:
            return h

    # Fallback: return house whose Madhya is nearest (should not reach here)
    madhyas_list = {h: sandhis[h] for h in range(1, 13)}
    nearest = min(madhyas_list, key=lambda h: _circular_distance(p_lon, madhyas_list[h]))
    return nearest


def get_sandhi_planets(chart: ChartData) -> list[PlanetSandhiStatus]:
    """Return only planets that are in a Sandhi zone (within 3°20' of a house boundary).

    Args:
        chart: A fully computed ChartData instance.

    Returns:
        List of PlanetSandhiStatus for each planet in sandhi. Empty if none.
    """
    result = compute_sripati_bhava_madhya(chart)
    return [ps for ps in result.planet_status.values() if ps.is_in_sandhi]


def get_planets_near_madhya(chart: ChartData, threshold: float = 5.0) -> list[PlanetSandhiStatus]:
    """Return planets close to their Bhava Madhya (within threshold degrees).

    Planets near the Madhya are powerfully placed — they express the house's
    full significations most directly.

    Args:
        chart: A fully computed ChartData instance.
        threshold: Maximum degrees from Madhya (default 5°).

    Returns:
        List of PlanetSandhiStatus for planets near their Madhya.
    """
    result = compute_sripati_bhava_madhya(chart)
    return [ps for ps in result.planet_status.values() if ps.distance_to_madhya <= threshold]
