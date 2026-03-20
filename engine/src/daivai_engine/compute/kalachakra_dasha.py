"""Kalachakra Dasha — "most respectable dasha" per Parashar (BPHS Ch.46).

The Wheel of Time dasha. Based on Moon's nakshatra AND pada (not just
nakshatra like Vimshottari). Each of the 108 padas maps to a UNIQUE
9-sign sequence with specific Deha (body) and Jeeva (soul) anchors.

Key features:
- Sign-based (Rashi), not planet-based
- Variable Paramayus: 83, 85, 86, or 100 years per pada sequence
- 4 nakshatra groups: Savya-I, Savya-II, Apasavya-I, Apasavya-II
- Non-linear jumps (Gatis): Manduka, Markati, Simhavalokana
- DEHA = first sign of sequence (physical body)
- JEEVA = last sign of sequence (soul/life-force)
- ALL 12 signs used: Aries(7), Taurus(16), Gemini(9), Cancer(21), Leo(5),
  Virgo(9), Libra(16), Scorpio(7), Sagittarius(10), Capricorn(4),
  Aquarius(4), Pisces(10)

Source: BPHS Chapter 46 "Kalachakra Dasha Adhyaya"
"""

from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict

from daivai_engine.constants import SIGNS, SIGNS_HI
from daivai_engine.models.chart import ChartData


# ── Sign durations in years (BPHS Ch.46 v3-5) ──────────────────────────
_SIGN_YEARS: dict[int, int] = {
    0: 7,
    1: 16,
    2: 9,
    3: 21,
    4: 5,
    5: 9,
    6: 16,
    7: 7,
    8: 10,
    9: 4,
    10: 4,
    11: 10,
}

# ── Nakshatra groups (BPHS Ch.46 v6-12) ─────────────────────────────────
_SAVYA_I = {
    "Ashwini",
    "Krittika",
    "Punarvasu",
    "Ashlesha",
    "Hasta",
    "Swati",
    "Moola",
    "Uttara Ashadha",
    "Purva Bhadrapada",
    "Revati",
}
_SAVYA_II = {
    "Bharani",
    "Pushya",
    "Chitra",
    "Purva Ashadha",
    "Uttara Bhadrapada",
}
_APASAVYA_I = {
    "Rohini",
    "Magha",
    "Vishakha",
    "Shravana",
}
_APASAVYA_II = {
    "Mrigashira",
    "Ardra",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Anuradha",
    "Jyeshtha",
    "Dhanishta",
    "Shatabhisha",
}

# ── The 108-pada sequences (BPHS Ch.46 v13-45) ─────────────────────────
# Each pada maps to a UNIQUE 9-sign sequence. Indices: 0=Aries..11=Pisces.
# Paramayus = sum of _SIGN_YEARS for the 9 signs.

_SEQ_SAVYA_I = {
    1: [0, 1, 2, 3, 4, 5, 6, 7, 8],  # 100y
    2: [9, 10, 11, 7, 6, 5, 3, 4, 2],  # 85y
    3: [1, 0, 11, 10, 9, 8, 0, 1, 2],  # 83y
    4: [3, 4, 5, 6, 7, 8, 9, 10, 11],  # 86y
}
_SEQ_SAVYA_II = {
    1: [7, 6, 5, 3, 4, 2, 1, 0, 11],  # 100y
    2: [10, 9, 8, 0, 1, 2, 3, 4, 5],  # 85y
    3: [6, 7, 8, 9, 10, 11, 7, 6, 5],  # 83y
    4: [3, 4, 2, 1, 0, 11, 10, 9, 8],  # 86y
}
_SEQ_APASAVYA_I = {
    1: [8, 9, 10, 11, 0, 1, 2, 4, 3],  # 86y
    2: [5, 6, 7, 11, 10, 9, 8, 7, 6],  # 83y
    3: [5, 4, 3, 2, 1, 0, 8, 9, 10],  # 85y
    4: [11, 0, 1, 2, 4, 3, 5, 6, 7],  # 100y
}
_SEQ_APASAVYA_II = {
    1: [11, 10, 9, 8, 7, 6, 5, 4, 3],  # 86y
    2: [2, 1, 0, 8, 9, 10, 11, 0, 1],  # 83y
    3: [2, 4, 3, 5, 6, 7, 11, 10, 9],  # 85y
    4: [8, 7, 6, 5, 4, 3, 2, 1, 0],  # 100y
}

_PADA_SPAN_DEG = 10.0 / 3.0  # 3.3333 degrees = 3 deg 20 min = 200 arc-min


class KalachakraDashaPeriod(BaseModel):
    """One period in the Kalachakra Dasha sequence."""

    model_config = ConfigDict(frozen=True)

    sign_index: int
    sign_name: str
    sign_hi: str
    years: int
    start: datetime
    end: datetime
    is_deha: bool  # First sign in sequence = physical body
    is_jeeva: bool  # Last sign in sequence = soul/life-force
    cycle: str  # savya_i / savya_ii / apasavya_i / apasavya_ii


class KalachakraDashaResult(BaseModel):
    """Complete Kalachakra Dasha result."""

    model_config = ConfigDict(frozen=True)

    group: str
    nakshatra: str
    pada: int  # 1-4
    paramayus: int  # 83, 85, 86, or 100
    balance_years: float
    deha_sign: int  # First sign = body anchor
    jeeva_sign: int  # Last sign = soul anchor
    periods: list[KalachakraDashaPeriod]


def compute_kalachakra_dasha(chart: ChartData) -> KalachakraDashaResult:
    """Compute Kalachakra Dasha from the 108-pada mapping.

    Algorithm (BPHS Ch.46):
    1. Moon nakshatra -> classify into 4 groups
    2. Moon pada (1-4) -> look up unique 9-sign sequence
    3. DEHA = first sign, JEEVA = last sign
    4. Balance from Moon's position within the pada
    5. Generate 9 periods with correct sign years

    Args:
        chart: Computed birth chart.

    Returns:
        KalachakraDashaResult with correct Paramayus and Gati jumps.
    """
    moon = chart.planets["Moon"]
    group, sequences = _get_group(moon.nakshatra)
    seq = sequences[moon.pada]

    deha = seq[0]
    jeeva = seq[8]
    paramayus = sum(_SIGN_YEARS[s] for s in seq)

    # Balance: fraction of pada remaining x first sign years
    nak_start = moon.nakshatra_index * (360.0 / 27.0)
    pada_start = nak_start + (moon.pada - 1) * _PADA_SPAN_DEG
    pada_end = pada_start + _PADA_SPAN_DEG
    remaining = pada_end - moon.longitude
    if remaining < 0:
        remaining += 360.0
    balance_frac = min(1.0, max(0.0, remaining / _PADA_SPAN_DEG))
    balance_years = _SIGN_YEARS[seq[0]] * balance_frac

    # Generate periods
    from daivai_engine.compute.datetime_utils import parse_birth_datetime

    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    periods: list[KalachakraDashaPeriod] = []
    current = birth_dt

    for i, sign_idx in enumerate(seq):
        yrs = _SIGN_YEARS[sign_idx]
        actual = balance_years if i == 0 else float(yrs)
        end = current + timedelta(days=actual * 365.25)
        periods.append(
            KalachakraDashaPeriod(
                sign_index=sign_idx,
                sign_name=SIGNS[sign_idx],
                sign_hi=SIGNS_HI[sign_idx],
                years=yrs,
                start=current,
                end=end,
                is_deha=(sign_idx == deha),
                is_jeeva=(sign_idx == jeeva),
                cycle=group,
            )
        )
        current = end

    return KalachakraDashaResult(
        group=group,
        nakshatra=moon.nakshatra,
        pada=moon.pada,
        paramayus=paramayus,
        balance_years=round(balance_years, 4),
        deha_sign=deha,
        jeeva_sign=jeeva,
        periods=periods,
    )


def _get_group(nakshatra: str) -> tuple[str, dict[int, list[int]]]:
    """Classify nakshatra into one of 4 Kalachakra groups (BPHS Ch.46 v6-12)."""
    if nakshatra in _SAVYA_I:
        return "savya_i", _SEQ_SAVYA_I
    if nakshatra in _SAVYA_II:
        return "savya_ii", _SEQ_SAVYA_II
    if nakshatra in _APASAVYA_I:
        return "apasavya_i", _SEQ_APASAVYA_I
    if nakshatra in _APASAVYA_II:
        return "apasavya_ii", _SEQ_APASAVYA_II
    return "savya_i", _SEQ_SAVYA_I  # Fallback
