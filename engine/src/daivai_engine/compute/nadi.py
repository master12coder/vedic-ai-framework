"""Nadi Amsha and Nadi Astrology Foundation.

Two complementary Nadi systems:

1. NAKSHATRA NADI (Gross level):
   Each of the 27 nakshatras belongs to one of three Nadis — Aadi (Pingala),
   Madhya (Sushumna), or Antya (Ida) — following a repeating 3-nakshatra
   pattern. Used in Koota matching (Nadi Koota = 8 points).

2. NADI AMSHA (Fine level):
   Each sign (30°) is divided into 150 Nadi Amshas of 12' (0.2°) each.
   These give extremely precise planet placement analysis. The 150 amshas
   cycle through the three Nadis in groups of 50:
     Amshas   1-50: Pingala (solar, Agni, right channel)
     Amshas  51-100: Ida (lunar, Soma, left channel)
     Amshas 101-150: Sushumna (central, both channels)

   Source: Nadi Grantha tradition; also used in Tamil Nadi palm-leaf readings.

3. NADI CLASSIFICATION RULE:
   Planet in Pingala Nadi → active, extrovert, solar energy dominant
   Planet in Ida Nadi → receptive, introvert, lunar energy dominant
   Planet in Sushumna Nadi → balanced, spiritual, both channels open

Source: Sarvartha Chintamani (Nadi Koota), various Nadi Jyotish texts,
        KN Rao commentary on Nadi system.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.constants import SIGNS, SIGNS_EN
from daivai_engine.models.chart import ChartData


# Nakshatra Nadi assignment — repeating pattern: Aadi, Madhya, Antya
# Index 0=Ashwini, 1=Bharani, ... 26=Revati
# Pattern repeats in groups of 3 nakshatras
_NAKSHATRA_NADI_CYCLE = ["aadi", "madhya", "antya"]

# Sanskrit names for the three Nadis
_NADI_NAMES: dict[str, str] = {
    "aadi": "Aadi (Pingala)",
    "madhya": "Madhya (Sushumna)",
    "antya": "Antya (Ida)",
}

_NADI_NAMES_HI: dict[str, str] = {
    "aadi": "आदि (पिंगला)",
    "madhya": "मध्य (सुषुम्ना)",
    "antya": "अंत्य (इड़ा)",
}

# Characteristics of each Nadi
_NADI_NATURE: dict[str, str] = {
    "aadi": "Solar/Pingala channel — active, masculine, fire energy. Planet here acts with vigour.",
    "madhya": "Sushumna channel — balanced, neutral, spiritual energy. Planet here acts with equanimity.",
    "antya": "Lunar/Ida channel — receptive, feminine, water energy. Planet here acts with sensitivity.",
}

# Nadi Amsha size in degrees
_NADI_AMSHA_SIZE: float = 0.2  # 12' = 0.2°
_NADI_AMSHAS_PER_SIGN: int = 150

# Nadi Amsha cycle within a sign: 1-50 Pingala, 51-100 Ida, 101-150 Sushumna
_AMSHA_NADI_GROUPS: list[tuple[int, int, str]] = [
    (1, 50, "pingala"),
    (51, 100, "ida"),
    (101, 150, "sushumna"),
]


class NadiAmshaPosition(BaseModel):
    """A planet's position in the Nadi Amsha system (fine-grained)."""

    model_config = ConfigDict(frozen=True)

    planet: str
    longitude: float = Field(ge=0, lt=360)
    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    degree_in_sign: float
    nadi_amsha_number: int = Field(ge=1, le=150)  # 1-150 within the sign
    nadi_amsha_start: float  # Start degree of this Nadi Amsha within sign
    nadi_amsha_end: float  # End degree of this Nadi Amsha within sign
    nadi: str  # pingala / ida / sushumna
    nadi_name: str  # Full name with Sanskrit


class NakshatraNadiResult(BaseModel):
    """A planet's Nadi classification at the nakshatra level (gross)."""

    model_config = ConfigDict(frozen=True)

    planet: str
    nakshatra: str
    nakshatra_index: int = Field(ge=0, le=26)
    nadi: str  # aadi / madhya / antya
    nadi_name: str  # "Aadi (Pingala)" etc.
    nadi_hi: str
    nature: str  # Short description of Nadi energy


class NadiAnalysisResult(BaseModel):
    """Complete Nadi analysis for all planets in a chart."""

    model_config = ConfigDict(frozen=True)

    nakshatra_nadis: list[NakshatraNadiResult]
    nadi_amshas: list[NadiAmshaPosition]
    dominant_nadi: str  # Which Nadi has the most planets
    nadi_distribution: dict[str, int]  # Count of planets per Nadi


def compute_nakshatra_nadi(chart: ChartData) -> list[NakshatraNadiResult]:
    """Compute Nadi classification for each planet at the nakshatra level.

    The 27 nakshatras cycle through Aadi (Pingala), Madhya (Sushumna),
    and Antya (Ida) Nadis in order. This is the standard Nadi Koota
    classification used in marriage compatibility analysis.

    Args:
        chart: Natal birth chart.

    Returns:
        List of NakshatraNadiResult for each of the 7 classical planets.
    """
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results: list[NakshatraNadiResult] = []

    for name in planets:
        p = chart.planets[name]
        nadi_key = _NAKSHATRA_NADI_CYCLE[p.nakshatra_index % 3]
        results.append(
            NakshatraNadiResult(
                planet=name,
                nakshatra=p.nakshatra,
                nakshatra_index=p.nakshatra_index,
                nadi=nadi_key,
                nadi_name=_NADI_NAMES[nadi_key],
                nadi_hi=_NADI_NAMES_HI[nadi_key],
                nature=_NADI_NATURE[nadi_key],
            )
        )
    return results


def compute_nadi_amsha(chart: ChartData) -> list[NadiAmshaPosition]:
    """Compute Nadi Amsha position for each planet (fine-grained analysis).

    Each sign is divided into 150 Nadi Amshas of 12' (0.2°) each.
    The amshas cycle through Pingala (1-50), Ida (51-100), Sushumna (101-150).

    This gives a highly precise view of planetary placement, used in Nadi
    Jyotish for exact event prediction.

    Args:
        chart: Natal birth chart.

    Returns:
        List of NadiAmshaPosition for each of the 7 classical planets.
    """
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    results: list[NadiAmshaPosition] = []

    for name in planets:
        p = chart.planets[name]
        position = _compute_single_nadi_amsha(name, p.longitude, p.sign_index, p.degree_in_sign)
        results.append(position)
    return results


def compute_nadi_analysis(chart: ChartData) -> NadiAnalysisResult:
    """Compute full Nadi analysis including both Nakshatra Nadi and Nadi Amsha.

    Args:
        chart: Natal birth chart.

    Returns:
        NadiAnalysisResult with complete Nadi breakdown.
    """
    nakshatra_nadis = compute_nakshatra_nadi(chart)
    nadi_amshas = compute_nadi_amsha(chart)

    # Count Nadi distribution (at nakshatra level for the 7 planets)
    distribution: dict[str, int] = {"aadi": 0, "madhya": 0, "antya": 0}
    for r in nakshatra_nadis:
        distribution[r.nadi] += 1

    dominant = max(distribution, key=lambda k: distribution[k])

    return NadiAnalysisResult(
        nakshatra_nadis=nakshatra_nadis,
        nadi_amshas=nadi_amshas,
        dominant_nadi=dominant,
        nadi_distribution=distribution,
    )


def get_nadi_koota_score(chart1: ChartData, chart2: ChartData) -> dict[str, object]:
    """Compute Nadi Koota score for compatibility between two charts.

    Nadi Koota is worth 8 points in the 36-point Ashta Koota system.
    Maximum points (8) are given when the two Moon signs are in DIFFERENT
    Nadis. Zero points when in the SAME Nadi (Nadi Dosha).

    Args:
        chart1: First chart (usually bride/groom 1).
        chart2: Second chart (usually groom/bride 2).

    Returns:
        Dict with nadi1, nadi2, score (0 or 8), and dosha flag.
    """
    moon1_nakshatra_idx = chart1.planets["Moon"].nakshatra_index
    moon2_nakshatra_idx = chart2.planets["Moon"].nakshatra_index

    nadi1 = _NAKSHATRA_NADI_CYCLE[moon1_nakshatra_idx % 3]
    nadi2 = _NAKSHATRA_NADI_CYCLE[moon2_nakshatra_idx % 3]

    same_nadi = nadi1 == nadi2
    score = 0 if same_nadi else 8
    dosha = same_nadi

    return {
        "nadi1": _NADI_NAMES[nadi1],
        "nadi2": _NADI_NAMES[nadi2],
        "nadi1_key": nadi1,
        "nadi2_key": nadi2,
        "score": score,
        "max_score": 8,
        "nadi_dosha": dosha,
        "dosha_description": (
            "Nadi Dosha present — same Nadi Koota. Can cause health/progeny issues in marriage."
            if dosha
            else "No Nadi Dosha — different Nadis. Excellent compatibility."
        ),
    }


# ── Private helpers ────────────────────────────────────────────────────────


def _compute_single_nadi_amsha(
    planet_name: str,
    longitude: float,
    sign_index: int,
    degree_in_sign: float,
) -> NadiAmshaPosition:
    """Compute the Nadi Amsha position for a single planet."""
    # Amsha number within the sign (1-150)
    amsha_num = int(degree_in_sign / _NADI_AMSHA_SIZE) + 1
    amsha_num = min(amsha_num, _NADI_AMSHAS_PER_SIGN)  # Clamp to 150

    # Start/end degrees of this Nadi Amsha within the sign
    amsha_start = (amsha_num - 1) * _NADI_AMSHA_SIZE
    amsha_end = amsha_num * _NADI_AMSHA_SIZE

    # Classify which Nadi this amsha belongs to
    nadi_key = _classify_amsha_nadi(amsha_num)

    nadi_full_names: dict[str, str] = {
        "pingala": "Pingala (Solar/Right channel)",
        "ida": "Ida (Lunar/Left channel)",
        "sushumna": "Sushumna (Central/Both channels)",
    }

    return NadiAmshaPosition(
        planet=planet_name,
        longitude=longitude,
        sign_index=sign_index,
        sign=SIGNS[sign_index],
        sign_en=SIGNS_EN[sign_index],
        degree_in_sign=round(degree_in_sign, 4),
        nadi_amsha_number=amsha_num,
        nadi_amsha_start=round(amsha_start, 4),
        nadi_amsha_end=round(amsha_end, 4),
        nadi=nadi_key,
        nadi_name=nadi_full_names[nadi_key],
    )


def _classify_amsha_nadi(amsha_num: int) -> str:
    """Classify a Nadi Amsha number (1-150) into its Nadi channel."""
    for start, end, nadi in _AMSHA_NADI_GROUPS:
        if start <= amsha_num <= end:
            return nadi
    return "sushumna"  # Fallback (should not happen with valid input)
