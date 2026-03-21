"""Additional yoga detectors — Gajakesari, Budhaditya, Kemdrum, etc."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import (
    DUSTHANAS,
    EXALTATION,
    KENDRAS,
    OWN_SIGNS,
    PLANETS,
    SIGN_LORDS,
    TRIKONAS,
)
from daivai_engine.models.yoga import YogaResult


def _is_in_kendra(house: int) -> bool:
    """Check if house is a kendra (1/4/7/10)."""
    return house in KENDRAS


def _is_in_own_or_exalted(planet_name: str, sign_index: int) -> bool:
    """Check if planet is in own or exalted sign."""
    if planet_name in EXALTATION and EXALTATION[planet_name] == sign_index:
        return True
    return bool(planet_name in OWN_SIGNS and sign_index in OWN_SIGNS[planet_name])


def _planet_in_kendra_from_reference(chart: ChartData, planet: str, ref_planet: str) -> bool:
    """Check if planet is in kendra from reference planet."""
    p_sign = chart.planets[planet].sign_index
    ref_sign = chart.planets[ref_planet].sign_index
    distance = ((p_sign - ref_sign) % 12) + 1
    return distance in KENDRAS


def detect_other_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Gajakesari, Budhaditya, Chandra-Mangal, Vipreet Raj, and more."""
    yogas: list[YogaResult] = []

    # Gajakesari: Jupiter in kendra from Moon
    if _planet_in_kendra_from_reference(chart, "Jupiter", "Moon"):
        yogas.append(
            YogaResult(
                name="Gajakesari Yoga",
                name_hindi="गजकेसरी योग",
                is_present=True,
                planets_involved=["Jupiter", "Moon"],
                houses_involved=[chart.planets["Jupiter"].house, chart.planets["Moon"].house],
                description="Jupiter in kendra from Moon — wisdom, fame, long life, leadership",
                effect="benefic",
            )
        )

    # Budhaditya: Sun-Mercury conjunction
    sun = chart.planets["Sun"]
    mercury = chart.planets["Mercury"]
    if sun.sign_index == mercury.sign_index:
        yogas.append(
            YogaResult(
                name="Budhaditya Yoga",
                name_hindi="बुधादित्य योग",
                is_present=True,
                planets_involved=["Sun", "Mercury"],
                houses_involved=[sun.house],
                description="Sun-Mercury conjunction — intelligence, analytical mind, communication",
                effect="benefic",
            )
        )

    # Chandra-Mangal: Moon-Mars conjunction
    moon = chart.planets["Moon"]
    mars = chart.planets["Mars"]
    if moon.sign_index == mars.sign_index:
        yogas.append(
            YogaResult(
                name="Chandra-Mangal Yoga",
                name_hindi="चन्द्र-मंगल योग",
                is_present=True,
                planets_involved=["Moon", "Mars"],
                houses_involved=[moon.house],
                description="Moon-Mars conjunction — courage, wealth through effort, emotional strength",
                effect="benefic",
            )
        )

    # Vipreet Raj Yoga: dusthana lord in another dusthana
    for h in DUSTHANAS:
        lord = get_house_lord(chart, h)
        p = chart.planets.get(lord)
        if p and p.house in DUSTHANAS and p.house != h:
            yogas.append(
                YogaResult(
                    name="Vipreet Raj Yoga",
                    name_hindi="विपरीत राज योग",
                    is_present=True,
                    planets_involved=[lord],
                    houses_involved=[h, p.house],
                    description=f"{h}th lord ({lord}) in {p.house}th house — rise through adversity",
                    effect="mixed",
                )
            )

    # Neech Bhanga Raj Yoga
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        if p.dignity == "debilitated":
            debil_sign_lord = SIGN_LORDS[p.sign_index]
            dsl = chart.planets.get(debil_sign_lord)
            cancelled = False
            reason = ""
            if dsl and _is_in_kendra(dsl.house):
                cancelled = True
                reason = f"Lord of debilitation sign ({debil_sign_lord}) in kendra"
            if dsl and _planet_in_kendra_from_reference(chart, debil_sign_lord, "Moon"):
                cancelled = True
                reason = f"Lord of debilitation sign ({debil_sign_lord}) in kendra from Moon"
            if planet_name in EXALTATION:
                exalt_sign = EXALTATION[planet_name]
                exalt_lord = SIGN_LORDS[exalt_sign]
                el = chart.planets.get(exalt_lord)
                if el and _is_in_kendra(el.house):
                    cancelled = True
                    reason = f"Exaltation lord ({exalt_lord}) in kendra"
            if cancelled:
                yogas.append(
                    YogaResult(
                        name="Neech Bhanga Raj Yoga",
                        name_hindi="नीच भंग राज योग",
                        is_present=True,
                        planets_involved=[planet_name],
                        houses_involved=[p.house],
                        description=f"Debilitated {planet_name} with cancellation: {reason}",
                        effect="benefic",
                    )
                )

    # Kemdrum Dosha
    moon_sign = moon.sign_index
    sign_before = (moon_sign - 1) % 12
    sign_after = (moon_sign + 1) % 12
    has_planet_adjacent = any(
        chart.planets[pn].sign_index in (sign_before, sign_after)
        for pn in ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    )
    if not has_planet_adjacent:
        yogas.append(
            YogaResult(
                name="Kemdrum Yoga",
                name_hindi="केमद्रुम योग",
                is_present=True,
                planets_involved=["Moon"],
                houses_involved=[moon.house],
                description="No planet in 2nd or 12th from Moon — loneliness, financial fluctuations",
                effect="malefic",
            )
        )

    # Saraswati Yoga
    jup = chart.planets["Jupiter"]
    ven = chart.planets["Venus"]
    mer = chart.planets["Mercury"]
    kendra_trikona = set(KENDRAS) | set(TRIKONAS)
    if all(chart.planets[p].house in kendra_trikona for p in ["Jupiter", "Venus", "Mercury"]):
        yogas.append(
            YogaResult(
                name="Saraswati Yoga",
                name_hindi="सरस्वती योग",
                is_present=True,
                planets_involved=["Jupiter", "Venus", "Mercury"],
                houses_involved=[jup.house, ven.house, mer.house],
                description="Jupiter, Venus, Mercury in kendra/trikona — learning, wisdom, arts",
                effect="benefic",
            )
        )

    # Lakshmi Yoga
    lord_9 = get_house_lord(chart, 9)
    p9 = chart.planets.get(lord_9)
    if p9 and _is_in_kendra(p9.house) and _is_in_own_or_exalted(lord_9, p9.sign_index):
        yogas.append(
            YogaResult(
                name="Lakshmi Yoga",
                name_hindi="लक्ष्मी योग",
                is_present=True,
                planets_involved=[lord_9],
                houses_involved=[9, p9.house],
                description=f"9th lord ({lord_9}) in own/exalted in kendra — fortune, prosperity",
                effect="benefic",
            )
        )

    return yogas
