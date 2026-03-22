"""Sahams — 16 classical Tajaka Arabic Parts (sensitive points).

The 16 Tajaka Sahams come from the Persian-Arabic annual astrology tradition
integrated into Vedic jyotish via Tajaka Neelakanthi. Each Saham is a
sensitive zodiac point computed from the Lagna and two planets.

Day formula:  Saham = (Lagna + A - B) mod 360
Night formula: Saham = (Lagna + B - A) mod 360

Day/night: Sun above horizon (houses 7-12) = daytime birth.

Sources: Tajaka Neelakanthi (Nilakantha), Phala Deepika Ch. 25,
         Dr. B.V. Raman "Varshphal" Ch. 4.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    NAKSHATRA_SPAN_DEG,
    NAKSHATRAS,
    SIGNS_EN,
    SIGNS_HI,
)
from daivai_engine.models.chart import ChartData


class TajakaSaham(BaseModel):
    """A single Tajaka Saham (sensitive point / Arabic Part).

    Each Saham marks a zodiac degree that is sensitive to the signification
    described by its name (e.g., fame, wealth, education).
    """

    model_config = ConfigDict(frozen=True)

    name: str  # English name (e.g., "Yasha Saham")
    name_hi: str  # Sanskrit/Hindi name
    signification: str  # What this Saham indicates
    formula_day: str  # Textual formula used for day births
    longitude: float  # Sidereal, 0-360°
    sign_index: int  # 0-11
    sign_en: str
    sign_hi: str
    degree_in_sign: float
    nakshatra: str


class TajakaSahamsResult(BaseModel):
    """Complete set of 16 Tajaka Sahams for a chart."""

    model_config = ConfigDict(frozen=True)

    is_day_birth: bool
    sahams: list[TajakaSaham]  # Exactly 16 classical + 1 additional


def compute_tajaka_sahams(chart: ChartData) -> TajakaSahamsResult:
    """Compute the 16 classical Tajaka Sahams from Tajaka Neelakanthi.

    Day birth: Sun in houses 7-12 (above horizon in traditional reckoning).
    Night birth: Sun in houses 1-6 (below horizon).

    Args:
        chart: Natal or annual birth chart.

    Returns:
        TajakaSahamsResult with 16 sahams.
    """
    lagna = chart.lagna_longitude
    sun = chart.planets["Sun"].longitude
    moon = chart.planets["Moon"].longitude
    mars = chart.planets["Mars"].longitude
    mercury = chart.planets["Mercury"].longitude
    jupiter = chart.planets["Jupiter"].longitude
    venus = chart.planets["Venus"].longitude
    saturn = chart.planets["Saturn"].longitude

    is_day = chart.planets["Sun"].house >= 7

    def _d(a: float, b: float) -> float:
        """Day formula: (lagna + A - B) mod 360. Night: (lagna + B - A) mod 360."""
        if is_day:
            return (lagna + a - b) % FULL_CIRCLE_DEG
        return (lagna + b - a) % FULL_CIRCLE_DEG

    raw_sahams: list[tuple[str, str, str, str, float]] = [
        # (name_en, name_hi, signification, formula_day, longitude)
        (
            "Punya Saham",
            "पुण्य सहम",
            "Fortune, merit, and accumulated virtue",
            "Lagna + Moon - Sun",
            _d(moon, sun),
        ),
        (
            "Vidya Saham",
            "विद्या सहम",
            "Education, learning, and intellectual pursuits",
            "Lagna + Jupiter - Mercury",
            _d(jupiter, mercury),
        ),
        (
            "Yasha Saham",
            "यश सहम",
            "Fame, honour, recognition, and social standing",
            "Lagna + Jupiter - Sun",
            _d(jupiter, sun),
        ),
        (
            "Mitra Saham",
            "मित्र सहम",
            "Friends, allies, helpful associates",
            "Lagna + Moon - Mercury",
            _d(moon, mercury),
        ),
        (
            "Mahatmya Saham",
            "महात्म्य सहम",
            "Greatness, dignity, and noble qualities",
            "Lagna + Mars - Moon",
            _d(mars, moon),
        ),
        (
            "Asha Saham",
            "आशा सहम",
            "Hope, desire, wishes, and aspirations",
            "Lagna + Saturn - Jupiter",
            _d(saturn, jupiter),
        ),
        (
            "Samartha Saham",
            "समर्थ सहम",
            "Capability, strength, and competence",
            "Lagna + Mars - Saturn",
            _d(mars, saturn),
        ),
        (
            "Bhratri Saham",
            "भ्रातृ सहम",
            "Siblings, co-borns, and cousins",
            "Lagna + Jupiter - Saturn",
            _d(jupiter, saturn),
        ),
        (
            "Gaurava Saham",
            "गौरव सहम",
            "Respect, reverence, and honour from others",
            "Lagna + Moon - Jupiter",
            _d(moon, jupiter),
        ),
        (
            "Pitri Saham",
            "पितृ सहम",
            "Father, authority figures, and past karma",
            "Lagna + Sun - Saturn",
            _d(sun, saturn),
        ),
        (
            "Rajya Saham",
            "राज्य सहम",
            "Career, status, government, and public life",
            "Lagna + Saturn - Sun",
            _d(saturn, sun),
        ),
        (
            "Matri Saham",
            "मातृ सहम",
            "Mother, nurturing, home, and emotional support",
            "Lagna + Moon - Venus",
            _d(moon, venus),
        ),
        (
            "Putra Saham",
            "पुत्र सहम",
            "Children, creativity, and speculative gains",
            "Lagna + Jupiter - Moon",
            _d(jupiter, moon),
        ),
        (
            "Jeeva Saham",
            "जीव सहम",
            "Life force, vitality, and the soul's journey",
            "Lagna + Saturn - Moon",
            _d(saturn, moon),
        ),
        (
            "Karman Saham",
            "कर्मन सहम",
            "Career deeds, professional actions, and duty",
            "Lagna + Mercury - Sun",
            _d(mercury, sun),
        ),
        (
            "Kali Saham",
            "काली सहम",
            "Obstacles, destruction, and dark forces",
            "Lagna + Mars - Jupiter",
            _d(mars, jupiter),
        ),
        (
            "Pasha Saham",
            "पाश सहम",
            "Bondage, attachments, and restrictive karma",
            "Lagna + Mercury - Saturn",
            _d(mercury, saturn),
        ),
    ]

    built: list[TajakaSaham] = [_build(t) for t in raw_sahams]
    return TajakaSahamsResult(is_day_birth=is_day, sahams=built)


def get_saham_by_name(result: TajakaSahamsResult, name: str) -> TajakaSaham | None:
    """Retrieve a single Saham from a result set by name.

    Args:
        result: Computed TajakaSahamsResult.
        name: Saham name (e.g., "Yasha Saham").

    Returns:
        TajakaSaham if found, else None.
    """
    for s in result.sahams:
        if s.name == name:
            return s
    return None


# ── Private helpers ────────────────────────────────────────────────────────────


def _build(
    record: tuple[str, str, str, str, float],
) -> TajakaSaham:
    """Construct a TajakaSaham from a raw (name_en, name_hi, sig, formula, lon) tuple."""
    name_en, name_hi, sig, formula, longitude = record
    sign_idx = int(longitude / DEGREES_PER_SIGN) % 12
    deg = longitude - sign_idx * DEGREES_PER_SIGN
    nak_idx = min(int(longitude / NAKSHATRA_SPAN_DEG), 26)
    return TajakaSaham(
        name=name_en,
        name_hi=name_hi,
        signification=sig,
        formula_day=formula,
        longitude=round(longitude, 4),
        sign_index=sign_idx,
        sign_en=SIGNS_EN[sign_idx],
        sign_hi=SIGNS_HI[sign_idx],
        degree_in_sign=round(deg, 4),
        nakshatra=NAKSHATRAS[nak_idx],
    )
