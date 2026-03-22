"""Rasi (sign-based) Dasha systems: Sthira, Shoola, Mandooka.

All three systems use zodiac signs as dasha lords with fixed annual durations
per sign, starting from lagna and progressing forward/backward depending on
lagna parity.

Sources:
    Sthira Dasha  — BPHS Ch.47
    Shoola Dasha  — BPHS Ch.48 (used for timing of severe events / maraka)
    Mandooka Dasha — BPHS Ch.49 (frog-jump alternating sign progression)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from daivai_engine.compute.datetime_utils import parse_birth_datetime
from daivai_engine.constants import (
    MANDOOKA_SIGN_YEARS,
    MANDOOKA_TOTAL_YEARS,
    SHOOLA_DASHA_YEARS,
    SHOOLA_TOTAL_YEARS,
    SIGNS,
    STHIRA_DASHA_YEARS,
    STHIRA_TOTAL_YEARS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_rasi import RasiAntardasha, RasiDashaPeriod


# ── Internal helpers ─────────────────────────────────────────────────────────


def _rasi_antardasha(
    md: RasiDashaPeriod,
    sign_years: dict[int, int],
    total_years: int,
) -> list[RasiAntardasha]:
    """Compute 12 Antardashas within a Rasi Dasha Mahadasha.

    Each sub-period duration = MD_days x (ad_sign_years / total_years).
    The order starts from the same sign as the MD, then cycles forward.

    Args:
        md: Parent Mahadasha period.
        sign_years: Mapping of sign_index → canonical years for the system.
        total_years: Total cycle length of the system.

    Returns:
        List of 12 RasiAntardasha objects.
    """
    md_days = (md.end - md.start).total_seconds() / 86400.0
    ads: list[RasiAntardasha] = []
    current = md.start

    for i in range(12):
        ad_sign_idx = (md.sign_index + i) % 12
        ad_years = sign_years[ad_sign_idx]
        ad_days = md_days * (ad_years / total_years)
        ad_end = current + timedelta(days=ad_days)
        ads.append(
            RasiAntardasha(
                sign=SIGNS[ad_sign_idx],
                sign_index=ad_sign_idx,
                start=current,
                end=ad_end,
            )
        )
        current = ad_end

    return ads


def _rasi_md_sequence(
    lagna: int,
    sign_years: dict[int, int],
    total_years: int,
    birth_dt: datetime,
) -> list[RasiDashaPeriod]:
    """Build 12 Mahadasha periods for a rasi dasha, no balance proration.

    Odd lagna (0-indexed even) → signs advance forward (Mesha=0 is odd in
    Sanskrit count = index 0, Vrishabha=index 1 is even, etc.).
    The Sanskrit "odd" sign is index 0,2,4,6,8,10 (Mesha, Mithuna …).
    Odd lagna → forward; even lagna → backward.

    Args:
        lagna: Lagna sign index (0=Mesha … 11=Meena).
        sign_years: sign_index → years mapping.
        total_years: Total cycle length.
        birth_dt: Birth datetime.

    Returns:
        List of 12 RasiDashaPeriod objects.
    """
    periods: list[RasiDashaPeriod] = []
    current_start = birth_dt
    forward = lagna % 2 == 0  # 0=Mesha=odd in Sanskrit = even index → forward

    for i in range(12):
        if forward:
            sign_idx = (lagna + i) % 12
        else:
            sign_idx = (lagna - i) % 12

        years = sign_years[sign_idx]
        days = years * 365.25
        end = current_start + timedelta(days=days)

        md = RasiDashaPeriod(
            sign=SIGNS[sign_idx],
            sign_index=sign_idx,
            years=years,
            start=current_start,
            end=end,
        )
        ads = _rasi_antardasha(md, sign_years, total_years)
        md = md.model_copy(update={"antardasha": ads})
        periods.append(md)
        current_start = end

    return periods


# ── Sthira Dasha ─────────────────────────────────────────────────────────────


def compute_sthira_dasha(chart: ChartData) -> list[RasiDashaPeriod]:
    """Compute Sthira Dasha periods (96-year cycle).

    Each sign has a fixed duration by sign type:
    - Chara (movable) signs → 7 years
    - Sthira (fixed) signs → 8 years
    - Dwiswabhava (dual/common) signs → 9 years

    Starts from lagna sign. Odd lagna → forward; even lagna → backward.
    Source: BPHS Ch.47.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 12 RasiDashaPeriod objects.
    """
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    return _rasi_md_sequence(
        chart.lagna_sign_index,
        STHIRA_DASHA_YEARS,
        STHIRA_TOTAL_YEARS,
        birth_dt,
    )


# ── Shoola Dasha ─────────────────────────────────────────────────────────────


def compute_shoola_dasha(chart: ChartData) -> list[RasiDashaPeriod]:
    """Compute Shoola Dasha periods (90-year cycle).

    Used for timing of maraka (death / severe crisis) events.
    Odd signs (Sanskrit count, 0-indexed even) → 7 years.
    Even signs (Sanskrit count, 0-indexed odd) → 8 years.

    Starts from lagna sign. Odd lagna → forward; even lagna → backward.
    Source: BPHS Ch.48.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 12 RasiDashaPeriod objects.
    """
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    return _rasi_md_sequence(
        chart.lagna_sign_index,
        SHOOLA_DASHA_YEARS,
        SHOOLA_TOTAL_YEARS,
        birth_dt,
    )


def get_shoola_maraka_signs(chart: ChartData) -> list[int]:
    """Return the sign indices most relevant to Shoola Dasha maraka timing.

    The 2nd and 7th houses from lagna are primary maraka houses; their
    signs are the most critical periods in Shoola Dasha for death/illness.

    Args:
        chart: Computed birth chart.

    Returns:
        List of two sign indices [2nd-house sign, 7th-house sign].
    """
    lagna = chart.lagna_sign_index
    return [(lagna + 1) % 12, (lagna + 6) % 12]


# ── Mandooka Dasha ───────────────────────────────────────────────────────────


def _mandooka_sign_sequence(lagna: int) -> list[int]:
    """Build the Mandooka (frog-jump) sign order starting from lagna.

    Mandooka leaps every alternate sign (frog-jump), cycling through all 12.
    Pattern for odd lagna (forward): lagna → +2 → +4 … (evens fill gap).
    Pattern for even lagna (backward): lagna → -2 → -4 … (odds fill gap).

    The jump order visits: [lagna, lagna±2, lagna±4, lagna±6, lagna±8,
    lagna±10, lagna±1, lagna±3, lagna±5, lagna±7, lagna±9, lagna±11].

    Args:
        lagna: Lagna sign index.

    Returns:
        Ordered list of 12 sign indices.
    """
    forward = lagna % 2 == 0
    if forward:
        evens = [(lagna + 2 * i) % 12 for i in range(6)]
        odds = [(lagna + 2 * i + 1) % 12 for i in range(6)]
    else:
        evens = [(lagna - 2 * i) % 12 for i in range(6)]
        odds = [(lagna - 2 * i - 1) % 12 for i in range(6)]
    return evens + odds


def compute_mandooka_dasha(chart: ChartData) -> list[RasiDashaPeriod]:
    """Compute Mandooka Dasha periods (84-year cycle).

    Named for the frog's leap (mandooka = frog): signs are visited in an
    alternating jump pattern rather than consecutively. Each sign lasts
    exactly 7 years. Total = 12 x 7 = 84 years.

    Source: BPHS Ch.49.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 12 RasiDashaPeriod objects in Mandooka jump order.
    """
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    lagna = chart.lagna_sign_index
    sign_order = _mandooka_sign_sequence(lagna)

    uniform_years: dict[int, int] = {i: MANDOOKA_SIGN_YEARS for i in range(12)}

    periods: list[RasiDashaPeriod] = []
    current_start = birth_dt

    for sign_idx in sign_order:
        days = MANDOOKA_SIGN_YEARS * 365.25
        end = current_start + timedelta(days=days)

        md = RasiDashaPeriod(
            sign=SIGNS[sign_idx],
            sign_index=sign_idx,
            years=MANDOOKA_SIGN_YEARS,
            start=current_start,
            end=end,
        )
        ads = _rasi_antardasha(md, uniform_years, MANDOOKA_TOTAL_YEARS)
        md = md.model_copy(update={"antardasha": ads})
        periods.append(md)
        current_start = end

    return periods
