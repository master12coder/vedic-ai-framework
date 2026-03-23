"""Special Lagnas — Hora, Bhava, Ghatika, Vighati, Pranapada, Indu, Shree.

All time-based lagnas (Hora/Bhava/Ghatika/Vighati) are computed from the
time elapsed since sunrise. Indu and Shree Lagnas are computed from
planetary longitudes directly.

Sources: BPHS Chapter 5; Uttarakalamrita; Phala Deepika.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.compute.datetime_utils import compute_sunrise
from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    SIGN_LORDS,
    SIGNS_EN,
    SIGNS_HI,
)
from daivai_engine.models.chart import ChartData


# Kaksha (weight) values used for Indu Lagna — Uttarakalamrita tradition.
# Rahu and Ketu have no Kaksha (nodes are excluded from 9th lord reckoning).
_PLANET_KAKSHA: dict[str, int] = {
    "Sun": 30,
    "Moon": 16,
    "Mars": 6,
    "Mercury": 8,
    "Jupiter": 10,
    "Venus": 12,
    "Saturn": 1,
    "Rahu": 0,
    "Ketu": 0,
}


class SpecialLagna(BaseModel):
    """A special ascendant point (Hora/Bhava/Ghatika/Vighati/Pranapada/Indu/Shree)."""

    name: str
    longitude: float  # Sidereal longitude 0-360
    sign_index: int
    sign_hi: str
    sign_en: str
    degree_in_sign: float


def compute_special_lagnas(chart: ChartData) -> dict[str, SpecialLagna]:
    """Compute all seven special lagnas.

    Time-based lagnas require sunrise time at birth location.
    1 ghatika = 24 minutes = 1/60th of a day.
    1 vighati = 24 seconds = 1/60th of a ghatika.

    Args:
        chart: Computed birth chart (needs julian_day, lat, lon).

    Returns:
        Dict with keys: 'hora', 'bhava', 'ghatika', 'vighati',
        'pranapada', 'indu', 'shree'.
    """
    birth_jd = chart.julian_day
    sunrise_jd = compute_sunrise(birth_jd, chart.latitude, chart.longitude)

    # Time elapsed from sunrise in ghatikas (1 ghatika = 24 min = 1/60 day)
    elapsed_days = birth_jd - sunrise_jd
    if elapsed_days < 0:
        # Born before sunrise → use previous day's sunrise
        elapsed_days += 1.0
    ghatikas = elapsed_days * 60.0  # 60 ghatikas per day
    vighatikas = ghatikas * 60.0  # 60 vighatikas per ghatika

    sun_lon = chart.planets["Sun"].longitude
    lagna_lon = chart.lagna_longitude

    # HORA LAGNA (BPHS Ch.5): advances 1 sign per 2.5 ghatikas = 12 deg/ghatika
    # Hora Lagna = Sun longitude + (ghatikas x 12 deg)
    hora_lon = (sun_lon + ghatikas * 12.0) % FULL_CIRCLE_DEG

    # BHAVA LAGNA (BPHS Ch.5): advances 1 sign per 5 ghatikas
    # Bhava Lagna = Lagna + (ghatikas x 6 deg)
    bhava_lon = (lagna_lon + ghatikas * 6.0) % FULL_CIRCLE_DEG

    # GHATIKA LAGNA (BPHS Ch.5): advances 1 sign per ghatika (24 min)
    # Ghatika Lagna = Lagna + (ghatikas x 30 deg)
    ghatika_lon = (lagna_lon + ghatikas * DEGREES_PER_SIGN) % FULL_CIRCLE_DEG

    # VIGHATI LAGNA: advances 1 sign per vighati (24 seconds) -- sub-ghatika precision
    # Vighati Lagna = Lagna + (vighatikas x 30 deg)
    vighati_lon = (lagna_lon + vighatikas * DEGREES_PER_SIGN) % FULL_CIRCLE_DEG

    # PRANAPADA (vital breath point) -- Uttarakalamrita tradition:
    # Moon's angular distance from Sun x 5, added to Lagna
    moon_lon = chart.planets["Moon"].longitude
    moon_from_sun = (moon_lon - sun_lon) % FULL_CIRCLE_DEG
    pranapada_lon = (lagna_lon + 5.0 * moon_from_sun) % FULL_CIRCLE_DEG

    return {
        "hora": _make_lagna("Hora Lagna", hora_lon),
        "bhava": _make_lagna("Bhava Lagna", bhava_lon),
        "ghatika": _make_lagna("Ghatika Lagna", ghatika_lon),
        "vighati": _make_lagna("Vighati Lagna", vighati_lon),
        "pranapada": _make_lagna("Pranapada", pranapada_lon),
        "indu": compute_indu_lagna(chart),
        "shree": compute_shree_lagna(chart),
    }


def compute_indu_lagna(chart: ChartData) -> SpecialLagna:
    """Compute Indu Lagna — wealth-indicator ascendant (Uttarakalamrita).

    Algorithm:
        1. Find 9th lord from Lagna and get its Kaksha value.
        2. Find 9th lord from Moon's sign and get its Kaksha value.
        3. Sum the two Kaksha values. Reduce mod 12 (0 → 12).
        4. Count that many signs from Moon's sign (Moon = 1st). That sign is Indu Lagna.

    Kaksha values: Sun=30, Moon=16, Mars=6, Mercury=8, Jupiter=10, Venus=12, Saturn=1.
    Planets aspecting Indu Lagna indicate sources of wealth.

    Args:
        chart: Computed birth chart.

    Returns:
        SpecialLagna positioned at the start (0 deg) of the Indu Lagna sign.
    """
    # 9th lord from Lagna
    lagna_9th_sign = (chart.lagna_sign_index + 8) % 12
    lagna_9th_lord = SIGN_LORDS[lagna_9th_sign]
    kaksha_lagna = _PLANET_KAKSHA[lagna_9th_lord]

    # 9th lord from Moon's sign
    moon_sign = chart.planets["Moon"].sign_index
    moon_9th_sign = (moon_sign + 8) % 12
    moon_9th_lord = SIGN_LORDS[moon_9th_sign]
    kaksha_moon = _PLANET_KAKSHA[moon_9th_lord]

    total = kaksha_lagna + kaksha_moon
    n = total % 12
    if n == 0:
        n = 12

    # Count n signs from Moon's sign (Moon's sign = count 1)
    indu_sign = (moon_sign + n - 1) % 12
    indu_lon = float(indu_sign * DEGREES_PER_SIGN)  # convention: 0 deg of that sign
    return _make_lagna("Indu Lagna", indu_lon)


def compute_shree_lagna(chart: ChartData) -> SpecialLagna:
    """Compute Shree Lagna — prosperity ascendant for Lakshmi's grace.

    Formula (Phala Deepika / Uttarakalamrita):
        Day birth  (Sun above horizon, house >= 7): Lagna + Moon - Sun
        Night birth (Sun below horizon, house < 7): Lagna + Sun  - Moon

    Args:
        chart: Computed birth chart.

    Returns:
        SpecialLagna for the Shree Lagna point.
    """
    lagna_lon = chart.lagna_longitude
    sun_lon = chart.planets["Sun"].longitude
    moon_lon = chart.planets["Moon"].longitude

    # Sun in houses 7-12 = above horizon = daytime birth
    is_day = chart.planets["Sun"].house >= 7
    if is_day:
        shree_lon = (lagna_lon + moon_lon - sun_lon) % FULL_CIRCLE_DEG
    else:
        shree_lon = (lagna_lon + sun_lon - moon_lon) % FULL_CIRCLE_DEG

    return _make_lagna("Shree Lagna", shree_lon)


def _make_lagna(name: str, longitude: float) -> SpecialLagna:
    """Build a SpecialLagna from a longitude."""
    sign_idx = int(longitude / DEGREES_PER_SIGN) % 12
    deg = longitude - sign_idx * DEGREES_PER_SIGN
    return SpecialLagna(
        name=name,
        longitude=round(longitude, 4),
        sign_index=sign_idx,
        sign_hi=SIGNS_HI[sign_idx],
        sign_en=SIGNS_EN[sign_idx],
        degree_in_sign=round(deg, 4),
    )
