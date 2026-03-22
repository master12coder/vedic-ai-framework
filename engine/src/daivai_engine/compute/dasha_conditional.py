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

from datetime import timedelta

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
    SIGN_LORDS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_conditional import (
    ConditionalAntardasha,
    ConditionalDashaPeriod,
)


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


# ── Applicability checks ─────────────────────────────────────────────────────


def _lagna_navamsha_sign(chart: ChartData) -> int:
    """Compute the navamsha sign of the Lagna degree.

    Each navamsha spans 3°20' (1/9 of a sign). The navamsha sign is
    used to determine Vargottama Lagna (rashi sign == navamsha sign).

    Returns:
        Navamsha sign index (0-11).
    """
    lagna_deg = chart.lagna_sign_index * 30.0 + (chart.lagna_longitude % 30.0)
    navamsha_unit = 30.0 / 9.0  # 3.3333 degrees
    sign_navamsha_start = chart.lagna_sign_index * 9
    degree_in_sign = chart.lagna_longitude % 30.0
    navamsha_idx_in_sign = int(degree_in_sign / navamsha_unit)
    _ = lagna_deg  # used in docstring context
    return (sign_navamsha_start + navamsha_idx_in_sign) % 12


def is_ashtottari_applicable(chart: ChartData) -> bool:
    """Check if Ashtottari Dasha applies (Rahu in kendra/trikona from Lagna lord).

    Kendra = houses 1, 4, 7, 10. Trikona = houses 1, 5, 9.
    Combined set = {1, 4, 5, 7, 9, 10}.

    Source: BPHS Ch.49.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)
    rahu = chart.planets.get("Rahu")
    if lord is None or rahu is None:
        return False
    # House of Rahu counted from the lagna lord's position
    rahu_from_lord = (rahu.sign_index - lord.sign_index) % 12 + 1
    kendra_trikona = {1, 4, 5, 7, 9, 10}
    return rahu_from_lord in kendra_trikona


def is_shodashottari_applicable(chart: ChartData) -> bool:
    """Check if Shodashottari Dasha applies (Krishna Paksha birth, Moon on Poorna Tithi).

    Krishna Paksha = waning moon (Sun-Moon longitude diff > 180°).
    Poorna Tithi = tithis 5, 10, 15, 20, 25, 30 (every fifth tithi).

    Source: BPHS Ch.49.
    """
    sun = chart.planets.get("Sun")
    moon = chart.planets.get("Moon")
    if sun is None or moon is None:
        return False

    # Tithi from elongation: Moon ahead of Sun by (tithi-1)*12 degrees
    elongation = (moon.longitude - sun.longitude) % 360.0
    tithi = int(elongation / 12.0) + 1  # 1-30

    # Krishna Paksha: tithis 16-30 (after full moon)
    krishna_paksha = tithi > 15

    # Poorna (complete) Tithi: divisible by 5
    poorna_tithi = tithi % 5 == 0

    return krishna_paksha and poorna_tithi


def is_dwisaptati_applicable(chart: ChartData) -> bool:
    """Check if Dwisaptati Sama Dasha applies.

    Condition: Lagna lord in 7th house OR 7th lord in Lagna (1st house).

    Source: BPHS Ch.50.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)

    # Condition 1: Lagna lord in 7th
    lagna_lord_in_7th = lord is not None and lord.house == 7

    # Condition 2: 7th lord in Lagna
    seventh_lord_name = SIGN_LORDS[(chart.lagna_sign_index + 6) % 12]
    seventh_lord = chart.planets.get(seventh_lord_name)
    seventh_lord_in_1st = seventh_lord is not None and seventh_lord.house == 1

    return lagna_lord_in_7th or seventh_lord_in_1st


def is_shatabdika_applicable(chart: ChartData) -> bool:
    """Check if Shatabdika Dasha applies (Lagna is in Vargottama — same sign in D1 and D9).

    A Vargottama Lagna means the Ascendant falls in the same sign in both
    the Rashi (D1) and Navamsha (D9) charts.

    Source: BPHS Ch.51.
    """
    navamsha_sign = _lagna_navamsha_sign(chart)
    return navamsha_sign == chart.lagna_sign_index


def is_chaturaseeti_applicable(chart: ChartData) -> bool:
    """Check if Chaturaseeti Sama Dasha applies (lagna lord in 10th house).

    Source: BPHS Ch.52.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)
    if lord is None:
        return False
    return lord.house == 10


def is_dwadashottari_applicable(chart: ChartData) -> bool:
    """Check if Dwadashottari Dasha applies (Venus in lagna / 1st house).

    Source: BPHS Ch.53.
    """
    venus = chart.planets.get("Venus")
    if venus is None:
        return False
    return venus.house == 1


def is_panchottari_applicable(chart: ChartData) -> bool:
    """Check if Panchottari Dasha applies (Moon in Dhanishtha nakshatra).

    Source: BPHS Ch.54. Dhanishtha = nakshatra index 23 (0-based).
    """
    moon = chart.planets.get("Moon")
    if moon is None:
        return False
    return moon.nakshatra_index == 23  # Dhanishtha


def is_shashtihayani_applicable(chart: ChartData) -> bool:
    """Check if Shashtihayani Dasha applies (Sun in lagna / 1st house).

    Source: BPHS Ch.55.
    """
    sun = chart.planets.get("Sun")
    if sun is None:
        return False
    return sun.house == 1


def is_shatrimsha_applicable(chart: ChartData) -> bool:
    """Check if Shatrimsha Sama Dasha applies (Mars in lagna / 1st house).

    Source: BPHS Ch.56.
    """
    mars = chart.planets.get("Mars")
    if mars is None:
        return False
    return mars.house == 1


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
