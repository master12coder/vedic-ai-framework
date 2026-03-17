"""Dosha detection — Mangal, Kaal Sarp, Sadesati, Pitra dosha."""

from __future__ import annotations

from datetime import datetime

from jyotish.utils.constants import SIGN_LORDS, SIGNS
from jyotish.compute.chart import ChartData, has_aspect
from jyotish.domain.models.dosha import DoshaResult


def detect_mangal_dosha(chart: ChartData) -> DoshaResult:
    """Detect Mangal (Kuja) Dosha — Mars in 1/2/4/7/8/12 from lagna."""
    mars = chart.planets["Mars"]
    mangal_houses = {1, 2, 4, 7, 8, 12}

    if mars.house not in mangal_houses:
        return DoshaResult(
            name="Mangal Dosha",
            name_hindi="मंगल दोष",
            is_present=False,
            severity="none",
            planets_involved=["Mars"],
            houses_involved=[mars.house],
            description="Mars not in 1/2/4/7/8/12 — no Mangal Dosha",
            cancellation_reasons=[],
        )

    # Check cancellation conditions
    cancellations = []

    # 1. Mars in own sign (Aries/Scorpio)
    if mars.sign_index in (0, 7):
        cancellations.append("Mars in own sign (Aries/Scorpio)")

    # 2. Mars in exaltation (Capricorn)
    if mars.sign_index == 9:
        cancellations.append("Mars exalted in Capricorn")

    # 3. Jupiter aspect on Mars
    if has_aspect(chart, "Jupiter", mars.house):
        cancellations.append("Jupiter aspects Mars")

    # 4. Venus aspect on Mars (soft planet mitigates)
    if has_aspect(chart, "Venus", mars.house):
        cancellations.append("Venus aspects Mars")

    # 5. Mars in 1st/8th for Aries/Scorpio lagna (own sign)
    if chart.lagna_sign_index in (0, 7) and mars.house in (1, 8):
        cancellations.append(f"Mars in own house for {SIGNS[chart.lagna_sign_index]} lagna")

    is_present = len(cancellations) == 0
    severity = "cancelled" if cancellations else "full"
    if len(cancellations) > 0 and len(cancellations) < 3:
        severity = "partial"
        is_present = True

    return DoshaResult(
        name="Mangal Dosha",
        name_hindi="मंगल दोष",
        is_present=is_present,
        severity=severity,
        planets_involved=["Mars"],
        houses_involved=[mars.house],
        description=f"Mars in {mars.house}th house from lagna"
        + (f" — cancellations: {', '.join(cancellations)}" if cancellations else ""),
        cancellation_reasons=cancellations,
    )


def detect_kaal_sarp_dosha(chart: ChartData) -> DoshaResult:
    """Detect Kaal Sarp Dosha — all planets hemmed between Rahu-Ketu."""
    rahu = chart.planets["Rahu"]
    ketu = chart.planets["Ketu"]

    rahu_lon = rahu.longitude
    ketu_lon = ketu.longitude

    # Count planets on each side of Rahu-Ketu axis
    planets_between = []
    planets_outside = []

    for pname in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p = chart.planets[pname]
        p_lon = p.longitude

        # Check if planet is between Rahu and Ketu (going forward)
        if rahu_lon < ketu_lon:
            between = rahu_lon <= p_lon <= ketu_lon
        else:
            between = p_lon >= rahu_lon or p_lon <= ketu_lon

        if between:
            planets_between.append(pname)
        else:
            planets_outside.append(pname)

    all_between = len(planets_outside) == 0
    partial = len(planets_outside) == 1

    if all_between:
        return DoshaResult(
            name="Kaal Sarp Dosha",
            name_hindi="काल सर्प दोष",
            is_present=True,
            severity="full",
            planets_involved=["Rahu", "Ketu"] + planets_between,
            houses_involved=[rahu.house, ketu.house],
            description="All 7 planets hemmed between Rahu-Ketu — full Kaal Sarp Dosha",
            cancellation_reasons=[],
        )
    elif partial:
        return DoshaResult(
            name="Kaal Sarp Dosha",
            name_hindi="काल सर्प दोष",
            is_present=True,
            severity="partial",
            planets_involved=["Rahu", "Ketu"] + planets_between,
            houses_involved=[rahu.house, ketu.house],
            description=f"Partial Kaal Sarp — {planets_outside[0]} escapes the axis",
            cancellation_reasons=[f"{planets_outside[0]} outside Rahu-Ketu axis"],
        )
    else:
        return DoshaResult(
            name="Kaal Sarp Dosha",
            name_hindi="काल सर्प दोष",
            is_present=False,
            severity="none",
            planets_involved=["Rahu", "Ketu"],
            houses_involved=[rahu.house, ketu.house],
            description="Planets not hemmed between Rahu-Ketu — no Kaal Sarp Dosha",
            cancellation_reasons=[],
        )


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
        moon_sign,               # 1st (over Moon)
        (moon_sign + 1) % 12,   # 2nd from Moon
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


def detect_all_doshas(chart: ChartData) -> list[DoshaResult]:
    """Detect all doshas in a chart."""
    return [
        detect_mangal_dosha(chart),
        detect_kaal_sarp_dosha(chart),
        detect_sadesati(chart),
        detect_pitra_dosha(chart),
    ]
