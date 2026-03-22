"""Mudda Dasha — compressed Vimshottari Dasha for one solar year.

In Varshphal (annual chart) analysis the Vimshottari sequence is
compressed so that 120 years maps onto 365.25 days (one tropical year).
The Moon's nakshatra in the *annual chart* determines the first ruling
period, exactly as in natal Vimshottari.

Formula:
    mudda_period_days(planet) = (planet_dasha_years / 120) * 365.25

Balance of first period:
    balance_days = nakshatra_balance_fraction * period_days_of_first_lord

Sources: Tajaka Neelakanthi Ch.12, B.V. Raman's "Varshphal" Ch.7,
         Komilla Sutton "The Essentials of Vedic Astrology".
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.constants import (
    DASHA_SEQUENCE,
    DASHA_TOTAL_YEARS,
    DASHA_YEARS,
    NAKSHATRA_SPAN_DEG,
)
from daivai_engine.models.chart import ChartData


# One solar year in days (tropical)
_SOLAR_YEAR_DAYS: float = 365.25


class MuddaDashaPeriod(BaseModel):
    """A single period in the Mudda (annual compressed) Dasha system.

    Each period spans a fraction of the 365-day year proportional to
    the planet's full Vimshottari years out of 120.
    """

    model_config = ConfigDict(frozen=True)

    level: str  # "MD" (Mudda Dasha) or "AD" (Mudda Antardasha)
    lord: str  # Ruling planet
    start: datetime
    end: datetime
    duration_days: float  # Actual length in days (rounded to 2 d.p.)
    parent_lord: str | None = None  # For Antardasha level


class MuddaDashaResult(BaseModel):
    """Complete Mudda Dasha calculation for one solar year.

    Contains all 9 main periods (MD) covering the full year, optionally
    with sub-periods (AD) for each MD.
    """

    model_config = ConfigDict(frozen=True)

    year: int
    start_date: datetime  # Varsha Pravesh / annual start
    end_date: datetime  # start_date + 365.25 days
    moon_nakshatra: str  # Moon's nakshatra in annual chart
    first_lord: str  # First ruling planet (from nakshatra lord)
    periods: list[MuddaDashaPeriod]  # 9 main Mudda Dasha periods
    total_days: float = Field(ge=364, le=367)


def compute_mudda_dasha(
    annual_chart: ChartData,
    varsha_pravesh_date: datetime,
    year: int,
    include_antardashas: bool = False,
) -> MuddaDashaResult:
    """Compute the Mudda Dasha for a complete solar year.

    Uses the annual chart's Moon nakshatra to determine the starting lord,
    then proportionally distributes 365.25 days across all 9 planets in
    the Vimshottari sequence.

    Args:
        annual_chart: The Varsha Pravesh (annual) chart.
        varsha_pravesh_date: Exact datetime of the solar return.
        year: The year being computed (for labelling).
        include_antardashas: If True, compute sub-periods for each MD.

    Returns:
        MuddaDashaResult with full period breakdown.
    """
    moon = annual_chart.planets["Moon"]
    moon_lon = moon.longitude
    nak_lord = moon.nakshatra_lord

    start_index = DASHA_SEQUENCE.index(nak_lord)
    balance = _nakshatra_balance(moon_lon)

    start_date = varsha_pravesh_date
    end_date = start_date + timedelta(days=_SOLAR_YEAR_DAYS)

    periods: list[MuddaDashaPeriod] = []
    current_start = start_date

    for i in range(9):
        lord_index = (start_index + i) % 9
        lord = DASHA_SEQUENCE[lord_index]
        full_days = _mudda_days(lord)

        if i == 0:
            period_days = balance * full_days
        else:
            period_days = full_days

        period_end = current_start + timedelta(days=period_days)
        if period_end > end_date:
            period_end = end_date

        md = MuddaDashaPeriod(
            level="MD",
            lord=lord,
            start=current_start,
            end=period_end,
            duration_days=round(period_days, 2),
        )
        periods.append(md)
        current_start = period_end

        if current_start >= end_date:
            break

    # Optionally compute Antardasha sub-periods
    if include_antardashas:
        expanded: list[MuddaDashaPeriod] = []
        for md in periods:
            expanded.append(md)
            expanded.extend(_compute_antardashas(md))
        periods = expanded

    return MuddaDashaResult(
        year=year,
        start_date=start_date,
        end_date=end_date,
        moon_nakshatra=moon.nakshatra,
        first_lord=nak_lord,
        periods=periods,
        total_days=round(_SOLAR_YEAR_DAYS, 2),
    )


def compute_mudda_antardashas(md: MuddaDashaPeriod) -> list[MuddaDashaPeriod]:
    """Compute Mudda Antardasha sub-periods within a single Mudda Dasha.

    The sub-period duration of planet B within planet A's main period is:
        duration = (md_duration_days * B_years) / 120

    Args:
        md: A main Mudda Dasha period.

    Returns:
        List of 9 MuddaDashaPeriod at level "AD".
    """
    return _compute_antardashas(md)


def get_active_mudda_dasha(
    result: MuddaDashaResult,
    query_date: datetime,
) -> MuddaDashaPeriod | None:
    """Return the Mudda Dasha period active on a given date.

    Only searches main (MD-level) periods.

    Args:
        result: Computed MuddaDashaResult.
        query_date: Date to check.

    Returns:
        Active MuddaDashaPeriod or None if outside the year.
    """
    for period in result.periods:
        if period.level == "MD" and period.start <= query_date < period.end:
            return period
    return None


# ── Private helpers ────────────────────────────────────────────────────────────


def _mudda_days(planet: str) -> float:
    """Return Mudda Dasha duration in days for a planet.

    Proportion = (planet_years / 120) * 365.25
    """
    return (DASHA_YEARS[planet] / DASHA_TOTAL_YEARS) * _SOLAR_YEAR_DAYS


def _nakshatra_balance(moon_longitude: float) -> float:
    """Fraction of the current nakshatra remaining (0..1).

    Args:
        moon_longitude: Sidereal Moon longitude (0-360).

    Returns:
        Float 0..1 — proportion of nakshatra period still to run.
    """
    nak_idx = int(moon_longitude / NAKSHATRA_SPAN_DEG)
    elapsed = moon_longitude - nak_idx * NAKSHATRA_SPAN_DEG
    return 1.0 - (elapsed / NAKSHATRA_SPAN_DEG)


def _compute_antardashas(md: MuddaDashaPeriod) -> list[MuddaDashaPeriod]:
    """Compute 9 Antardasha sub-periods within the given Mudda Dasha."""
    md_lord = md.lord
    md_duration_days = (md.end - md.start).total_seconds() / 86400.0
    start_index = DASHA_SEQUENCE.index(md_lord)

    sub_periods: list[MuddaDashaPeriod] = []
    current_start = md.start

    for i in range(9):
        ad_lord = DASHA_SEQUENCE[(start_index + i) % 9]
        ad_days = md_duration_days * (DASHA_YEARS[ad_lord] / DASHA_TOTAL_YEARS)
        ad_end = current_start + timedelta(days=ad_days)
        if ad_end > md.end:
            ad_end = md.end

        sub_periods.append(
            MuddaDashaPeriod(
                level="AD",
                lord=ad_lord,
                start=current_start,
                end=ad_end,
                duration_days=round(ad_days, 2),
                parent_lord=md_lord,
            )
        )
        current_start = ad_end

    return sub_periods
