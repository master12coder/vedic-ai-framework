"""Varsha Pravesh (Solar Return) with full Pydantic models.

Finds the exact moment the transiting Sun returns to its natal sidereal
longitude in a given year. Includes Muntha (annual ascendant progression),
year lord, and Panchavargiya Bala for the annual chart.

Sources: Tajaka Neelakanthi, Dr. B.V. Raman's Varshphal, Prashna Marga.
"""

from __future__ import annotations

from datetime import UTC, datetime

import swisseph as swe
from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.compute.chart import compute_chart
from daivai_engine.constants import (
    DAY_NAMES,
    DAY_NAMES_HI,
    DAY_PLANET,
    NAKSHATRA_SPAN_DEG,
    PLANETS,
    PLANETS_HI,
    SIGN_LORDS,
    SIGNS,
    SIGNS_EN,
    SIGNS_HI,
)
from daivai_engine.models.chart import ChartData


class MunthaResult(BaseModel):
    """Muntha — the annual Ascendant that progresses one sign per year.

    In Varshphal, Muntha advances one sign from the natal Lagna every year.
    It marks the primary zone of karmic activity for the current solar year.
    """

    model_config = ConfigDict(frozen=True)

    sign_index: int = Field(ge=0, le=11)
    sign: str  # Sanskrit sign name (e.g., "Karka")
    sign_en: str  # English (e.g., "Cancer")
    sign_hi: str  # Hindi (e.g., "कर्क")
    lord: str  # Sign lord planet
    house_from_lagna: int = Field(ge=1, le=12)
    description: str


class VarshaPraveshResult(BaseModel):
    """Complete Varsha Pravesh (Solar Return) computation result.

    Captures the moment the transiting Sun reaches the natal Sun's exact
    sidereal longitude, forming the basis for annual predictions.
    """

    model_config = ConfigDict(frozen=True)

    year: int
    solar_return_datetime: str  # UTC — "YYYY-MM-DD HH:MM:SS UTC"
    solar_return_jd: float  # Julian Day of solar return
    natal_sun_longitude: float  # Natal Sun sidereal longitude
    annual_chart: ChartData  # Full chart at solar return moment
    muntha: MunthaResult  # Annual progressed Ascendant
    year_lord: str  # Planet ruling weekday of solar return
    year_lord_hi: str
    year_day_name: str  # Weekday name (e.g., "Thursday")
    year_day_name_hi: str
    panchavargiya_bala: dict[str, str]  # 5-fold strength of year lord


def compute_varsha_pravesh(
    birth_chart: ChartData,
    year: int,
) -> VarshaPraveshResult:
    """Compute Varsha Pravesh (Solar Return) for a given calendar year.

    Steps:
      1. Find the Julian Day when the transiting Sun returns to natal longitude.
      2. Compute the full chart at that moment (at birth place).
      3. Compute Muntha (lagna + age signs forward).
      4. Determine year lord from the weekday of the solar return.
      5. Assess Panchavargiya Bala of the year lord.

    Args:
        birth_chart: Native's natal birth chart.
        year: Target calendar year (e.g., 2026).

    Returns:
        VarshaPraveshResult with all annual chart data.
    """
    natal_sun_lon = birth_chart.planets["Sun"].longitude
    sr_jd = _find_solar_return_jd(natal_sun_lon, year)
    sr_dt = _jd_to_utc_datetime(sr_jd)

    annual_chart = compute_chart(
        name=f"{birth_chart.name} Varsha Pravesh {year}",
        dob=sr_dt.strftime("%d/%m/%Y"),
        tob=sr_dt.strftime("%H:%M"),
        lat=birth_chart.latitude,
        lon=birth_chart.longitude,
        tz_name=birth_chart.timezone_name,
        gender=birth_chart.gender,
    )

    birth_year = int(birth_chart.dob.split("/")[2])
    age = year - birth_year
    muntha_sign = (birth_chart.lagna_sign_index + age) % 12
    muntha = _build_muntha(muntha_sign, birth_chart)

    # Weekday → year lord (Sunday=0 system via Monday=0 correction)
    weekday = sr_dt.weekday()  # Monday=0, Sunday=6
    day_idx = (weekday + 1) % 7  # Convert to Sunday=0
    year_lord = DAY_PLANET.get(day_idx, "Sun")

    yr_lord_hi = PLANETS_HI[PLANETS.index(year_lord)] if year_lord in PLANETS else year_lord

    return VarshaPraveshResult(
        year=year,
        solar_return_datetime=sr_dt.strftime("%Y-%m-%d %H:%M:%S UTC"),
        solar_return_jd=round(sr_jd, 6),
        natal_sun_longitude=round(natal_sun_lon, 4),
        annual_chart=annual_chart,
        muntha=muntha,
        year_lord=year_lord,
        year_lord_hi=yr_lord_hi,
        year_day_name=DAY_NAMES.get(day_idx, "Sunday"),
        year_day_name_hi=DAY_NAMES_HI.get(day_idx, "रविवार"),
        panchavargiya_bala=_panchavargiya_bala(annual_chart, year_lord),
    )


def get_muntha_annual(
    birth_chart: ChartData,
    year: int,
) -> MunthaResult:
    """Compute only the Muntha for a given year (without running the full chart).

    Muntha progresses one sign per year from the natal Lagna sign.
    Age = target_year - birth_year.

    Args:
        birth_chart: Natal chart.
        year: Target year.

    Returns:
        MunthaResult for that year.
    """
    birth_year = int(birth_chart.dob.split("/")[2])
    age = year - birth_year
    muntha_sign = (birth_chart.lagna_sign_index + age) % 12
    return _build_muntha(muntha_sign, birth_chart)


# ── Private helpers ────────────────────────────────────────────────────────────


def _build_muntha(muntha_sign: int, birth_chart: ChartData) -> MunthaResult:
    """Construct a MunthaResult for the given sign index."""
    lord = SIGN_LORDS[muntha_sign]
    house = ((muntha_sign - birth_chart.lagna_sign_index) % 12) + 1
    desc = (
        f"Muntha in {SIGNS[muntha_sign]} ({SIGNS_EN[muntha_sign]}), "
        f"lord {lord}, occupies house {house} from natal Lagna. "
        f"This sign is the primary zone of annual karmic activation."
    )
    return MunthaResult(
        sign_index=muntha_sign,
        sign=SIGNS[muntha_sign],
        sign_en=SIGNS_EN[muntha_sign],
        sign_hi=SIGNS_HI[muntha_sign],
        lord=lord,
        house_from_lagna=house,
        description=desc,
    )


def _panchavargiya_bala(chart: ChartData, year_lord: str) -> dict[str, str]:
    """Compute simplified Panchavargiya Bala (5-fold strength) of the year lord.

    The five components:
      1. Janma Rasi Bala — dignity of year lord in annual chart
      2. Hora Bala        — combustion status
      3. Weekday Bala     — year lord always has this (it is the weekday lord)
      4. Masa Bala        — dignity approximation for monthly strength
      5. Abda Bala        — year lord has full annual strength

    Returns:
        Mapping of bala_name → "strong" | "moderate" | "weak".
    """
    planet = chart.planets.get(year_lord)
    if not planet:
        return {}

    strong = {"exalted", "own", "mooltrikona"}
    dignity = planet.dignity

    janma = "strong" if dignity in strong else ("weak" if dignity == "debilitated" else "moderate")
    hora = "weak" if planet.is_combust else "strong"
    weekday = "strong"  # Year lord always has weekday bala
    masa = "strong" if dignity in strong else "moderate"
    abda = "strong"  # Year lord has full Abda Bala by definition

    return {
        "janma_rasi_bala": janma,
        "hora_bala": hora,
        "weekday_bala": weekday,
        "masa_bala": masa,
        "abda_bala": abda,
    }


def _find_solar_return_jd(natal_sun_lon: float, year: int) -> float:
    """Find Julian Day when the sidereal Sun reaches the natal longitude.

    Uses a coarse daily scan followed by 50-iteration binary search.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year, 12, 31, 23.99)

    jd = jd_start
    prev_lon = _sun_lon(jd)
    while jd < jd_end:
        jd += 1.0
        cur_lon = _sun_lon(jd)

        if prev_lon <= cur_lon:
            crossed = prev_lon <= natal_sun_lon < cur_lon
        else:
            crossed = natal_sun_lon >= prev_lon or natal_sun_lon < cur_lon

        if crossed:
            lo, hi = jd - 1.0, jd
            for _ in range(50):
                mid = (lo + hi) / 2.0
                diff = _sun_diff(mid, natal_sun_lon)
                lo, hi = (mid, hi) if diff < 0 else (lo, mid)
            return float((lo + hi) / 2.0)

        prev_lon = cur_lon

    return float(swe.julday(year, 3, 14, 12.0))  # Fallback


def _sun_lon(jd: float) -> float:
    """Return sidereal Sun longitude at the given Julian Day."""
    result = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    lon: float = result[0][0]
    return lon


def _sun_diff(jd: float, target: float) -> float:
    """Signed difference between current Sun longitude and target (-180..+180)."""
    diff = _sun_lon(jd) - target
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


# ── Nakshatra balance helper (used by mudda_dasha) ────────────────────────────


def nakshatra_balance(moon_longitude: float) -> float:
    """Return fraction of nakshatra period remaining at a given Moon longitude.

    Used for computing Mudda Dasha balance in the annual chart.

    Args:
        moon_longitude: Sidereal Moon longitude (0-360).

    Returns:
        Float 0..1 — fraction of nakshatra remaining.
    """
    nak_idx = int(moon_longitude / NAKSHATRA_SPAN_DEG)
    elapsed = moon_longitude - nak_idx * NAKSHATRA_SPAN_DEG
    return 1.0 - (elapsed / NAKSHATRA_SPAN_DEG)
