"""Dosha detection — Mangal, Kaal Sarp, Sadesati, Pitra dosha."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, has_aspect
from daivai_engine.compute.dosha_sadesati_pitra import (
    detect_pitra_dosha,
    detect_sadesati,
)
from daivai_engine.constants import SIGNS
from daivai_engine.models.dosha import DoshaResult


# Re-export for backward compatibility
detect_sadesati = detect_sadesati
detect_pitra_dosha = detect_pitra_dosha


# -- Kaal Sarp Dosha: 12 named types by Rahu's house -------------------------
# Source: Traditional Jyotish; widely cited in post-classical texts.
_KSD_TYPES: dict[int, tuple[str, str]] = {
    1: ("Anant", "अनन्त"),
    2: ("Kulik", "कुलिक"),
    3: ("Vasuki", "वासुकि"),
    4: ("Shankhapal", "शंखपाल"),
    5: ("Padma", "पद्म"),
    6: ("Mahapadma", "महापद्म"),
    7: ("Takshak", "तक्षक"),
    8: ("Karkotak", "कर्कोटक"),
    9: ("Shankhnaad", "शंखनाद"),
    10: ("Ghatak", "घातक"),
    11: ("Vishdhar", "विषधर"),
    12: ("Sheshnag", "शेषनाग"),
}


def _mangal_cancellations(chart: ChartData, mars_house_from_ref: int) -> list[str]:
    """Compute Mangal Dosha cancellation conditions for a given reference point.

    Args:
        chart: The birth chart.
        mars_house_from_ref: Mars's house number counted from the reference point.

    Returns:
        List of cancellation reason strings (empty = no cancellation).
    """
    mars = chart.planets["Mars"]
    moon = chart.planets["Moon"]
    cancellations: list[str] = []

    # 1. Mars in own sign (Aries=0, Scorpio=7) — BPHS
    if mars.sign_index in (0, 7):
        cancellations.append("Mars in own sign (Aries/Scorpio)")

    # 2. Mars in exaltation (Capricorn=9) — BPHS
    if mars.sign_index == 9:
        cancellations.append("Mars exalted in Capricorn")

    # 3. Mars in Jupiter's sign (Sagittarius=8, Pisces=11) — Phaladeepika
    if mars.sign_index in (8, 11):
        cancellations.append(
            "Mars in Jupiter's sign (Sagittarius/Pisces) — friendly, reduces severity"
        )

    # 4. Lagna is Aries or Scorpio (Mars = lagna lord) — BPHS Ch.77
    if chart.lagna_sign_index in (0, 7):
        cancellations.append(
            f"Lagna is {SIGNS[chart.lagna_sign_index]} — Mars is lagna lord, dosha cancelled"
        )

    # 5. Jupiter aspects Mars — Traditional Parashari
    if has_aspect(chart, "Jupiter", mars.house):
        cancellations.append("Jupiter aspects Mars")

    # 6. Saturn aspects Mars — Phaladeepika
    if has_aspect(chart, "Saturn", mars.house):
        cancellations.append("Saturn aspects Mars")

    # 7. Mars conjunct Jupiter — Phaladeepika
    jupiter = chart.planets.get("Jupiter")
    if jupiter and jupiter.sign_index == mars.sign_index:
        cancellations.append("Mars conjunct Jupiter — neutralises Kuja Dosha")

    # 8. Moon conjunct Mars (Chandra-Mangal) — Phaladeepika
    if moon.sign_index == mars.sign_index:
        cancellations.append("Moon conjunct Mars — Chandra-Mangal cancels Kuja Dosha")

    # 9. Mars in 2nd house from ref in Gemini or Virgo (Mercury sign) — South Indian
    if mars_house_from_ref == 2 and mars.sign_index in (2, 5):
        cancellations.append(
            "Mars in 2nd in Gemini/Virgo (Mercury sign) — South Indian cancellation"
        )

    # 10. Mars in 12th house from ref in Taurus or Libra (Venus sign) — South Indian
    if mars_house_from_ref == 12 and mars.sign_index in (1, 6):
        cancellations.append(
            "Mars in 12th in Taurus/Libra (Venus sign) — South Indian cancellation"
        )

    return cancellations


def detect_mangal_dosha(chart: ChartData) -> DoshaResult:
    """Detect Mangal (Kuja) Dosha from Lagna, Moon, and Venus.

    Mars in 1/2/4/7/8/12 from ANY of the three reference points triggers the dosha:
    - From Lagna (ascendant)
    - From Moon's sign (Chandrama)
    - From Venus's sign (Shukra)

    The result carries lagna_dosha / moon_dosha / venus_dosha flags indicating
    which reference points triggered.

    Source: BPHS Ch.77, Phaladeepika.
    Cancellation rules: BPHS, Muhurta Chintamani, South Indian traditions.
    """
    mars = chart.planets["Mars"]
    moon = chart.planets["Moon"]
    venus = chart.planets["Venus"]
    mangal_houses = {1, 2, 4, 7, 8, 12}

    # House of Mars from each reference point
    lagna_mars_house: int = mars.house
    moon_mars_house: int = (mars.sign_index - moon.sign_index) % 12 + 1
    venus_mars_house: int = (mars.sign_index - venus.sign_index) % 12 + 1

    lagna_triggered = lagna_mars_house in mangal_houses
    moon_triggered = moon_mars_house in mangal_houses
    venus_triggered = venus_mars_house in mangal_houses

    any_triggered = lagna_triggered or moon_triggered or venus_triggered

    if not any_triggered:
        return DoshaResult(
            name="Mangal Dosha",
            name_hindi="मंगल दोष",
            is_present=False,
            severity="none",
            lagna_dosha=False,
            moon_dosha=False,
            venus_dosha=False,
            planets_involved=["Mars"],
            houses_involved=[mars.house],
            description="Mars not in 1/2/4/7/8/12 from Lagna, Moon, or Venus — no Mangal Dosha",
            cancellation_reasons=[],
        )

    # Collect cancellations from all triggered reference points (union)
    all_cancellations: set[str] = set()
    if lagna_triggered:
        all_cancellations.update(_mangal_cancellations(chart, lagna_mars_house))
    if moon_triggered:
        all_cancellations.update(_mangal_cancellations(chart, moon_mars_house))
    if venus_triggered:
        all_cancellations.update(_mangal_cancellations(chart, venus_mars_house))
    cancellations = sorted(all_cancellations)

    # Build triggered-point description
    triggered_parts: list[str] = []
    if lagna_triggered:
        triggered_parts.append(f"Lagna (Mars in {lagna_mars_house}th)")
    if moon_triggered:
        triggered_parts.append(f"Moon (Mars in {moon_mars_house}th from Moon)")
    if venus_triggered:
        triggered_parts.append(f"Venus (Mars in {venus_mars_house}th from Venus)")

    is_present = len(cancellations) == 0
    severity = "cancelled" if len(cancellations) >= 2 else ("partial" if cancellations else "full")
    if severity == "cancelled":
        is_present = False

    desc = "Mangal Dosha triggered from: " + ", ".join(triggered_parts)
    if cancellations:
        desc += f" — cancellations: {', '.join(cancellations)}"

    return DoshaResult(
        name="Mangal Dosha",
        name_hindi="मंगल दोष",
        is_present=is_present,
        severity=severity,
        lagna_dosha=lagna_triggered,
        moon_dosha=moon_triggered,
        venus_dosha=venus_triggered,
        planets_involved=["Mars"],
        houses_involved=[mars.house],
        description=desc,
        cancellation_reasons=cancellations,
    )


def _ksd_type(rahu_house: int) -> tuple[str, str]:
    """Return (english_name, hindi_name) of the Kaal Sarp type from Rahu's house.

    Source: Traditional Jyotish; 12 types named after serpents.
    """
    return _KSD_TYPES.get(rahu_house, ("Unknown", "अज्ञात"))


def detect_kaal_sarp_dosha(chart: ChartData) -> DoshaResult:
    """Detect Kaal Sarp Dosha — all planets hemmed between Rahu-Ketu.

    Also identifies which of the 12 named KSD types applies based on Rahu's house.
    Source: Traditional Jyotish (not in BPHS — post-classical).
    """
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

        # Check if planet is between Rahu and Ketu (going forward from Rahu)
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

    ksd_name, ksd_name_hi = _ksd_type(rahu.house)

    if all_between:
        return DoshaResult(
            name="Kaal Sarp Dosha",
            name_hindi="काल सर्प दोष",
            is_present=True,
            severity="full",
            planets_involved=["Rahu", "Ketu", *planets_between],
            houses_involved=[rahu.house, ketu.house],
            description=(
                f"Full Kaal Sarp Dosha — {ksd_name} ({ksd_name_hi}) type. "
                f"Rahu in house {rahu.house}, Ketu in house {ketu.house}. "
                "All 7 planets hemmed between Rahu-Ketu axis."
            ),
            cancellation_reasons=[],
        )
    elif partial:
        return DoshaResult(
            name="Kaal Sarp Dosha",
            name_hindi="काल सर्प दोष",
            is_present=True,
            severity="partial",
            planets_involved=["Rahu", "Ketu", *planets_between],
            houses_involved=[rahu.house, ketu.house],
            description=(
                f"Partial Kaal Sarp — {ksd_name} ({ksd_name_hi}) type (if full). "
                f"{planets_outside[0]} escapes the axis, reducing severity."
            ),
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


def detect_all_doshas(chart: ChartData) -> list[DoshaResult]:
    """Detect all doshas — 10 checks from BPHS, Phaladeepika."""
    from daivai_engine.compute.dosha_extended import detect_extended_doshas

    return [
        detect_mangal_dosha(chart),
        detect_kaal_sarp_dosha(chart),
        detect_sadesati(chart),
        detect_pitra_dosha(chart),
        *detect_extended_doshas(chart),
    ]
