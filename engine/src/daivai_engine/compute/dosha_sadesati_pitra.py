"""Dosha detection — Sadesati and Pitra dosha.

Source: BPHS, Phaladeepika, traditional Jyotish.
"""

from __future__ import annotations

from daivai_engine.constants import SIGN_LORDS, SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dosha import DoshaResult


def detect_sadesati(chart: ChartData, transit_saturn_sign: int | None = None) -> DoshaResult:
    """Detect Sadesati — Saturn transiting 12th/1st/2nd from Moon sign.

    Args:
        chart: Natal chart
        transit_saturn_sign: Current transit Saturn sign index. If None, uses natal Saturn.
    """
    moon_sign = chart.planets["Moon"].sign_index

    if transit_saturn_sign is None:
        # Use natal Saturn for basic check
        saturn_sign = chart.planets["Saturn"].sign_index
    else:
        saturn_sign = transit_saturn_sign

    sadesati_signs = {
        (moon_sign - 1) % 12,  # 12th from Moon
        moon_sign,  # 1st (over Moon)
        (moon_sign + 1) % 12,  # 2nd from Moon
    }

    if saturn_sign in sadesati_signs:
        # Determine phase
        if saturn_sign == (moon_sign - 1) % 12:
            phase = "Rising (12th from Moon) — beginning phase"
        elif saturn_sign == moon_sign:
            phase = "Peak (over Moon) — most intense phase"
        else:
            phase = "Setting (2nd from Moon) — concluding phase"

        return DoshaResult(
            name="Sadesati",
            name_hindi="साढ़ेसाती",
            is_present=True,
            severity="full",
            planets_involved=["Saturn", "Moon"],
            houses_involved=[chart.planets["Moon"].house],
            description=f"Saturn in {SIGNS[saturn_sign]} — {phase}",
            cancellation_reasons=[],
        )

    return DoshaResult(
        name="Sadesati",
        name_hindi="साढ़ेसाती",
        is_present=False,
        severity="none",
        planets_involved=["Saturn", "Moon"],
        houses_involved=[],
        description="Saturn not transiting 12th/1st/2nd from Moon — no Sadesati",
        cancellation_reasons=[],
    )


def detect_pitra_dosha(chart: ChartData) -> DoshaResult:
    """Detect Pitra Dosha — Sun conjunct Rahu, or 9th lord afflicted."""
    sun = chart.planets["Sun"]
    rahu = chart.planets["Rahu"]
    ketu = chart.planets["Ketu"]
    saturn = chart.planets["Saturn"]

    reasons = []

    # Condition 1: Sun conjunct Rahu
    if sun.sign_index == rahu.sign_index:
        reasons.append("Sun conjunct Rahu (Grahan Yoga on Sun)")

    # Condition 2: Sun conjunct Ketu
    if sun.sign_index == ketu.sign_index:
        reasons.append("Sun conjunct Ketu")

    # Condition 3: 9th lord afflicted by Rahu/Ketu/Saturn
    lord_9 = SIGN_LORDS[(chart.lagna_sign_index + 8) % 12]
    p9 = chart.planets.get(lord_9)
    if p9:
        if p9.sign_index == rahu.sign_index:
            reasons.append(f"9th lord ({lord_9}) conjunct Rahu")
        if p9.sign_index == ketu.sign_index:
            reasons.append(f"9th lord ({lord_9}) conjunct Ketu")
        if p9.sign_index == saturn.sign_index and lord_9 != "Saturn":
            reasons.append(f"9th lord ({lord_9}) conjunct Saturn")

    if reasons:
        return DoshaResult(
            name="Pitra Dosha",
            name_hindi="पितृ दोष",
            is_present=True,
            severity="full" if len(reasons) >= 2 else "partial",
            planets_involved=["Sun", "Rahu", lord_9],
            houses_involved=[sun.house, 9],
            description="; ".join(reasons),
            cancellation_reasons=[],
        )

    return DoshaResult(
        name="Pitra Dosha",
        name_hindi="पितृ दोष",
        is_present=False,
        severity="none",
        planets_involved=["Sun"],
        houses_involved=[9],
        description="No Pitra Dosha indicators found",
        cancellation_reasons=[],
    )
