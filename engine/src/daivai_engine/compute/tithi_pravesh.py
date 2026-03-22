"""Tithi Pravesh (Lunar Return / Tithi Return).

Computes the exact moment the Sun-Moon angular difference (Tithi arc)
returns to the natal value. One full lunar month ≈ 29.5 days, so
approximately 12-13 Tithi Pravesh events occur each year.

In Tajaka jyotish the Tithi Pravesh chart for a given month is used to
refine predictions within the annual (Varsha Pravesh) period.

Sources: Tajaka Neelakanthi, Neel Kanthi's Varshphal commentary,
         K.N. Rao's "Predicting through Jaimini's Chara Dasha".
"""

from __future__ import annotations

from datetime import UTC, datetime

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.compute.chart import compute_chart
from daivai_engine.models.chart import ChartData


# Month name lookup (1-indexed)
_MONTH_NAMES: list[str] = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# Tithi names for Shukla Paksha (1-15)
_SHUKLA_TITHIS: list[str] = [
    "Pratipada",
    "Dwitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
    "Purnima",
]

# Tithi names for Krishna Paksha (16-30)
_KRISHNA_TITHIS: list[str] = [
    "Pratipada",
    "Dwitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dwadashi",
    "Trayodashi",
    "Chaturdashi",
    "Amavasya",
]


class TithiPraveshResult(BaseModel):
    """Tithi Pravesh (Lunar Return) result for a specific month.

    Represents the exact moment the Sun-Moon angular difference returns
    to its natal value during a given calendar month.
    """

    model_config = ConfigDict(frozen=True)

    year: int
    month: int = Field(ge=1, le=12)
    month_name: str
    tithi_pravesh_datetime: str  # UTC — "YYYY-MM-DD HH:MM:SS UTC"
    tithi_pravesh_jd: float  # Julian Day
    natal_tithi_arc: float  # Natal Sun-Moon angle (0-360°)
    natal_tithi_number: int = Field(ge=1, le=30)
    natal_tithi_name: str  # e.g., "Shukla Saptami"
    natal_paksha: str  # "Shukla" or "Krishna"
    annual_chart: ChartData  # Chart computed for Tithi Pravesh moment


def compute_tithi_pravesh(
    birth_chart: ChartData,
    year: int,
    month: int,
) -> TithiPraveshResult:
    """Compute the Tithi Pravesh for a given year and month.

    Finds the moment in `month` when (transit Moon longitude - transit Sun
    longitude) mod 360° equals the natal (Moon - Sun) mod 360°, then
    builds the full chart for that instant.

    Args:
        birth_chart: Native's natal birth chart.
        year: Calendar year (e.g., 2026).
        month: Calendar month 1-12.

    Returns:
        TithiPraveshResult for that month.
    """
    natal_arc = _natal_tithi_arc(birth_chart)
    tithi_num = int(natal_arc / 12.0) + 1
    tithi_num = min(tithi_num, 30)

    tp_jd = _find_tithi_return(natal_arc, year, month)
    tp_dt = _jd_to_utc_datetime(tp_jd)

    chart = compute_chart(
        name=f"{birth_chart.name} Tithi Pravesh {year}-{month:02d}",
        dob=tp_dt.strftime("%d/%m/%Y"),
        tob=tp_dt.strftime("%H:%M"),
        lat=birth_chart.latitude,
        lon=birth_chart.longitude,
        tz_name=birth_chart.timezone_name,
        gender=birth_chart.gender,
    )

    return TithiPraveshResult(
        year=year,
        month=month,
        month_name=_MONTH_NAMES[month],
        tithi_pravesh_datetime=tp_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        tithi_pravesh_jd=round(tp_jd, 6),
        natal_tithi_arc=round(natal_arc, 4),
        natal_tithi_number=tithi_num,
        natal_tithi_name=_tithi_name(tithi_num),
        natal_paksha="Shukla" if tithi_num <= 15 else "Krishna",
        annual_chart=chart,
    )


def compute_annual_tithi_pravesh(
    birth_chart: ChartData,
    year: int,
) -> list[TithiPraveshResult]:
    """Compute all 12 Tithi Pravesh charts for a given year.

    Each month yields the moment the natal Tithi arc recurs.

    Args:
        birth_chart: Native's natal birth chart.
        year: Calendar year (e.g., 2026).

    Returns:
        List of 12 TithiPraveshResult, one per calendar month.
    """
    return [compute_tithi_pravesh(birth_chart, year, m) for m in range(1, 13)]


def natal_tithi_number(birth_chart: ChartData) -> int:
    """Return the natal Tithi number (1-30) from a birth chart.

    Tithi number = floor(Sun-Moon arc / 12) + 1, clamped to 1-30.

    Args:
        birth_chart: Natal birth chart.

    Returns:
        Integer 1-30.
    """
    arc = _natal_tithi_arc(birth_chart)
    num = int(arc / 12.0) + 1
    return min(num, 30)


# ── Private helpers ────────────────────────────────────────────────────────────


def _natal_tithi_arc(chart: ChartData) -> float:
    """Compute the natal Sun-Moon angular difference (Tithi arc, 0-360°)."""
    sun = chart.planets["Sun"].longitude
    moon = chart.planets["Moon"].longitude
    return (moon - sun) % 360.0


def _find_tithi_return(natal_arc: float, year: int, month: int) -> float:
    """Find the Julian Day when the Tithi arc matches the natal value in a month.

    Uses hourly scanning followed by 50-iteration binary search within
    the crossing interval.

    Args:
        natal_arc: Target Sun-Moon angle (0-360°).
        year: Calendar year.
        month: Calendar month (1-12).

    Returns:
        Julian Day of the Tithi Pravesh moment.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    jd_start = swe.julday(year, month, 1, 0.0)
    if month < 12:
        jd_end = swe.julday(year, month + 1, 1, 0.0)
    else:
        jd_end = swe.julday(year + 1, 1, 1, 0.0)

    step = 1.0 / 24.0  # 1-hour scan
    jd = jd_start
    prev = _tithi_diff(jd, natal_arc)

    while jd < jd_end:
        jd += step
        cur = _tithi_diff(jd, natal_arc)

        if prev * cur < 0:  # Sign change → crossing found
            lo, hi = jd - step, jd
            for _ in range(50):
                mid = (lo + hi) / 2.0
                d = _tithi_diff(mid, natal_arc)
                lo, hi = (mid, hi) if d * prev >= 0 else (lo, mid)
            return float((lo + hi) / 2.0)

        prev = cur

    return float((jd_start + jd_end) / 2.0)  # Fallback: mid-month


def _get_tithi_arc(jd: float) -> float:
    """Return (Moon - Sun) mod 360° at the given Julian Day (sidereal Lahiri)."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    sun_lon: float = swe.calc_ut(jd, swe.SUN, flags)[0][0]
    moon_lon: float = swe.calc_ut(jd, swe.MOON, flags)[0][0]
    return (moon_lon - sun_lon) % 360.0


def _tithi_diff(jd: float, natal_arc: float) -> float:
    """Signed difference between current Tithi arc and natal (-180..+180)."""
    diff = _get_tithi_arc(jd) - natal_arc
    if diff > 180:
        diff -= 360
    if diff < -180:
        diff += 360
    return diff


def _jd_to_utc_datetime(jd: float) -> datetime:
    """Convert a Julian Day number to a UTC datetime."""
    year, month, day, hour = swe.revjul(jd)
    h = int(hour)
    m = int((hour - h) * 60)
    return datetime(year, month, day, h, m, tzinfo=UTC)


def _tithi_name(tithi_num: int) -> str:
    """Return the traditional name for a Tithi number (1-30)."""
    if tithi_num <= 15:
        return f"Shukla {_SHUKLA_TITHIS[tithi_num - 1]}"
    return f"Krishna {_KRISHNA_TITHIS[tithi_num - 16]}"
