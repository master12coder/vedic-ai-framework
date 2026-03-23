"""Eclipse-natal chart impact analysis.

Finds solar and lunar eclipses within a date range and computes their
impact on natal chart positions — checking proximity of the eclipse
point to natal planets and lagna.

Source: BPHS Ch.27, Surya Siddhanta.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.compute.eclipse_natal_helpers import (
    DEFAULT_IMPACT_ORB,
    ECLIPSE_NODE_ORB,
    SIGNIFICATIONS,
    classify_severity,
    find_full_moons,
    find_new_moons,
    orb_between,
    sidereal_lon_by_id,
)
from daivai_engine.compute.transit_finder_utils import (
    jd_to_datetime,
    nakshatra_of,
    sign_of,
)
from daivai_engine.constants import (
    FULL_CIRCLE_DEG,
    PLANETS,
    SIGN_LORDS,
    SIGNS,
    SWE_PLANETS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.eclipse_natal import (
    EclipseData,
    EclipseNatalResult,
    NatalImpact,
)


# ── Backward-compatible aliases (used by eclipse_natal imports) ────────────
_nakshatra_of = nakshatra_of
_sign_of = sign_of
_sidereal_lon = sidereal_lon_by_id
_orb_between = orb_between
_classify_severity = classify_severity
_find_new_moons = find_new_moons
_find_full_moons = find_full_moons
_ECLIPSE_NODE_ORB = ECLIPSE_NODE_ORB
_DEFAULT_IMPACT_ORB = DEFAULT_IMPACT_ORB
_SIGNIFICATIONS = SIGNIFICATIONS


# ── Public API ───────────────────────────────────────────────────────────────


def find_eclipses(start_jd: float, end_jd: float) -> list[EclipseData]:
    """Find solar and lunar eclipses in the given Julian Day range.

    Solar eclipses occur at New Moons within ~18 deg of Rahu/Ketu axis.
    Lunar eclipses occur at Full Moons within ~18 deg of Rahu/Ketu axis.

    Args:
        start_jd: Start Julian Day.
        end_jd: End Julian Day.

    Returns:
        List of EclipseData sorted chronologically.

    Source: Surya Siddhanta — eclipse conditions.
    """
    eclipses: list[EclipseData] = []

    # Solar eclipses at New Moons near nodes
    for nm_jd in find_new_moons(start_jd, end_jd):
        sun_lon = sidereal_lon_by_id(nm_jd, swe.SUN)
        rahu_lon = sidereal_lon_by_id(nm_jd, SWE_PLANETS["Rahu"])
        ketu_lon = (rahu_lon + 180.0) % FULL_CIRCLE_DEG

        if (
            orb_between(sun_lon, rahu_lon) <= ECLIPSE_NODE_ORB
            or orb_between(sun_lon, ketu_lon) <= ECLIPSE_NODE_ORB
        ):
            si = sign_of(sun_lon)
            dt = jd_to_datetime(nm_jd)
            eclipses.append(
                EclipseData(
                    eclipse_type="solar",
                    date=dt.strftime("%d/%m/%Y"),
                    julian_day=round(nm_jd, 6),
                    longitude=round(sun_lon, 4),
                    sign_index=si,
                    sign=SIGNS[si],
                    nakshatra=nakshatra_of(sun_lon),
                )
            )

    # Lunar eclipses at Full Moons near nodes
    for fm_jd in find_full_moons(start_jd, end_jd):
        moon_lon = sidereal_lon_by_id(fm_jd, swe.MOON)
        rahu_lon = sidereal_lon_by_id(fm_jd, SWE_PLANETS["Rahu"])
        ketu_lon = (rahu_lon + 180.0) % FULL_CIRCLE_DEG

        if (
            orb_between(moon_lon, rahu_lon) <= ECLIPSE_NODE_ORB
            or orb_between(moon_lon, ketu_lon) <= ECLIPSE_NODE_ORB
        ):
            si = sign_of(moon_lon)
            dt = jd_to_datetime(fm_jd)
            eclipses.append(
                EclipseData(
                    eclipse_type="lunar",
                    date=dt.strftime("%d/%m/%Y"),
                    julian_day=round(fm_jd, 6),
                    longitude=round(moon_lon, 4),
                    sign_index=si,
                    sign=SIGNS[si],
                    nakshatra=nakshatra_of(moon_lon),
                )
            )

    eclipses.sort(key=lambda e: e.julian_day)
    return eclipses


def compute_eclipse_natal_impact(
    chart: ChartData,
    eclipse: EclipseData,
    orb: float = DEFAULT_IMPACT_ORB,
) -> EclipseNatalResult:
    """Compute the impact of a single eclipse on a natal chart.

    Checks proximity of eclipse longitude to all 9 natal planets + lagna.

    Args:
        chart: Natal chart data.
        eclipse: Eclipse event data.
        orb: Maximum orb in degrees (default 5.0).

    Returns:
        EclipseNatalResult with sorted impacts and activation details.

    Source: BPHS Ch.27 — eclipse effects are proportional to proximity.
    """
    impacts: list[NatalImpact] = []

    # Check all natal planets
    for pname in PLANETS:
        if pname not in chart.planets:
            continue
        pd = chart.planets[pname]
        o = orb_between(eclipse.longitude, pd.longitude)
        house = pd.house
        impacts.append(
            NatalImpact(
                natal_point=pname,
                natal_longitude=round(pd.longitude, 4),
                orb=round(o, 4),
                is_hit=o <= orb,
                severity=classify_severity(o),
                house_affected=house,
                significations=SIGNIFICATIONS.get(pname, []),
            )
        )

    # Check lagna
    lagna_orb = orb_between(eclipse.longitude, chart.lagna_longitude)
    impacts.append(
        NatalImpact(
            natal_point="Lagna",
            natal_longitude=round(chart.lagna_longitude, 4),
            orb=round(lagna_orb, 4),
            is_hit=lagna_orb <= orb,
            severity=classify_severity(lagna_orb),
            house_affected=1,
            significations=SIGNIFICATIONS.get("Lagna", []),
        )
    )

    # Sort by orb (tightest first)
    impacts.sort(key=lambda i: i.orb)

    # Determine most affected
    hit_impacts = [i for i in impacts if i.is_hit]
    most_planet = hit_impacts[0].natal_point if hit_impacts else None
    most_house = hit_impacts[0].house_affected if hit_impacts else None

    # Houses activated: houses whose lords are hit
    houses_activated: list[int] = []
    hit_names = {i.natal_point for i in hit_impacts}
    for si in range(12):
        lord = SIGN_LORDS[si]
        if lord in hit_names:
            house_num = ((si - chart.lagna_sign_index) % 12) + 1
            if house_num not in houses_activated:
                houses_activated.append(house_num)
    houses_activated.sort()

    is_significant = any(i.severity in ("exact", "strong") for i in impacts)

    # Build summary
    if hit_impacts:
        top = hit_impacts[0]
        summary = (
            f"{eclipse.eclipse_type.title()} eclipse in {eclipse.sign} "
            f"most closely affects natal {top.natal_point} "
            f"(orb {top.orb:.1f} deg, house {top.house_affected})"
        )
    else:
        summary = (
            f"{eclipse.eclipse_type.title()} eclipse in {eclipse.sign} "
            f"has no significant natal impacts within {orb} deg orb"
        )

    return EclipseNatalResult(
        eclipse=eclipse,
        impacts=impacts,
        most_affected_planet=most_planet,
        most_affected_house=most_house,
        houses_activated=houses_activated,
        is_significant=is_significant,
        summary=summary,
    )


def compute_upcoming_eclipse_impacts(
    chart: ChartData,
    start_jd: float,
    years: int = 1,
) -> list[EclipseNatalResult]:
    """Find all eclipses in the period and compute their natal impact.

    Args:
        chart: Natal chart data.
        start_jd: Start Julian Day.
        years: Number of years to scan (default 1).

    Returns:
        List of EclipseNatalResult sorted chronologically.

    Source: BPHS Ch.27, Surya Siddhanta.
    """
    end_jd = start_jd + years * 365.25
    eclipses = find_eclipses(start_jd, end_jd)
    return [compute_eclipse_natal_impact(chart, ecl) for ecl in eclipses]
