"""Additional Dasha systems — Yogini, Ashtottari, Chara (Jaimini)."""

from __future__ import annotations

from datetime import timedelta

from daivai_engine.compute.datetime_utils import parse_birth_datetime
from daivai_engine.constants import (
    ASHTOTTARI_TOTAL_YEARS as _ASHTOTTARI_TOTAL_YEARS,
)
from daivai_engine.constants import (
    NAKSHATRA_SPAN_DEG,
    SIGN_LORDS,
    SIGNS,
)
from daivai_engine.constants import (
    YOGINI_TOTAL_YEARS as _YOGINI_TOTAL_YEARS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_extra import (
    AshtottariDashaPeriod,
    CharaDashaPeriod,
    YoginiDashaPeriod,
)


# ── Yogini Dasha (36-year cycle) ────────────────────────────────────────────

YOGINI_SEQUENCE = [
    ("Mangala", "Moon", 1),
    ("Pingala", "Sun", 2),
    ("Dhanya", "Jupiter", 3),
    ("Bhramari", "Mars", 4),
    ("Bhadrika", "Mercury", 5),
    ("Ulka", "Saturn", 6),
    ("Siddha", "Venus", 7),
    ("Sankata", "Rahu", 8),
]
YOGINI_TOTAL_YEARS = _YOGINI_TOTAL_YEARS


# Yogini start nakshatra mapping: nakshatra_index % 8 -> yogini index
# Ashwini(0)->Mangala, Bharani(1)->Pingala, Krittika(2)->Dhanya,
# Rohini(3)->Bhramari, Mrigashira(4)->Bhadrika, Ardra(5)->Ulka,
# Punarvasu(6)->Siddha, Pushya(7)->Sankata, then repeats.
# Source: Jataka Parijata, Yogini Dasha chapter.
def _yogini_start_index(nakshatra_index: int) -> int:
    """Get starting Yogini from Moon's nakshatra.

    Each nakshatra maps to a Yogini by simple modulo-8 cycle starting
    from Ashwini (index 0) = Mangala.

    Returns:
        Index into YOGINI_SEQUENCE (0=Mangala … 7=Sankata).
    """
    return nakshatra_index % 8


def compute_yogini_dasha(chart: ChartData) -> list[YoginiDashaPeriod]:
    """Compute Yogini Dasha periods (36-year cycle).

    Args:
        chart: Computed birth chart

    Returns:
        List of 8 Yogini Dasha periods.
    """
    moon = chart.planets["Moon"]
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)

    start_idx = _yogini_start_index(moon.nakshatra_index)

    # Calculate balance of first dasha
    degree_in_nak = moon.longitude - moon.nakshatra_index * NAKSHATRA_SPAN_DEG
    fraction_elapsed = degree_in_nak / NAKSHATRA_SPAN_DEG
    balance = 1.0 - fraction_elapsed

    periods: list[YoginiDashaPeriod] = []
    current_start = birth_dt

    for i in range(8):
        idx = (start_idx + i) % 8
        name, planet, years = YOGINI_SEQUENCE[idx]

        if i == 0:
            effective_years = years * balance
        else:
            effective_years = float(years)

        days = effective_years * 365.25
        end = current_start + timedelta(days=days)

        periods.append(
            YoginiDashaPeriod(
                yogini_name=name,
                planet=planet,
                years=years,
                start=current_start,
                end=end,
            )
        )
        current_start = end

    return periods


# ── Ashtottari Dasha (108-year cycle) ──────────────────────────────────────

ASHTOTTARI_SEQUENCE = [
    ("Sun", 6),
    ("Moon", 15),
    ("Mars", 8),
    ("Mercury", 17),
    ("Saturn", 10),
    ("Jupiter", 19),
    ("Rahu", 12),
    ("Venus", 21),
]
ASHTOTTARI_TOTAL_YEARS = _ASHTOTTARI_TOTAL_YEARS

# Ashtottari uses only specific nakshatras (Ardra-based system)
ASHTOTTARI_NAK_LORDS = {
    5: "Sun",  # Ardra
    6: "Moon",  # Punarvasu
    7: "Mars",  # Pushya
    8: "Mercury",  # Ashlesha
    9: "Saturn",  # Magha
    10: "Jupiter",  # P.Phalguni
    11: "Rahu",  # U.Phalguni
    12: "Venus",  # Hasta
}


def _ashtottari_start_lord(nakshatra_index: int) -> str:
    """Get starting Ashtottari lord from Moon's nakshatra."""
    # Map nakshatra to Ashtottari sequence
    nak_mod = nakshatra_index % 8
    lord_map = [p for p, _ in ASHTOTTARI_SEQUENCE]
    return lord_map[nak_mod]


def is_ashtottari_applicable(chart: ChartData) -> bool:
    """Check if Ashtottari Dasha applies for this chart.

    Applicability condition (BPHS Ch.45): Rahu must be in a kendra
    (houses 1/4/7/10) or trikona (5/9) from the lagna lord's sign.
    Rahu in the same sign as the lagna lord also qualifies (counts as 1st).

    Source: BPHS Ch.45 "Ashtottari Dasha Adhyaya".
    """
    rahu = chart.planets["Rahu"]
    lagna_lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lagna_lord = chart.planets.get(lagna_lord_name)
    if lagna_lord is None:
        return False  # Rahu/Ketu as lagna lord edge case

    rahu_sign = rahu.sign_index
    lord_sign = lagna_lord.sign_index
    distance = ((rahu_sign - lord_sign) % 12) + 1  # 1-indexed house distance
    kendra_trikona = {1, 4, 5, 7, 9, 10}
    return distance in kendra_trikona


def compute_ashtottari_dasha(chart: ChartData) -> list[AshtottariDashaPeriod]:
    """Compute Ashtottari Dasha periods (108-year cycle).

    Note: Use is_ashtottari_applicable(chart) to check if this system applies
    before using results. When inapplicable, Vimshottari is the default.

    Args:
        chart: Computed birth chart

    Returns:
        List of 8 Ashtottari Dasha periods.
    """
    moon = chart.planets["Moon"]
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)

    start_lord = _ashtottari_start_lord(moon.nakshatra_index)
    start_idx = next(i for i, (p, _) in enumerate(ASHTOTTARI_SEQUENCE) if p == start_lord)

    nak_span = 360.0 / 27.0
    degree_in_nak = moon.longitude - moon.nakshatra_index * nak_span
    balance = 1.0 - (degree_in_nak / nak_span)

    periods: list[AshtottariDashaPeriod] = []
    current_start = birth_dt

    for i in range(8):
        idx = (start_idx + i) % 8
        planet, years = ASHTOTTARI_SEQUENCE[idx]

        effective_years = years * balance if i == 0 else float(years)
        days = effective_years * 365.25
        end = current_start + timedelta(days=days)

        periods.append(
            AshtottariDashaPeriod(
                planet=planet,
                years=years,
                start=current_start,
                end=end,
            )
        )
        current_start = end

    return periods


# ── Chara Dasha (Jaimini, sign-based) ──────────────────────────────────────


def _chara_dasha_years(sign_index: int, chart: ChartData) -> float:
    """Calculate Chara Dasha years for a sign.

    Years = distance of sign lord from the sign.
    For dual signs, the count is different.
    """
    lord = SIGN_LORDS[sign_index]
    lord_sign = chart.planets[lord].sign_index

    # For odd signs, count forward; for even, count backward
    if sign_index % 2 == 0:  # Odd sign
        distance = (lord_sign - sign_index) % 12
    else:  # Even sign
        distance = (sign_index - lord_sign) % 12

    # If lord is in own sign, years = 12
    if distance == 0:
        distance = 12

    return float(distance)


def compute_chara_dasha(chart: ChartData) -> list[CharaDashaPeriod]:
    """Compute Chara (Jaimini) Dasha — sign-based dasha system.

    Starting sign depends on whether lagna is in odd/even sign.
    Odd lagna: signs go forward from lagna.
    Even lagna: signs go backward from lagna.

    Args:
        chart: Computed birth chart

    Returns:
        List of 12 Chara Dasha periods (one per sign).
    """
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    lagna = chart.lagna_sign_index

    periods: list[CharaDashaPeriod] = []
    current_start = birth_dt

    for i in range(12):
        if lagna % 2 == 0:  # Odd sign lagna — forward
            sign_idx = (lagna + i) % 12
        else:  # Even sign lagna — backward
            sign_idx = (lagna - i) % 12

        years = _chara_dasha_years(sign_idx, chart)
        days = years * 365.25
        end = current_start + timedelta(days=days)

        periods.append(
            CharaDashaPeriod(
                sign=SIGNS[sign_idx],
                sign_index=sign_idx,
                years=years,
                start=current_start,
                end=end,
            )
        )
        current_start = end

    return periods
