"""Internal helpers for conditional dasha computation — period building."""

from __future__ import annotations

from datetime import timedelta

from daivai_engine.compute.datetime_utils import parse_birth_datetime
from daivai_engine.constants import NAKSHATRA_SPAN_DEG
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_conditional import (
    ConditionalAntardasha,
    ConditionalDashaPeriod,
)


def _start_index(nakshatra_index: int, num_planets: int) -> int:
    """Map Moon's nakshatra index to a starting planet in the sequence.

    Uses simple modulo mapping: nakshatra_index % num_planets gives the
    index into the sequence. This follows the same principle as Vimshottari
    but adapted for shorter sequences.

    Args:
        nakshatra_index: Moon's nakshatra (0=Ashwini … 26=Revati).
        num_planets: Number of planets in the dasha sequence.

    Returns:
        Starting index (0-based) into the planet sequence.
    """
    return nakshatra_index % num_planets


def _compute_antardasha(
    md: ConditionalDashaPeriod,
    sequence: list[tuple[str, int]],
    total_years: int,
    start_idx: int,
) -> list[ConditionalAntardasha]:
    """Compute sub-periods (Antardashas) within a Mahadasha.

    Each AD duration = MD_days x (ad_planet_years / total_years).
    Order starts from the same planet as the MD, then cycles forward.

    Args:
        md: Parent Mahadasha period.
        sequence: Full planet sequence with years.
        total_years: Total cycle length of the system.
        start_idx: Index of md's planet in the sequence.

    Returns:
        List of ConditionalAntardasha objects.
    """
    n = len(sequence)
    md_days = (md.end - md.start).total_seconds() / 86400.0
    ads: list[ConditionalAntardasha] = []
    current = md.start

    for i in range(n):
        idx = (start_idx + i) % n
        planet, years = sequence[idx]
        ad_days = md_days * (years / total_years)
        ad_end = current + timedelta(days=ad_days)
        ads.append(
            ConditionalAntardasha(
                planet=planet,
                start=current,
                end=ad_end,
            )
        )
        current = ad_end

    return ads


def compute_periods(
    chart: ChartData,
    sequence: list[tuple[str, int]],
    total_years: int,
) -> list[ConditionalDashaPeriod]:
    """Build Mahadasha list for any conditional nakshatra-based system.

    The first period is prorated by the fraction of the Moon's nakshatra
    remaining at birth (same balance formula as Vimshottari).

    Args:
        chart: Computed birth chart.
        sequence: Planet sequence with canonical year durations.
        total_years: Total cycle length.

    Returns:
        List of ConditionalDashaPeriod objects (one full cycle).
    """
    moon = chart.planets["Moon"]
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)

    n = len(sequence)
    start_idx = _start_index(moon.nakshatra_index, n)

    degree_in_nak = moon.longitude - moon.nakshatra_index * NAKSHATRA_SPAN_DEG
    balance = 1.0 - (degree_in_nak / NAKSHATRA_SPAN_DEG)

    periods: list[ConditionalDashaPeriod] = []
    current_start = birth_dt

    for i in range(n):
        idx = (start_idx + i) % n
        planet, years = sequence[idx]

        effective_years = years * balance if i == 0 else float(years)
        days = effective_years * 365.25
        end = current_start + timedelta(days=days)

        md = ConditionalDashaPeriod(
            planet=planet,
            years=years,
            start=current_start,
            end=end,
        )
        ads = _compute_antardasha(md, sequence, total_years, idx)
        md = md.model_copy(update={"antardasha": ads})
        periods.append(md)
        current_start = end

    return periods
