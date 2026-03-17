"""Upagraha (shadow planet) computation.

Upagrahas are mathematical points derived from planetary positions.
- Gulika/Mandi: derived from Saturn's lordship of time segments
- Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu: derived from Sun
"""

from __future__ import annotations

from jyotish.utils.constants import SIGNS, GULIKA_SLOT
from jyotish.utils.datetime_utils import (
    to_jd, compute_sunrise, compute_sunset, from_jd, parse_birth_datetime,
)
from jyotish.domain.models.chart import ChartData
from jyotish.domain.models.upagraha import UpagrahaPosition
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)

# Planet ruling each 1/8th of day (from sunrise), indexed by weekday (0=Sun)
# Each day starts with the day lord, then follows the sequence
DAY_HORA_SEQUENCE = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
UPAGRAHA_PLANET_ORDER = {
    0: ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"],      # Sunday
    1: ["Moon", "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury"],      # Monday
    2: ["Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter"],      # Tuesday
    3: ["Mercury", "Moon", "Saturn", "Jupiter", "Mars", "Sun", "Venus"],      # Wednesday
    4: ["Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon", "Saturn"],      # Thursday
    5: ["Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars", "Sun"],      # Friday
    6: ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"],      # Saturday
}


def compute_gulika_longitude(chart: ChartData) -> float:
    """Compute Gulika's sidereal longitude.

    Gulika is the Saturn-ruled segment of the day.
    Its longitude = the lagna rising at the start of Saturn's segment.
    """
    import swisseph as swe
    from jyotish.utils.datetime_utils import parse_birth_datetime

    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    jd = to_jd(birth_dt)

    try:
        sunrise_jd = compute_sunrise(jd, chart.latitude, chart.longitude)
        sunset_jd = compute_sunset(jd, chart.latitude, chart.longitude)
    except Exception:
        logger.warning("Could not compute sunrise/sunset for Gulika, using approximate")
        return 0.0

    daylight = sunset_jd - sunrise_jd
    segment = daylight / 8.0

    # Get weekday (0=Sun)
    day_dt = from_jd(sunrise_jd)
    py_weekday = day_dt.weekday()  # Mon=0..Sun=6
    weekday_map = {6: 0, 0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
    day_index = weekday_map[py_weekday]

    gulika_slot = GULIKA_SLOT[day_index]
    gulika_jd = sunrise_jd + (gulika_slot - 1) * segment

    # Compute lagna at that moment
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(gulika_jd)
    _, ascmc = swe.houses_ex(gulika_jd, chart.latitude, chart.longitude, b"W")
    lagna_tropical = ascmc[0]
    return (lagna_tropical - ayanamsha) % 360.0


def compute_sun_upagrahas(chart: ChartData) -> list[UpagrahaPosition]:
    """Compute Sun-derived upagrahas: Dhuma, Vyatipata, Parivesha, Indrachapa, Upaketu.

    Formulas (from BPHS):
    - Dhuma = Sun + 133°20'
    - Vyatipata = 360° - Dhuma
    - Parivesha = Vyatipata + 180°
    - Indrachapa = 360° - Parivesha
    - Upaketu = Indrachapa + 16°40'
    """
    sun_lon = chart.planets["Sun"].longitude
    lagna_sign = chart.lagna_sign_index

    dhuma = (sun_lon + 133.333) % 360.0
    vyatipata = (360.0 - dhuma) % 360.0
    parivesha = (vyatipata + 180.0) % 360.0
    indrachapa = (360.0 - parivesha) % 360.0
    upaketu = (indrachapa + 16.667) % 360.0

    def _make(name: str, name_hi: str, lon: float, source: str) -> UpagrahaPosition:
        sign_idx = int(lon / 30.0)
        deg = lon - sign_idx * 30.0
        house = ((sign_idx - lagna_sign) % 12) + 1
        return UpagrahaPosition(
            name=name, name_hi=name_hi,
            longitude=round(lon, 4), sign_index=sign_idx,
            sign=SIGNS[sign_idx], degree_in_sign=round(deg, 4),
            house=house, source_planet=source,
        )

    return [
        _make("Dhuma", "धूम", dhuma, "Sun"),
        _make("Vyatipata", "व्यतिपात", vyatipata, "Sun"),
        _make("Parivesha", "परिवेश", parivesha, "Sun"),
        _make("Indrachapa", "इन्द्रचाप", indrachapa, "Sun"),
        _make("Upaketu", "उपकेतु", upaketu, "Sun"),
    ]


def compute_all_upagrahas(chart: ChartData) -> list[UpagrahaPosition]:
    """Compute all upagrahas for a chart.

    Returns:
        List of UpagrahaPosition for Gulika/Mandi + Sun-derived upagrahas.
    """
    results = []

    # Gulika (Saturn-derived)
    try:
        gulika_lon = compute_gulika_longitude(chart)
        sign_idx = int(gulika_lon / 30.0)
        deg = gulika_lon - sign_idx * 30.0
        house = ((sign_idx - chart.lagna_sign_index) % 12) + 1
        results.append(UpagrahaPosition(
            name="Gulika", name_hi="गुलिक",
            longitude=round(gulika_lon, 4), sign_index=sign_idx,
            sign=SIGNS[sign_idx], degree_in_sign=round(deg, 4),
            house=house, source_planet="Saturn",
        ))
        # Mandi = same as Gulika in most systems
        results.append(UpagrahaPosition(
            name="Mandi", name_hi="मान्दि",
            longitude=round(gulika_lon, 4), sign_index=sign_idx,
            sign=SIGNS[sign_idx], degree_in_sign=round(deg, 4),
            house=house, source_planet="Saturn",
        ))
    except Exception as e:
        logger.warning("Could not compute Gulika/Mandi: %s", e)

    # Sun-derived upagrahas
    results.extend(compute_sun_upagrahas(chart))

    return results
