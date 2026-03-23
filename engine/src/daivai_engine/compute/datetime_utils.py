"""IST conversion, Julian Day helpers."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta, timezone

import pytz
import swisseph as swe


logger = logging.getLogger(__name__)

IST = timezone(timedelta(hours=5, minutes=30))


def to_jd(dt: datetime) -> float:
    """Convert a datetime to Julian Day (UT)."""
    utc_dt = dt.astimezone(UTC)
    hour_frac = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour_frac)
    return float(jd)


def from_jd(jd: float) -> datetime:
    """Convert Julian Day to UTC datetime."""
    year, month, day, hour_frac = swe.revjul(jd)
    hours = int(hour_frac)
    remainder = (hour_frac - hours) * 60
    minutes = int(remainder)
    seconds = int((remainder - minutes) * 60)
    return datetime(year, month, day, hours, minutes, seconds, tzinfo=UTC)


def parse_birth_datetime(
    dob: str,
    tob: str,
    tz_name: str = "Asia/Kolkata",
) -> datetime:
    """Parse DOB (DD/MM/YYYY) and TOB (HH:MM or HH:MM:SS) into a timezone-aware datetime.

    Handles DST edge cases automatically:
    - Ambiguous times (DST fall-back, clocks repeat an hour): standard time is chosen.
    - Non-existent times (DST spring-forward, clocks skip an hour): the next valid
      local time is returned and a warning is logged.

    Args:
        dob: Date of birth as DD/MM/YYYY.
        tob: Time of birth as HH:MM or HH:MM:SS.
        tz_name: IANA timezone name (e.g. "Asia/Kolkata", "America/New_York").

    Returns:
        Timezone-aware datetime in the given timezone.
    """
    day, month, year = dob.split("/")
    parts = tob.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    second = int(parts[2]) if len(parts) > 2 else 0

    tz = pytz.timezone(tz_name)
    naive = datetime(int(year), int(month), int(day), hour, minute, second)

    try:
        # is_dst=None raises on ambiguity; we catch and resolve below.
        return tz.localize(naive, is_dst=None)
    except pytz.exceptions.AmbiguousTimeError:
        # DST fall-back: this local time exists twice (standard + DST).
        # Choose the standard-time (non-DST) interpretation.
        logger.warning(
            "Birth time %s %s in %s is DST-ambiguous — using standard time (non-DST).",
            dob,
            tob,
            tz_name,
        )
        return tz.localize(naive, is_dst=False)
    except pytz.exceptions.NonExistentTimeError:
        # DST spring-forward: this local time does not exist.
        # Shift forward by 1 hour (standard DST gap) and warn.
        shifted = naive + timedelta(hours=1)
        logger.warning(
            "Birth time %s %s in %s does not exist (DST spring-forward) — using %s instead.",
            dob,
            tob,
            tz_name,
            shifted.strftime("%H:%M:%S"),
        )
        return tz.localize(shifted, is_dst=True)


def now_ist() -> datetime:
    """Current time in IST."""
    return datetime.now(IST)


def compute_sunrise(jd: float, lat: float, lon: float) -> float:
    """Compute sunrise Julian Day for a given date and location."""
    # swe.rise_trans(tjdut, body, rsmi, geopos, atpress, attemp)
    rsmi = swe.CALC_RISE | swe.BIT_DISC_CENTER
    result = swe.rise_trans(
        jd - 0.5,  # Start searching from previous noon
        swe.SUN,
        rsmi,
        (lon, lat, 0),  # geopos: lon, lat, altitude
        1013.25,  # atmospheric pressure
        15.0,  # atmospheric temperature
    )
    return float(result[1][0])


def compute_sunset(jd: float, lat: float, lon: float) -> float:
    """Compute sunset Julian Day for a given date and location."""
    rsmi = swe.CALC_SET | swe.BIT_DISC_CENTER
    result = swe.rise_trans(
        jd - 0.5,
        swe.SUN,
        rsmi,
        (lon, lat, 0),
        1013.25,
        15.0,
    )
    return float(result[1][0])
