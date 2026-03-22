"""Conditional nakshatra-based Dasha systems.

Each system applies only when a specific chart condition is met. When the
condition is not met, Vimshottari (120-year cycle) remains the default.

Systems implemented (with total years and applicability):
    Dwisaptati Sama  (72 yr) — Lagna lord in 7th house
    Shatabdika       (100 yr) — Lagna lord in lagna
    Chaturaseeti Sama(84 yr) — Lagna lord in 10th house
    Dwadashottari    (112 yr) — Venus in lagna
    Panchottari      (105 yr) — Cancer lagna AND Moon in lagna
    Shashtihayani    (60 yr)  — Sun in lagna
    Shatrimsha Sama  (36 yr)  — Mars in lagna

Sources: BPHS Ch.50-56.
"""

from __future__ import annotations

from datetime import timedelta

from daivai_engine.compute.dasha_conditional_checks import (
    is_chaturaseeti_applicable,
    is_dwadashottari_applicable,
    is_dwisaptati_applicable,
    is_panchottari_applicable,
    is_shashtihayani_applicable,
    is_shatabdika_applicable,
    is_shatrimsha_applicable,
)
from daivai_engine.compute.datetime_utils import parse_birth_datetime
from daivai_engine.constants import (
    CHATURASEETI_SEQUENCE,
    CHATURASEETI_TOTAL_YEARS,
    DWADASHOTTARI_SEQUENCE,
    DWADASHOTTARI_TOTAL_YEARS,
    DWISAPTATI_SEQUENCE,
    DWISAPTATI_TOTAL_YEARS,
    NAKSHATRA_SPAN_DEG,
    PANCHOTTARI_SEQUENCE,
    PANCHOTTARI_TOTAL_YEARS,
    SHASHTIHAYANI_SEQUENCE,
    SHASHTIHAYANI_TOTAL_YEARS,
    SHATABDIKA_SEQUENCE,
    SHATABDIKA_TOTAL_YEARS,
    SHATRIMSHA_SEQUENCE,
    SHATRIMSHA_TOTAL_YEARS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_conditional import (
    ConditionalAntardasha,
    ConditionalDashaPeriod,
)


__all__ = [
    "compute_chaturaseeti_dasha",
    "compute_dwadashottari_dasha",
    "compute_dwisaptati_dasha",
    "compute_panchottari_dasha",
    "compute_shashtihayani_dasha",
    "compute_shatabdika_dasha",
    "compute_shatrimsha_dasha",
    "is_chaturaseeti_applicable",
    "is_dwadashottari_applicable",
    "is_dwisaptati_applicable",
    "is_panchottari_applicable",
    "is_shashtihayani_applicable",
    "is_shatabdika_applicable",
    "is_shatrimsha_applicable",
]


# ── Internal helpers ─────────────────────────────────────────────────────────


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


def _compute_periods(
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


# ── Computation functions ────────────────────────────────────────────────────


def compute_dwisaptati_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Dwisaptati Sama Dasha periods (72-year cycle).

    8 planets x 9 years each. Applicable when lagna lord is in 7th house.
    Use is_dwisaptati_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 8 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, DWISAPTATI_SEQUENCE, DWISAPTATI_TOTAL_YEARS)


def compute_shatabdika_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Shatabdika Dasha periods (100-year cycle).

    5 planets x 20 years each. Applicable when lagna lord is in lagna.
    Use is_shatabdika_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 5 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, SHATABDIKA_SEQUENCE, SHATABDIKA_TOTAL_YEARS)


def compute_chaturaseeti_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Chaturaseeti Sama Dasha periods (84-year cycle).

    7 planets x 12 years each. Applicable when lagna lord is in 10th house.
    Use is_chaturaseeti_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 7 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, CHATURASEETI_SEQUENCE, CHATURASEETI_TOTAL_YEARS)


def compute_dwadashottari_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Dwadashottari Dasha periods (112-year cycle).

    8 planets: Sun(7)+Moon(14)+Mars(8)+Mercury(17)+Jupiter(10)+Venus(25)+
    Saturn(10)+Rahu(21) = 112 years.
    Applicable when Venus is in lagna.
    Use is_dwadashottari_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 8 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, DWADASHOTTARI_SEQUENCE, DWADASHOTTARI_TOTAL_YEARS)


def compute_panchottari_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Panchottari Dasha periods (105-year cycle).

    5 planets: Sun(12)+Moon(21)+Mars(16)+Mercury(42)+Saturn(14) = 105 years.
    Applicable only when Cancer lagna AND Moon is in lagna.
    Use is_panchottari_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 5 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, PANCHOTTARI_SEQUENCE, PANCHOTTARI_TOTAL_YEARS)


def compute_shashtihayani_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Shashtihayani Dasha periods (60-year cycle).

    2 planets: Sun(30) + Moon(30) = 60 years.
    Applicable when Sun is in lagna.
    Use is_shashtihayani_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 2 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, SHASHTIHAYANI_SEQUENCE, SHASHTIHAYANI_TOTAL_YEARS)


def compute_shatrimsha_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Shatrimsha Sama Dasha periods (36-year cycle).

    6 planets x 6 years each = 36 years.
    Applicable when Mars is in lagna.
    Use is_shatrimsha_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 6 ConditionalDashaPeriod objects.
    """
    return _compute_periods(chart, SHATRIMSHA_SEQUENCE, SHATRIMSHA_TOTAL_YEARS)
