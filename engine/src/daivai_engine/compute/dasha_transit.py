"""Dasha-Transit integration — the #1 predictive timing technique.

Combines running Vimshottari dasha lords with their transit positions,
Bhinnashtakavarga (BAV) strength, and double transit activation of
houses they own. This answers "WHEN will X happen?"

Source: BPHS Ch.25, Phaladeepika Ch.26.
"""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.dasha import find_current_dasha
from daivai_engine.compute.dasha_transit_helpers import (
    _check_double_transit_on_houses,
    _check_mutual_aspect,
    _classify_bav,
    _get_dignity,
    _get_houses_owned,
    _get_relationship,
    _get_transit_position,
)
from daivai_engine.compute.dasha_transit_scoring import (
    build_summary,
    compute_overall_favorability,
    compute_score,
    score_to_favorability,
)
from daivai_engine.compute.datetime_utils import now_ist, to_jd
from daivai_engine.constants import DEGREES_PER_SIGN
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_transit import (
    DashaLordTransit,
    DashaTransitAnalysis,
)


# House significations for event domain mapping
_HOUSE_DOMAINS: dict[int, str] = {
    1: "self/health",
    2: "wealth/family",
    3: "siblings/courage",
    4: "home/mother",
    5: "children/creativity",
    6: "enemies/disease",
    7: "marriage/partnership",
    8: "transformation/longevity",
    9: "fortune/father",
    10: "career/status",
    11: "gains/income",
    12: "loss/liberation",
}


def compute_dasha_transit(
    chart: ChartData,
    target_date: datetime | None = None,
) -> DashaTransitAnalysis:
    """Compute complete dasha-transit integration analysis.

    This is the PRIMARY timing technique for professional Vedic astrology
    prediction. It combines:
      1. Current dasha lords (MD/AD/PD)
      2. Each lord's transit position and BAV strength
      3. Double transit activation on houses they own
      4. MD-AD inter-relationship
      5. Composite favorability and event domain mapping

    Source: BPHS Ch.25 — dasha lords deliver results based on natal
    promise + transit delivery. Phaladeepika Ch.26 — transit modulation.

    Args:
        chart: Natal birth chart.
        target_date: Date for transit computation. Defaults to current IST.

    Returns:
        DashaTransitAnalysis with full dasha-transit integration.
    """
    if target_date is None:
        target_date = now_ist()

    # Step 1: Get current dasha lords
    md, ad, pd = find_current_dasha(chart, target_date)

    # Step 2: Compute transit JD
    jd = to_jd(target_date)
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Step 3: Get BAV data
    ak_result = compute_ashtakavarga(chart)

    # Step 4: Build DashaLordTransit for MD, AD, PD
    md_transit = _build_lord_transit(chart, md.lord, "MD", jd, ak_result.bhinna)
    ad_transit = _build_lord_transit(chart, ad.lord, "AD", jd, ak_result.bhinna)
    pd_transit = _build_lord_transit(chart, pd.lord, "PD", jd, ak_result.bhinna)

    # Step 5: Collect all houses owned by MD and AD lords
    dasha_houses = set(md_transit.houses_owned + ad_transit.houses_owned)

    # Step 6: Check double transit on dasha houses
    dt_activation = _check_double_transit_on_houses(
        chart,
        dasha_houses,
        jd,
    )

    # Step 7: MD-AD relationship
    relationship = _get_relationship(md.lord, ad.lord)

    # Step 8: MD-AD mutual aspect in transit
    mutual_aspect = _check_mutual_aspect(
        md_transit.transit_sign_index,
        ad_transit.transit_sign_index,
        md.lord,
        ad.lord,
    )

    # Step 9: Active houses = owned by dasha lords AND activated by double transit
    activated_dt_houses = {dt.house for dt in dt_activation if dt.both_activate}
    active_houses = sorted(dasha_houses & activated_dt_houses)

    # Step 10: Map active houses to event domains
    event_domains = [_HOUSE_DOMAINS[h] for h in active_houses if h in _HOUSE_DOMAINS]

    # Step 11: Overall favorability
    overall = compute_overall_favorability(
        md_transit,
        ad_transit,
        relationship,
        len(active_houses),
    )

    # Step 12: Summary
    summary = build_summary(
        md_transit,
        ad_transit,
        relationship,
        active_houses,
        event_domains,
        overall,
    )

    return DashaTransitAnalysis(
        analysis_date=target_date.strftime("%d/%m/%Y"),
        md_lord=md_transit,
        ad_lord=ad_transit,
        pd_lord=pd_transit,
        double_transit_activation=dt_activation,
        md_ad_relationship=relationship,
        md_ad_mutual_aspect=mutual_aspect,
        overall_favorability=overall,
        active_houses=active_houses,
        event_domains=event_domains,
        summary=summary,
    )


def _build_lord_transit(
    chart: ChartData,
    lord: str,
    level: str,
    jd: float,
    bhinna: dict[str, list[int]],
) -> DashaLordTransit:
    """Build transit analysis for a single dasha lord.

    Args:
        chart: Natal chart.
        lord: Planet name (e.g. "Jupiter").
        level: Dasha level ("MD" / "AD" / "PD").
        jd: Julian day for transit.
        bhinna: Bhinnashtakavarga tables from compute_ashtakavarga.

    Returns:
        DashaLordTransit with natal + transit data.
    """
    natal = chart.planets[lord]

    # Transit position
    transit_lon, is_retro = _get_transit_position(lord, jd)
    transit_sign = int(transit_lon / DEGREES_PER_SIGN) % 12

    # Transit houses
    transit_house_lagna = ((transit_sign - chart.lagna_sign_index) % 12) + 1
    moon_sign = chart.planets["Moon"].sign_index
    transit_house_moon = ((transit_sign - moon_sign) % 12) + 1
    transit_house_natal = ((transit_sign - natal.sign_index) % 12) + 1

    # Transit dignity
    transit_dignity = _get_dignity(lord, transit_sign)

    # BAV bindus (Rahu/Ketu not in standard BAV — use neutral 4)
    bav_bindus = bhinna.get(lord, [4] * 12)[transit_sign]
    bav_strength = _classify_bav(bav_bindus)

    # Houses owned
    houses_owned = _get_houses_owned(chart, lord)

    # Scoring
    score = compute_score(bav_bindus, transit_dignity, transit_house_lagna)
    favorability = score_to_favorability(score)

    return DashaLordTransit(
        lord=lord,
        dasha_level=level,
        natal_house=natal.house,
        natal_sign_index=natal.sign_index,
        natal_dignity=natal.dignity,
        transit_sign_index=transit_sign,
        transit_house_from_lagna=transit_house_lagna,
        transit_house_from_moon=transit_house_moon,
        transit_house_from_natal=transit_house_natal,
        transit_dignity=transit_dignity,
        is_retrograde_transit=is_retro,
        bav_bindus=bav_bindus,
        bav_strength=bav_strength,
        houses_owned=houses_owned,
        favorability=favorability,
        score=score,
    )
