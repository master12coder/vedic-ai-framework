"""Advanced Compatibility — Mangal Dosha detailed + Nadi Dosha analysis.

Extends basic matching with detailed severity scoring and cancellation logic.

Source: BPHS, Muhurta Chintamani.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.constants import (
    EXALTATION,
    NAKSHATRA_LORDS,
    NAKSHATRA_NADIS,
    NATURAL_FRIENDS,
    OWN_SIGNS,
)
from daivai_engine.models.chart import ChartData


class MangalDoshaDetail(BaseModel):
    """Detailed Mangal Dosha analysis with severity and cancellations."""

    is_present: bool
    severity: int  # 0-10 scale
    mars_house: int
    cancellations: list[str]
    net_effect: str  # cancelled / mild / moderate / severe
    description: str


class NadiDoshaDetail(BaseModel):
    """Nadi Dosha analysis between two charts."""

    is_present: bool
    person1_nadi: str  # Aadi / Madhya / Antya
    person2_nadi: str
    exceptions: list[str]
    net_severity: str  # cancelled / mild / severe
    description: str


# Mars houses that cause Mangal Dosha (from Lagna) — BPHS
_MANGAL_HOUSES = {1, 2, 4, 7, 8, 12}


def compute_mangal_dosha_detailed(chart: ChartData) -> MangalDoshaDetail:
    """Compute Mangal Dosha with full cancellation analysis.

    Mars in 1/2/4/7/8/12 from Lagna = Mangal Dosha present.
    Multiple cancellation conditions can reduce or eliminate it.

    Source: BPHS, Muhurta Chintamani.
    """
    mars = chart.planets["Mars"]
    is_present = mars.house in _MANGAL_HOUSES

    if not is_present:
        return MangalDoshaDetail(
            is_present=False,
            severity=0,
            mars_house=mars.house,
            cancellations=[],
            net_effect="none",
            description="Mars not in 1/2/4/7/8/12 — no Mangal Dosha",
        )

    severity = 7  # Start at moderate-high
    cancellations: list[str] = []

    # Cancellation 1: Mars in own sign (Aries/Scorpio) — BPHS
    if mars.sign_index in OWN_SIGNS.get("Mars", []):
        cancellations.append("Mars in own sign (Aries/Scorpio)")
        severity -= 3

    # Cancellation 2: Mars exalted (Capricorn)
    if EXALTATION.get("Mars") == mars.sign_index:
        cancellations.append("Mars exalted in Capricorn")
        severity -= 3

    # Cancellation 3: Jupiter aspects Mars
    jupiter = chart.planets["Jupiter"]
    if _aspects(jupiter.house, mars.house):
        cancellations.append("Jupiter aspects Mars")
        severity -= 2

    # Cancellation 4: Venus aspects Mars
    venus = chart.planets["Venus"]
    if _aspects(venus.house, mars.house):
        cancellations.append("Venus aspects Mars")
        severity -= 1

    # Cancellation 5: Mars in 2nd but in Gemini/Virgo
    if mars.house == 2 and mars.sign_index in (2, 5):
        cancellations.append("Mars in 2nd house in Gemini/Virgo")
        severity -= 2

    # Cancellation 6: Mars in 12th but in Taurus/Libra
    if mars.house == 12 and mars.sign_index in (1, 6):
        cancellations.append("Mars in 12th house in Taurus/Libra")
        severity -= 2

    severity = max(0, severity)
    if severity == 0:
        net = "cancelled"
    elif severity <= 3:
        net = "mild"
    elif severity <= 6:
        net = "moderate"
    else:
        net = "severe"

    return MangalDoshaDetail(
        is_present=True,
        severity=severity,
        mars_house=mars.house,
        cancellations=cancellations,
        net_effect=net,
        description=f"Mars in house {mars.house}: severity {severity}/10 ({net})",
    )


def analyze_nadi_dosha(
    chart1: ChartData,
    chart2: ChartData,
) -> NadiDoshaDetail:
    """Analyze Nadi Dosha between two charts.

    Same Nadi = Nadi Dosha (0 points in Ashtakoot, most serious).
    Multiple exceptions can mitigate.

    Source: Muhurta Chintamani.
    """
    nak1 = chart1.planets["Moon"].nakshatra_index
    nak2 = chart2.planets["Moon"].nakshatra_index
    nadi1 = NAKSHATRA_NADIS[nak1]
    nadi2 = NAKSHATRA_NADIS[nak2]

    is_present = nadi1 == nadi2
    if not is_present:
        return NadiDoshaDetail(
            is_present=False,
            person1_nadi=nadi1,
            person2_nadi=nadi2,
            exceptions=[],
            net_severity="none",
            description=f"Different Nadis ({nadi1} vs {nadi2}) — no dosha",
        )

    exceptions: list[str] = []

    # Exception 1: Same nakshatra, different padas
    if (
        chart1.planets["Moon"].nakshatra == chart2.planets["Moon"].nakshatra
        and chart1.planets["Moon"].pada != chart2.planets["Moon"].pada
    ):
        exceptions.append("Same nakshatra but different padas")

    # Exception 2: Nakshatra lords are friends
    lord1 = NAKSHATRA_LORDS[nak1]
    lord2 = NAKSHATRA_LORDS[nak2]
    if lord2 in NATURAL_FRIENDS.get(lord1, []):
        exceptions.append(f"Nakshatra lords are friends ({lord1}-{lord2})")

    if exceptions:
        net = "mild"
    else:
        net = "severe"

    return NadiDoshaDetail(
        is_present=True,
        person1_nadi=nadi1,
        person2_nadi=nadi2,
        exceptions=exceptions,
        net_severity=net,
        description=f"Same Nadi ({nadi1}) — {net} dosha{', with exceptions' if exceptions else ''}",
    )


def _aspects(from_house: int, to_house: int) -> bool:
    """Check if from_house aspects to_house (7th aspect)."""
    return ((from_house - 1 + 6) % 12) + 1 == to_house
