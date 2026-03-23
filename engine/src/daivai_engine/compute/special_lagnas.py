"""Special Lagnas — Hora, Bhava, Ghatika, Vighati, Pranapada, Indu, Shree, Varnada.

All time-based lagnas (Hora/Bhava/Ghatika/Vighati) are computed from the
time elapsed since sunrise. Indu, Shree, and Varnada Lagnas are computed
from planetary longitudes and sign parity rules.

Sources: BPHS Chapter 5; Uttarakalamrita; Phala Deepika; Jaimini Sutras Ch.1.
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
    """A special ascendant point (Hora/Bhava/Ghatika/Vighati/Pranapada/Indu/Shree/Varnada)."""

    name: str
    longitude: float  # Sidereal longitude 0-360
    sign_index: int
    sign_hi: str
    sign_en: str
    degree_in_sign: float


def compute_special_lagnas(chart: ChartData) -> dict[str, SpecialLagna]:
    """Compute all eight special lagnas.

    Time-based lagnas require sunrise time at birth location.
    1 ghatika = 24 minutes = 1/60th of a day.
    1 vighati = 24 seconds = 1/60th of a ghatika.

    Args:
        chart: Computed birth chart (needs julian_day, lat, lon).

    Returns:
        Dict with keys: 'hora', 'bhava', 'ghatika', 'vighati',
        'pranapada', 'indu', 'shree', 'varnada'.
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
        "varnada": compute_varnada_lagna(chart, hora_lon),
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


def compute_varnada_lagna(chart: ChartData, hora_lon: float) -> SpecialLagna:
    """Compute Varnada Lagna — Jaimini career/profession indicator.

    The Varnada Lagna indicates the native's varna (social role/profession)
    and overall standing in society. It is computed from the relationship
    between the Lagna sign and the Hora Lagna sign using odd/even parity.

    Algorithm (Jaimini Sutras Ch.1, Sanjay Rath tradition):
        1. Let L = Lagna sign (0-indexed), H = Hora Lagna sign (0-indexed).
        2. If Lagna is in an ODD sign (Aries=0, Gemini=2, ...):
           a. Count from Aries (0) to L → forward_L = L + 1
           b. If Hora is ALSO odd: forward_H = H + 1
              Else (Hora even): forward_H = (12 - H)
           c. Sum = forward_L + forward_H
        3. If Lagna is in an EVEN sign (Taurus=1, Cancer=3, ...):
           a. Count from Pisces (11) backward to L → forward_L = (12 - L)
           b. If Hora is ALSO even: forward_H = (12 - H)
              Else (Hora odd): forward_H = H + 1
           c. Sum = forward_L + forward_H
        4. Varnada sign = (Sum - 1) mod 12 if Lagna odd, counted from Aries.
           Varnada sign = (12 - ((Sum - 1) mod 12)) mod 12 if Lagna even,
           counted backward from Pisces.

    Args:
        chart: Computed birth chart.
        hora_lon: Hora Lagna longitude (pre-computed).

    Returns:
        SpecialLagna for the Varnada Lagna point.
    """
    lagna_sign = chart.lagna_sign_index
    hora_sign = int(hora_lon / DEGREES_PER_SIGN) % 12

    lagna_odd = lagna_sign % 2 == 0  # 0=Aries(odd), 1=Taurus(even), etc.
    hora_odd = hora_sign % 2 == 0

    if lagna_odd:
        forward_l = lagna_sign + 1
        forward_h = (hora_sign + 1) if hora_odd else (12 - hora_sign)
        total = forward_l + forward_h
        varnada_sign = (total - 1) % 12
    else:
        forward_l = 12 - lagna_sign
        forward_h = (12 - hora_sign) if not hora_odd else (hora_sign + 1)
        total = forward_l + forward_h
        varnada_sign = (12 - ((total - 1) % 12)) % 12

    varnada_lon = float(varnada_sign * DEGREES_PER_SIGN)
    return _make_lagna("Varnada Lagna", varnada_lon)


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
