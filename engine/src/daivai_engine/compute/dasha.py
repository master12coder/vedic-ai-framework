"""Vimshottari Dasha calculator — MD/AD/PD with date ranges."""

from __future__ import annotations

from datetime import datetime, timedelta

from daivai_engine.constants import (
    DASHA_SEQUENCE,
    DASHA_TOTAL_YEARS,
    DASHA_YEARS,
    NAKSHATRA_SPAN_DEG,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod


def _dasha_start_index(nakshatra_lord: str) -> int:
    """Get the index in DASHA_SEQUENCE for a given nakshatra lord."""
    return DASHA_SEQUENCE.index(nakshatra_lord)


def _balance_of_dasha(moon_longitude: float) -> float:
    """Calculate the fraction of first dasha remaining based on Moon's position in nakshatra."""
    nak_index = int(moon_longitude / NAKSHATRA_SPAN_DEG)
    degree_in_nak = moon_longitude - nak_index * NAKSHATRA_SPAN_DEG
    fraction_elapsed = degree_in_nak / NAKSHATRA_SPAN_DEG
    return 1.0 - fraction_elapsed


def compute_mahadashas(chart: ChartData) -> list[DashaPeriod]:
    """Compute all 9 Mahadasha periods from birth."""
    moon = chart.planets["Moon"]
    nak_lord = moon.nakshatra_lord
    start_index = _dasha_start_index(nak_lord)
    balance = _balance_of_dasha(moon.longitude)

    from daivai_engine.compute.datetime_utils import parse_birth_datetime

    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)

    periods: list[DashaPeriod] = []
    current_start = birth_dt

    for i in range(9):
        lord_index = (start_index + i) % 9
        lord = DASHA_SEQUENCE[lord_index]
        total_years = DASHA_YEARS[lord]

        if i == 0:
            # First dasha: only the remaining balance
            years = total_years * balance
        else:
            years = float(total_years)

        days = years * 365.25
        end = current_start + timedelta(days=days)

        periods.append(
            DashaPeriod(
                level="MD",
                lord=lord,
                start=current_start,
                end=end,
            )
        )

        current_start = end

    return periods


def compute_antardashas(md: DashaPeriod) -> list[DashaPeriod]:
    """Compute Antardasha periods within a Mahadasha."""
    md_lord = md.lord
    md_duration_days = (md.end - md.start).total_seconds() / 86400.0
    start_index = DASHA_SEQUENCE.index(md_lord)

    periods: list[DashaPeriod] = []
    current_start = md.start

    for i in range(9):
        ad_lord_index = (start_index + i) % 9
        ad_lord = DASHA_SEQUENCE[ad_lord_index]
        ad_years = DASHA_YEARS[ad_lord]

        # AD duration = (AD_years / 120) * MD duration
        ad_days = md_duration_days * (ad_years / DASHA_TOTAL_YEARS)

        end = current_start + timedelta(days=ad_days)
        if end > md.end:
            end = md.end

        periods.append(
            DashaPeriod(
                level="AD",
                lord=ad_lord,
                start=current_start,
                end=end,
                parent_lord=md_lord,
            )
        )

        current_start = end

    return periods


def compute_pratyantardashas(ad: DashaPeriod) -> list[DashaPeriod]:
    """Compute Pratyantardasha periods within an Antardasha."""
    ad_lord = ad.lord
    ad_duration_days = (ad.end - ad.start).total_seconds() / 86400.0
    start_index = DASHA_SEQUENCE.index(ad_lord)

    periods: list[DashaPeriod] = []
    current_start = ad.start

    for i in range(9):
        pd_lord_index = (start_index + i) % 9
        pd_lord = DASHA_SEQUENCE[pd_lord_index]
        pd_years = DASHA_YEARS[pd_lord]

        pd_days = ad_duration_days * (pd_years / DASHA_TOTAL_YEARS)
        end = current_start + timedelta(days=pd_days)
        if end > ad.end:
            end = ad.end

        periods.append(
            DashaPeriod(
                level="PD",
                lord=pd_lord,
                start=current_start,
                end=end,
                parent_lord=ad.lord,
            )
        )

        current_start = end

    return periods


def find_current_dasha(
    chart: ChartData,
    target_date: datetime | None = None,
) -> tuple[DashaPeriod, DashaPeriod, DashaPeriod]:
    """Find the MD/AD/PD running at a given date.

    Returns: (mahadasha, antardasha, pratyantardasha)
    """
    if target_date is None:
        from daivai_engine.compute.datetime_utils import now_ist

        target_date = now_ist()

    mahadashas = compute_mahadashas(chart)

    current_md: DashaPeriod | None = None
    for md in mahadashas:
        if md.start <= target_date <= md.end:
            current_md = md
            break

    if current_md is None:
        # Target date is outside the 120-year range; use last MD
        current_md = mahadashas[-1]

    antardashas = compute_antardashas(current_md)
    current_ad: DashaPeriod | None = None
    for ad in antardashas:
        if ad.start <= target_date <= ad.end:
            current_ad = ad
            break
    if current_ad is None:
        current_ad = antardashas[-1]

    pratyantardashas = compute_pratyantardashas(current_ad)
    current_pd: DashaPeriod | None = None
    for pd in pratyantardashas:
        if pd.start <= target_date <= pd.end:
            current_pd = pd
            break
    if current_pd is None:
        current_pd = pratyantardashas[-1]

    return current_md, current_ad, current_pd


def get_dasha_timeline(chart: ChartData) -> list[dict]:
    """Get a simplified dasha timeline for display."""
    mahadashas = compute_mahadashas(chart)
    timeline = []
    for md in mahadashas:
        antardashas = compute_antardashas(md)
        ad_list = [
            {
                "lord": ad.lord,
                "start": ad.start.strftime("%d/%m/%Y"),
                "end": ad.end.strftime("%d/%m/%Y"),
            }
            for ad in antardashas
        ]
        timeline.append(
            {
                "level": "MD",
                "lord": md.lord,
                "start": md.start.strftime("%d/%m/%Y"),
                "end": md.end.strftime("%d/%m/%Y"),
                "antardashas": ad_list,
            }
        )
    return timeline
