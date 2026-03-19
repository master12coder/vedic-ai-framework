"""Hindu Calendar — Samvat, months, Sankranti, Ekadashi, festivals, Choghadiya.

All dates are COMPUTED from astronomical positions via Swiss Ephemeris,
not looked up from tables.

Source: Dharmasindhu, Nirnaya Sindhu, Surya Siddhanta.
"""

from __future__ import annotations

from datetime import date

import swisseph as swe
from pydantic import BaseModel

from daivai_engine.constants import DEGREES_PER_SIGN, SIGNS_HI


class SankrantiDate(BaseModel):
    """Sun's transit into a new sign."""

    sign_index: int
    sign_hi: str
    date: str  # YYYY-MM-DD
    name: str  # e.g. "Makar Sankranti"


class FestivalDate(BaseModel):
    """A computed Hindu festival date."""

    name: str
    name_hi: str
    date: str  # YYYY-MM-DD
    tithi: str
    description: str


class ChoghadiyaPeriod(BaseModel):
    """One Choghadiya time slot."""

    name: str
    name_hi: str
    quality: str  # shubh / labh / amrit / chal / rog / kaal / udveg
    start_hour: float  # Hours from midnight (0-24)
    end_hour: float
    is_auspicious: bool


# Sankranti names — Surya Siddhanta
_SANKRANTI_NAMES = {
    0: "Mesh Sankranti",
    1: "Vrishabh Sankranti",
    2: "Mithun Sankranti",
    3: "Kark Sankranti",
    4: "Simha Sankranti",
    5: "Kanya Sankranti",
    6: "Tula Sankranti",
    7: "Vrischika Sankranti",
    8: "Dhanu Sankranti",
    9: "Makar Sankranti",
    10: "Kumbh Sankranti",
    11: "Meen Sankranti",
}

# Choghadiya sequence starting from Sunday's day lord
# Sunday=Sun, Mon=Moon, Tue=Mars, Wed=Mercury, Thu=Jupiter, Fri=Venus, Sat=Saturn
_CHOG_NAMES = ["Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]
_CHOG_NAMES_HI = ["उद्वेग", "चल", "लाभ", "अमृत", "काल", "शुभ", "रोग"]
_CHOG_QUALITY = {
    "Udveg": "udveg",
    "Chal": "chal",
    "Labh": "labh",
    "Amrit": "amrit",
    "Kaal": "kaal",
    "Shubh": "shubh",
    "Rog": "rog",
}
_CHOG_AUSPICIOUS = {"Labh", "Amrit", "Shubh"}
# Day Choghadiya starting index per weekday (Sun=0..Sat=6) — traditional
_CHOG_DAY_START = {0: 0, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 6}


def gregorian_to_samvat(d: date) -> dict[str, int | str]:
    """Convert Gregorian date to Vikram/Shaka Samvat years.

    Vikram Samvat ≈ Gregorian + 57 (starts Chaitra Shukla Pratipada)
    Shaka Samvat = Gregorian - 78 (used by Indian government)
    Kali Yuga = Gregorian + 3101

    Source: Indian calendar reform committee (1957).
    """
    # Approximate: Vikram new year is around March-April
    vs = d.year + 57 if d.month >= 4 else d.year + 56
    return {
        "vikram_samvat": vs,
        "shaka_samvat": d.year - 78,
        "kali_yuga": d.year + 3101,
        "gregorian": d.isoformat(),
    }


def get_sankranti_dates(year: int) -> list[SankrantiDate]:
    """Compute all 12 Sankranti dates for a year using Swiss Ephemeris.

    Sankranti = moment Sun's sidereal longitude crosses a 30° boundary.

    Source: Surya Siddhanta.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    results: list[SankrantiDate] = []

    for sign_idx in range(12):
        target_lon = sign_idx * DEGREES_PER_SIGN
        jd = _find_sun_crossing(target_lon, year)
        if jd:
            y, m, d, _h = swe.revjul(jd)
            results.append(
                SankrantiDate(
                    sign_index=sign_idx,
                    sign_hi=SIGNS_HI[sign_idx],
                    date=f"{y:04d}-{m:02d}-{d:02d}",
                    name=_SANKRANTI_NAMES.get(sign_idx, f"Sankranti {sign_idx + 1}"),
                )
            )

    results.sort(key=lambda s: s.date)
    return results


def get_choghadiya(
    d: date, sunrise_hour: float = 6.0, sunset_hour: float = 18.0
) -> list[ChoghadiyaPeriod]:
    """Compute 16 Choghadiya periods (8 day + 8 night) for a date.

    Day divided into 8 equal segments from sunrise to sunset.
    Night divided into 8 equal segments from sunset to next sunrise.

    Source: Traditional panchang, based on weekday planetary hours.
    """
    weekday = d.weekday()
    day_idx = (weekday + 1) % 7  # Sunday=0

    day_duration = sunset_hour - sunrise_hour
    night_duration = 24.0 - day_duration
    day_slot = day_duration / 8.0
    night_slot = night_duration / 8.0

    start_idx = _CHOG_DAY_START.get(day_idx, 0)
    periods: list[ChoghadiyaPeriod] = []

    # 8 day slots
    for i in range(8):
        name_idx = (start_idx + i) % 7
        name = _CHOG_NAMES[name_idx]
        periods.append(
            ChoghadiyaPeriod(
                name=name,
                name_hi=_CHOG_NAMES_HI[name_idx],
                quality=_CHOG_QUALITY[name],
                start_hour=round(sunrise_hour + i * day_slot, 2),
                end_hour=round(sunrise_hour + (i + 1) * day_slot, 2),
                is_auspicious=name in _CHOG_AUSPICIOUS,
            )
        )

    # 8 night slots (start from planet ruling the night)
    night_start_idx = (start_idx + 4) % 7  # Night starts 4 planets ahead
    for i in range(8):
        name_idx = (night_start_idx + i) % 7
        name = _CHOG_NAMES[name_idx]
        start_h = sunset_hour + i * night_slot
        end_h = sunset_hour + (i + 1) * night_slot
        if start_h >= 24:
            start_h -= 24
        if end_h >= 24:
            end_h -= 24
        periods.append(
            ChoghadiyaPeriod(
                name=name,
                name_hi=_CHOG_NAMES_HI[name_idx],
                quality=_CHOG_QUALITY[name],
                start_hour=round(start_h, 2),
                end_hour=round(end_h, 2),
                is_auspicious=name in _CHOG_AUSPICIOUS,
            )
        )

    return periods


def _find_sun_crossing(target_lon: float, year: int) -> float | None:
    """Find JD when sidereal Sun longitude crosses target_lon in given year."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH

    jd_start = swe.julday(year, 1, 1, 0.0)
    jd_end = swe.julday(year, 12, 31, 23.99)

    jd = jd_start
    prev_lon = swe.calc_ut(jd, swe.SUN, flags)[0][0]  # type: ignore[index]

    while jd < jd_end:
        jd += 1.0
        cur_lon: float = swe.calc_ut(jd, swe.SUN, flags)[0][0]  # type: ignore[index]
        # Check if target crossed between prev and cur
        if _crossed(prev_lon, cur_lon, target_lon):
            # Binary search
            lo, hi = jd - 1.0, jd
            for _ in range(40):
                mid = (lo + hi) / 2.0
                mid_lon: float = swe.calc_ut(mid, swe.SUN, flags)[0][0]  # type: ignore[index]
                if _crossed(prev_lon, mid_lon, target_lon):
                    hi = mid
                else:
                    lo = mid
                    prev_lon = mid_lon
            result_jd: float = (lo + hi) / 2.0
            return result_jd
        prev_lon = cur_lon

    return None


def _crossed(lon1: float, lon2: float, target: float) -> bool:
    """Check if target longitude was crossed going from lon1 to lon2."""
    if lon1 <= lon2:
        return lon1 <= target < lon2
    # Wrapped past 360°
    return target >= lon1 or target < lon2
