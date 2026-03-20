"""Bhrigu Bindu computation — midpoint of Rahu and Moon.

Bhrigu Bindu is one of the most sensitive points in Vedic predictive
astrology. When transit planets (especially Saturn, Jupiter, Rahu) cross
this point, major life events occur in the house area it occupies.

Primary formula (BPHS tradition):
    Bhrigu Bindu = (Rahu_longitude + Moon_longitude) / 2  (mod 360)

If the sum exceeds 360°, subtract 360°. This simple average is the most
widely used convention in Bhrigu Samhita and Jyotish texts.
"""

from __future__ import annotations

from daivai_engine.constants import (
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    SIGN_LORDS,
    SIGNS,
    SIGNS_EN,
)
from daivai_engine.models.bhrigu_bindu import BhriguBinduResult
from daivai_engine.models.chart import ChartData


# Width of each nakshatra in degrees (360 / 27)
_NAKSHATRA_WIDTH: float = 360.0 / 27.0


def _midpoint_longitude(lon_a: float, lon_b: float) -> float:
    """Compute Bhrigu Bindu longitude as the simple average of two longitudes.

    Formula: (lon_a + lon_b) / 2, taken mod 360.
    This follows the primary BPHS/Bhrigu Samhita convention.

    Args:
        lon_a: First longitude (0-360), typically Rahu.
        lon_b: Second longitude (0-360), typically Moon.

    Returns:
        Midpoint longitude in range [0, 360).
    """
    return ((lon_a + lon_b) / 2.0) % 360.0


def compute_bhrigu_bindu(chart: ChartData) -> BhriguBinduResult:
    """Compute the Bhrigu Bindu for a birth chart.

    Bhrigu Bindu = shorter-arc midpoint of Rahu and Moon longitudes.
    Determines the sign, house (whole-sign from Lagna), nakshatra, and lords.

    Args:
        chart: A fully computed birth chart with all planetary positions.

    Returns:
        BhriguBinduResult with full positional details of the Bhrigu Bindu.
    """
    rahu_lon = chart.planets["Rahu"].longitude
    moon_lon = chart.planets["Moon"].longitude

    bb_lon = _midpoint_longitude(rahu_lon, moon_lon)

    sign_index = int(bb_lon / 30.0)
    degree_in_sign = bb_lon - sign_index * 30.0

    # Whole-sign house from Lagna
    house = ((sign_index - chart.lagna_sign_index) % 12) + 1

    # Nakshatra
    nak_index = int(bb_lon / _NAKSHATRA_WIDTH)
    nak_index = min(nak_index, 26)  # guard against floating-point edge

    return BhriguBinduResult(
        longitude=bb_lon,
        sign_index=sign_index,
        sign=SIGNS[sign_index],
        sign_en=SIGNS_EN[sign_index],
        degree_in_sign=degree_in_sign,
        house=house,
        nakshatra_index=nak_index,
        nakshatra=NAKSHATRAS[nak_index],
        nakshatra_lord=NAKSHATRA_LORDS[nak_index],
        sign_lord=SIGN_LORDS[sign_index],
        rahu_longitude=rahu_lon,
        moon_longitude=moon_lon,
    )
