"""Conditional nakshatra-based Dasha systems.

Each system applies only when a specific chart condition is met. When the
condition is not met, Vimshottari (120-year cycle) remains the default.

Systems implemented (with total years and applicability per BPHS):
    Ashtottari       (108 yr) — Rahu in kendra/trikona from Lagna lord [BPHS Ch.49]
    Shodashottari    (116 yr) — Krishna Paksha birth, Moon on Poorna Tithi [BPHS Ch.49]
    Dwisaptati Sama  (72 yr)  — Lagna lord in 7th OR 7th lord in Lagna [BPHS Ch.50]
    Shatabdika       (100 yr) — Born in Vargottama Lagna [BPHS Ch.51]
    Chaturaseeti Sama(84 yr)  — Lagna lord in 10th house [BPHS Ch.52]
    Dwadashottari    (112 yr) — Venus in lagna [BPHS Ch.53]
    Panchottari      (105 yr) — Moon in Dhanishtha nakshatra [BPHS Ch.54]
    Shashtihayani    (60 yr)  — Sun in lagna [BPHS Ch.55]
    Shatrimsha Sama  (36 yr)  — Mars in lagna [BPHS Ch.56]

Sources: BPHS Ch.49-56.
"""

from __future__ import annotations

from daivai_engine.compute.dasha_conditional_checks import (
    is_ashtottari_applicable,
    is_chaturaseeti_applicable,
    is_dwadashottari_applicable,
    is_dwisaptati_applicable,
    is_panchottari_applicable,
    is_shashtihayani_applicable,
    is_shatabdika_applicable,
    is_shatrimsha_applicable,
    is_shodashottari_applicable,
)
from daivai_engine.compute.dasha_conditional_helpers import compute_periods
from daivai_engine.constants import (
    CHATURASEETI_SEQUENCE,
    CHATURASEETI_TOTAL_YEARS,
    DWADASHOTTARI_SEQUENCE,
    DWADASHOTTARI_TOTAL_YEARS,
    DWISAPTATI_SEQUENCE,
    DWISAPTATI_TOTAL_YEARS,
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
from daivai_engine.models.dasha_conditional import ConditionalDashaPeriod


__all__ = [
    "compute_chaturaseeti_dasha",
    "compute_dwadashottari_dasha",
    "compute_dwisaptati_dasha",
    "compute_panchottari_dasha",
    "compute_shashtihayani_dasha",
    "compute_shatabdika_dasha",
    "compute_shatrimsha_dasha",
    "is_ashtottari_applicable",
    "is_chaturaseeti_applicable",
    "is_dwadashottari_applicable",
    "is_dwisaptati_applicable",
    "is_panchottari_applicable",
    "is_shashtihayani_applicable",
    "is_shatabdika_applicable",
    "is_shatrimsha_applicable",
    "is_shodashottari_applicable",
]


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
    return compute_periods(chart, DWISAPTATI_SEQUENCE, DWISAPTATI_TOTAL_YEARS)


def compute_shatabdika_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Shatabdika Dasha periods (100-year cycle).

    5 planets x 20 years each. Applicable when lagna lord is in lagna.
    Use is_shatabdika_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 5 ConditionalDashaPeriod objects.
    """
    return compute_periods(chart, SHATABDIKA_SEQUENCE, SHATABDIKA_TOTAL_YEARS)


def compute_chaturaseeti_dasha(chart: ChartData) -> list[ConditionalDashaPeriod]:
    """Compute Chaturaseeti Sama Dasha periods (84-year cycle).

    7 planets x 12 years each. Applicable when lagna lord is in 10th house.
    Use is_chaturaseeti_applicable(chart) to verify before relying on results.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 7 ConditionalDashaPeriod objects.
    """
    return compute_periods(chart, CHATURASEETI_SEQUENCE, CHATURASEETI_TOTAL_YEARS)


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
    return compute_periods(chart, DWADASHOTTARI_SEQUENCE, DWADASHOTTARI_TOTAL_YEARS)


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
    return compute_periods(chart, PANCHOTTARI_SEQUENCE, PANCHOTTARI_TOTAL_YEARS)


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
    return compute_periods(chart, SHASHTIHAYANI_SEQUENCE, SHASHTIHAYANI_TOTAL_YEARS)


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
    return compute_periods(chart, SHATRIMSHA_SEQUENCE, SHATRIMSHA_TOTAL_YEARS)
