"""Saham Points (Sensitive Points / Arabic Parts adapted for Vedic).

Traditional Tajaka/Varshphal sahams computed from lagna, planets,
and house cusps. Used primarily in annual chart interpretation.

Sources: Tajaka Neelakanthi, Uttarakalamrita, Phala Deepika.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    NAKSHATRA_SPAN_DEG,
    NAKSHATRAS,
    SIGN_LORDS,
    SIGNS_EN,
    SIGNS_HI,
)
from daivai_engine.models.chart import ChartData


class SahamPoint(BaseModel):
    """A single sensitive point."""

    name: str  # Punya, Vivaha, Putra, etc.
    name_hi: str
    longitude: float  # Sidereal, 0-360
    sign_index: int
    sign_hi: str
    sign_en: str
    degree_in_sign: float
    nakshatra: str


def compute_sahams(chart: ChartData) -> list[SahamPoint]:
    """Compute 29 traditional Saham (sensitive) points.

    Formulas from Tajaka Neelakanthi, Uttarakalamrita, and Phala Deepika.
    Day/night determined by Sun's house: Sun in houses 7-12 = daytime birth.

    Args:
        chart: Computed birth chart.

    Returns:
        List of 29 SahamPoint objects.
    """
    lagna_lon = chart.lagna_longitude
    lagna_idx = chart.lagna_sign_index
    sun = chart.planets["Sun"].longitude
    moon = chart.planets["Moon"].longitude
    mars = chart.planets["Mars"].longitude
    mercury = chart.planets["Mercury"].longitude
    jupiter = chart.planets["Jupiter"].longitude
    venus = chart.planets["Venus"].longitude
    saturn = chart.planets["Saturn"].longitude

    # Whole-sign house cusps (start-of-sign longitude)
    def _cusp(n: int) -> float:
        """Return the longitude of the nth house cusp (whole sign)."""
        return ((lagna_idx + n - 1) % 12) * DEGREES_PER_SIGN

    cusp_2 = _cusp(2)
    cusp_4 = _cusp(4)
    cusp_5 = _cusp(5)
    cusp_6 = _cusp(6)
    cusp_7 = _cusp(7)
    cusp_8 = _cusp(8)
    cusp_9 = _cusp(9)
    cusp_10 = _cusp(10)
    cusp_11 = _cusp(11)
    cusp_12 = _cusp(12)

    def _lord_lon(house_n: int) -> float:
        """Return the longitude of the lord of house N (whole sign)."""
        house_sign = (lagna_idx + house_n - 1) % 12
        lord_name = SIGN_LORDS[house_sign]
        return chart.planets[lord_name].longitude

    lord_2 = _lord_lon(2)
    lord_6 = _lord_lon(6)
    lord_9 = _lord_lon(9)
    lord_11 = _lord_lon(11)
    lord_12 = _lord_lon(12)

    # Moon's lord (lord of sign Moon occupies)
    moon_lord = SIGN_LORDS[chart.planets["Moon"].sign_index]
    moon_lord_cusp = chart.planets[moon_lord].sign_index * DEGREES_PER_SIGN

    # Day/night: Sun in houses 7-12 = daytime birth (above horizon)
    is_day = chart.planets["Sun"].house >= 7

    # ── Original 6 sahams ──────────────────────────────────────────────────

    punya_lon = (
        (lagna_lon + moon - sun) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + sun - moon) % FULL_CIRCLE_DEG
    )

    # ── Health & Body ──────────────────────────────────────────────────────

    roga_lon = (
        (lagna_lon + mars - saturn) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + saturn - mars) % FULL_CIRCLE_DEG
    )

    # ── Relationships ──────────────────────────────────────────────────────

    matri_lon = (
        (lagna_lon + moon - venus) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + venus - moon) % FULL_CIRCLE_DEG
    )

    pitri_lon = (
        (lagna_lon + sun - saturn) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + saturn - sun) % FULL_CIRCLE_DEG
    )

    bhratri_lon = (
        (lagna_lon + jupiter - saturn) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + saturn - jupiter) % FULL_CIRCLE_DEG
    )

    # ── Wealth & Career ────────────────────────────────────────────────────

    rajya_lon = (
        (lagna_lon + saturn - sun) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + sun - saturn) % FULL_CIRCLE_DEG
    )

    vyapara_lon = (
        (lagna_lon + mars - saturn) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + saturn - mars) % FULL_CIRCLE_DEG
    )

    shatru_lon = (
        (lagna_lon + mars - saturn) % FULL_CIRCLE_DEG
        if is_day
        else (lagna_lon + saturn - mars) % FULL_CIRCLE_DEG
    )

    sahams = [
        # ── Original 6 ────────────────────────────────────────────────────
        _make("Punya Saham", "पुण्य सहम", punya_lon),
        _make(
            "Vivaha Saham",
            "विवाह सहम",
            (lagna_lon + venus - cusp_7) % FULL_CIRCLE_DEG
            if is_day
            else (lagna_lon + cusp_7 - venus) % FULL_CIRCLE_DEG,
        ),
        _make("Putra Saham", "पुत्र सहम", (lagna_lon + jupiter - cusp_5) % FULL_CIRCLE_DEG),
        _make("Karma Saham", "कर्म सहम", (lagna_lon + saturn - cusp_10) % FULL_CIRCLE_DEG),
        _make("Vidya Saham", "विद्या सहम", (lagna_lon + mercury - cusp_5) % FULL_CIRCLE_DEG),
        _make("Mrityu Saham", "मृत्यु सहम", (lagna_lon + cusp_8 - moon) % FULL_CIRCLE_DEG),
        # ── Health & Body ─────────────────────────────────────────────────
        _make("Roga Saham", "रोग सहम", roga_lon),
        _make("Sharira Saham", "शरीर सहम", (lagna_lon + moon_lord_cusp - moon) % FULL_CIRCLE_DEG),
        # ── Relationships ─────────────────────────────────────────────────
        _make("Bandhu Saham", "बन्धु सहम", (lagna_lon + moon - mercury) % FULL_CIRCLE_DEG),
        _make("Matri Saham", "मातृ सहम", matri_lon),
        _make("Pitri Saham", "पितृ सहम", pitri_lon),
        _make("Bhratri Saham", "भ्रातृ सहम", bhratri_lon),
        # ── Wealth & Career ───────────────────────────────────────────────
        _make("Rajya Saham", "राज्य सहम", rajya_lon),
        _make("Dhana Saham", "धन सहम", (lagna_lon + moon - jupiter) % FULL_CIRCLE_DEG),
        _make("Vyapara Saham", "व्यापार सहम", vyapara_lon),
        _make("Labha Saham", "लाभ सहम", (lagna_lon + cusp_11 - lord_11) % FULL_CIRCLE_DEG),
        # ── Spiritual ─────────────────────────────────────────────────────
        _make("Dharma Saham", "धर्म सहम", (lagna_lon + cusp_9 - lord_9) % FULL_CIRCLE_DEG),
        _make("Guru Saham", "गुरु सहम", (lagna_lon + jupiter - sun) % FULL_CIRCLE_DEG),
        _make("Mantra Saham", "मन्त्र सहम", (lagna_lon + moon - jupiter) % FULL_CIRCLE_DEG),
        # ── Events ────────────────────────────────────────────────────────
        _make("Yatra Saham", "यात्रा सहम", (lagna_lon + cusp_9 - lord_9) % FULL_CIRCLE_DEG),
        _make("Vitta Saham", "वित्त सहम", (lagna_lon + cusp_2 - lord_2) % FULL_CIRCLE_DEG),
        _make("Paradesa Saham", "परदेश सहम", (lagna_lon + cusp_12 - lord_12) % FULL_CIRCLE_DEG),
        _make("Santana Saham", "सन्तान सहम", (lagna_lon + jupiter - moon) % FULL_CIRCLE_DEG),
        # ── Danger ────────────────────────────────────────────────────────
        _make("Apamrityu Saham", "अपमृत्यु सहम", (lagna_lon + cusp_8 - mars) % FULL_CIRCLE_DEG),
        _make("Kali Saham", "काली सहम", (lagna_lon + mars - jupiter) % FULL_CIRCLE_DEG),
        _make("Rog Saham", "रोग सहम (जीर्ण)", (lagna_lon + cusp_6 - lord_6) % FULL_CIRCLE_DEG),
        # ── Additional classical ───────────────────────────────────────────
        _make("Jalapatana Saham", "जलपतन सहम", (lagna_lon + cusp_4 - moon) % FULL_CIRCLE_DEG),
        _make("Shatru Saham", "शत्रु सहम", shatru_lon),
        _make("Gajakesari Saham", "गजकेसरी सहम", (lagna_lon + jupiter - moon) % FULL_CIRCLE_DEG),
    ]
    return sahams


def _make(name: str, name_hi: str, longitude: float) -> SahamPoint:
    """Build a SahamPoint from longitude."""
    sign_idx = int(longitude / DEGREES_PER_SIGN) % 12
    deg = longitude - sign_idx * DEGREES_PER_SIGN
    nak_idx = int(longitude / NAKSHATRA_SPAN_DEG)
    if nak_idx >= 27:
        nak_idx = 26
    return SahamPoint(
        name=name,
        name_hi=name_hi,
        longitude=round(longitude, 4),
        sign_index=sign_idx,
        sign_hi=SIGNS_HI[sign_idx],
        sign_en=SIGNS_EN[sign_idx],
        degree_in_sign=round(deg, 4),
        nakshatra=NAKSHATRAS[nak_idx],
    )
