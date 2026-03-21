"""Sudarshan Chakra Dasha — triple-cycle annual dasha system.

Each of the three reference points (Lagna, Moon, Sun) runs its own 12-year
cycle, with each sign receiving 1 year. All three cycles run simultaneously
from birth, giving a triple overlay for annual event timing.

Usage:
  - Find which sign is active in each cycle for a given age
  - Overlay all three to identify years where multiple cycles coincide
  - Years where all three cycles are in the same sign = peak significance

Source: Sudarshan Chakra chapter in traditional jyotish texts;
        Dr. B.V. Raman, "A Manual of Hindu Astrology" (Sudarshan Chakra).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.constants import SIGN_LORDS, SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData


class SudarshanDashaPeriod(BaseModel):
    """One year period in the Sudarshan Chakra Dasha.

    Represents a single year's active sign and its lord for one of the
    three reference cycles (Lagna, Moon, or Sun).
    """

    model_config = ConfigDict(frozen=True)

    reference: str  # "Lagna", "Moon", or "Sun"
    year_number: int  # Year from birth (1, 2, 3 …)
    cycle_number: int  # Which 12-year cycle (1 = first, 2 = second …)
    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    sign_lord: str


class SudarshanYear(BaseModel):
    """Triple-overlay analysis for a single calendar year.

    Combines Lagna, Moon, and Sun cycle active signs to assess the
    year's overall significance and quality.
    """

    model_config = ConfigDict(frozen=True)

    age: int  # Age at the start of that year
    calendar_year: int  # Approximate calendar year
    lagna_period: SudarshanDashaPeriod
    moon_period: SudarshanDashaPeriod
    sun_period: SudarshanDashaPeriod
    overlap_count: int  # How many cycles share the SAME sign (0-3)
    is_peak: bool  # True if all 3 cycles in same sign
    summary: str  # Human-readable interpretation


class SudarshanDashaResult(BaseModel):
    """Full Sudarshan Chakra Dasha for a native.

    Contains 12 years (one cycle) or more of the triple-overlay timeline.
    """

    model_config = ConfigDict(frozen=True)

    native_name: str
    birth_year: int
    lagna_sign_index: int
    moon_sign_index: int
    sun_sign_index: int
    years: list[SudarshanYear]


def compute_sudarshan_dasha(
    chart: ChartData,
    num_years: int = 36,
) -> SudarshanDashaResult:
    """Compute Sudarshan Chakra Dasha timeline from birth.

    Calculates the triple-cycle Sudarshan dasha for the native.
    Each of the three reference points cycles through 12 signs at 1 year per sign.

    The Lagna cycle starts from Lagna sign and progresses forward.
    The Moon cycle starts from Moon sign and progresses forward.
    The Sun cycle starts from Sun sign and progresses forward.

    Args:
        chart: Natal birth chart.
        num_years: Number of years to compute (default 36 = 3 full cycles).

    Returns:
        SudarshanDashaResult with year-by-year triple overlay.
    """
    birth_year = int(chart.dob.split("/")[2])
    lagna_start = chart.lagna_sign_index
    moon_start = chart.planets["Moon"].sign_index
    sun_start = chart.planets["Sun"].sign_index

    years: list[SudarshanYear] = []
    for age in range(num_years):
        l_period = _make_period("Lagna", age, lagna_start)
        m_period = _make_period("Moon", age, moon_start)
        s_period = _make_period("Sun", age, sun_start)

        active_signs = [l_period.sign_index, m_period.sign_index, s_period.sign_index]
        overlap = _count_overlaps(active_signs)
        is_peak = overlap == 3

        summary = _build_summary(l_period, m_period, s_period, overlap, is_peak)

        years.append(
            SudarshanYear(
                age=age + 1,
                calendar_year=birth_year + age,
                lagna_period=l_period,
                moon_period=m_period,
                sun_period=s_period,
                overlap_count=overlap,
                is_peak=is_peak,
                summary=summary,
            )
        )

    return SudarshanDashaResult(
        native_name=chart.name,
        birth_year=birth_year,
        lagna_sign_index=lagna_start,
        moon_sign_index=moon_start,
        sun_sign_index=sun_start,
        years=years,
    )


def get_sudarshan_year(
    chart: ChartData,
    target_age: int,
) -> SudarshanYear:
    """Get the Sudarshan Chakra Dasha analysis for a specific age.

    Args:
        chart: Natal birth chart.
        target_age: Age in years (1 = first year of life).

    Returns:
        SudarshanYear with triple-overlay analysis for that age.
    """
    if target_age < 1:
        target_age = 1

    lagna_start = chart.lagna_sign_index
    moon_start = chart.planets["Moon"].sign_index
    sun_start = chart.planets["Sun"].sign_index
    birth_year = int(chart.dob.split("/")[2])

    age = target_age - 1  # 0-indexed for computation
    l_period = _make_period("Lagna", age, lagna_start)
    m_period = _make_period("Moon", age, moon_start)
    s_period = _make_period("Sun", age, sun_start)

    active_signs = [l_period.sign_index, m_period.sign_index, s_period.sign_index]
    overlap = _count_overlaps(active_signs)
    is_peak = overlap == 3
    summary = _build_summary(l_period, m_period, s_period, overlap, is_peak)

    return SudarshanYear(
        age=target_age,
        calendar_year=birth_year + age,
        lagna_period=l_period,
        moon_period=m_period,
        sun_period=s_period,
        overlap_count=overlap,
        is_peak=is_peak,
        summary=summary,
    )


def find_peak_years(
    chart: ChartData,
    num_years: int = 120,
) -> list[SudarshanYear]:
    """Find years where all 3 Sudarshan cycles are in the same sign (peak years).

    These years represent maximum concentration of a single sign's energy
    and are considered especially significant for events related to that sign.

    Args:
        chart: Natal birth chart.
        num_years: Number of years to scan (default 120 = full lifespan).

    Returns:
        List of SudarshanYear where is_peak is True (all 3 cycles align).
    """
    full = compute_sudarshan_dasha(chart, num_years=num_years)
    return [y for y in full.years if y.is_peak]


# ── Private helpers ────────────────────────────────────────────────────────


def _make_period(reference: str, age: int, start_sign: int) -> SudarshanDashaPeriod:
    """Create a SudarshanDashaPeriod for a given age and start sign.

    Each year advances by 1 sign. The cycle repeats every 12 years.
    """
    sign_idx = (start_sign + age) % 12
    cycle_num = (age // 12) + 1
    return SudarshanDashaPeriod(
        reference=reference,
        year_number=age + 1,
        cycle_number=cycle_num,
        sign_index=sign_idx,
        sign=SIGNS[sign_idx],
        sign_en=SIGNS_EN[sign_idx],
        sign_lord=SIGN_LORDS[sign_idx],
    )


def _count_overlaps(signs: list[int]) -> int:
    """Count maximum overlap — how many cycles share the most common sign.

    Returns 3 if all same, 2 if two share a sign, 1 if all different.
    """
    from collections import Counter

    counts = Counter(signs)
    return max(counts.values())


def _build_summary(
    lagna_p: SudarshanDashaPeriod,
    moon_p: SudarshanDashaPeriod,
    sun_p: SudarshanDashaPeriod,
    overlap: int,
    is_peak: bool,
) -> str:
    """Build human-readable summary for a Sudarshan year."""
    if is_peak:
        return (
            f"PEAK: All 3 cycles in {lagna_p.sign_en} ({lagna_p.sign}). "
            f"Lord {lagna_p.sign_lord} dominates this year -- concentrated {lagna_p.sign_en} energy."
        )
    if overlap == 2:
        # Find which sign has the overlap
        from collections import Counter

        signs = [lagna_p.sign_index, moon_p.sign_index, sun_p.sign_index]
        refs = ["Lagna", "Moon", "Sun"]
        cnt = Counter(signs)
        shared_sign = cnt.most_common(1)[0][0]
        shared_refs = [refs[i] for i, s_i in enumerate(signs) if s_i == shared_sign]
        return (
            f"{' & '.join(shared_refs)} cycles in {SIGNS_EN[shared_sign]}. "
            f"Lagna->{lagna_p.sign_en}, Moon->{moon_p.sign_en}, Sun->{sun_p.sign_en}."
        )
    return (
        f"Mixed: Lagna->{lagna_p.sign_en} ({lagna_p.sign_lord}), "
        f"Moon->{moon_p.sign_en} ({moon_p.sign_lord}), "
        f"Sun->{sun_p.sign_en} ({sun_p.sign_lord})."
    )
