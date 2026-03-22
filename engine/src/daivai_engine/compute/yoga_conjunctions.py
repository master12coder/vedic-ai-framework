"""Planetary conjunction yoga detection — classical pair combinations.

Detects specific two-planet conjunctions that carry traditional yoga significance:
  Mars-Saturn, Mercury-Saturn, Venus-Saturn, Jupiter-Saturn,
  Mars-Mercury, Moon-Saturn (Visha), Sun-Saturn, Mars-Jupiter.

Also detects enhanced Sunapha/Anapha/Veshi/Voshi with planet-specific effects.

Source: Phaladeepika Ch.9; Saravali; BPHS.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.yoga_daridra import detect_daridra_extended
from daivai_engine.models.yoga import YogaResult


__all__ = [
    "detect_conjunction_yogas",
    "detect_daridra_extended",
    "detect_sunapha_anapha_specific",
]


_CONJUNCTION_YOGAS: list[tuple[str, str, str, str, str, str]] = [
    # (p1, p2, name, name_hi, description, effect)
    (
        "Mars",
        "Saturn",
        "Mars-Saturn Conjunction Yoga",
        "मंगल-शनि युति योग",
        "Mars+Saturn conjunct — friction, accidents, karmic struggle; competitive drive in upachaya houses",
        "malefic",
    ),
    (
        "Mercury",
        "Saturn",
        "Mercury-Saturn Conjunction Yoga",
        "बुध-शनि युति योग",
        "Mercury+Saturn conjunct — serious systematic mind, technical precision; tendency to melancholy",
        "mixed",
    ),
    (
        "Venus",
        "Saturn",
        "Venus-Saturn Conjunction Yoga",
        "शुक्र-शनि युति योग",
        "Venus+Saturn conjunct — karmic love relationships, delayed but enduring; best in Libra",
        "mixed",
    ),
    (
        "Jupiter",
        "Saturn",
        "Jupiter-Saturn Conjunction Yoga",
        "गुरु-शनि युति योग",
        "Jupiter+Saturn conjunct — expansion meets restriction; philosophical authority, alternating fortune",
        "mixed",
    ),
    (
        "Mars",
        "Mercury",
        "Mars-Mercury Conjunction Yoga",
        "मंगल-बुध युति योग",
        "Mars+Mercury conjunct — sharp incisive mind, technical skill, argumentative; excellent for engineering",
        "mixed",
    ),
    (
        "Moon",
        "Saturn",
        "Visha Yoga (Moon-Saturn)",
        "विष योग (चंद्र-शनि)",
        "Moon+Saturn conjunct — emotional heaviness, detachment from mother; discipline through suffering",
        "malefic",
    ),
    (
        "Sun",
        "Saturn",
        "Sun-Saturn Conjunction Yoga",
        "सूर्य-शनि युति योग",
        "Sun+Saturn conjunct — difficult father relationship, delayed authority; achieved through persistence",
        "malefic",
    ),
    (
        "Mars",
        "Jupiter",
        "Mars-Jupiter Conjunction Yoga",
        "मंगल-गुरु युति योग",
        "Mars+Jupiter conjunct — warrior-philosopher; brave, righteous action; dharmic courage",
        "benefic",
    ),
    (
        "Venus",
        "Jupiter",
        "Venus-Jupiter Conjunction Yoga",
        "शुक्र-गुरु युति योग",
        "Venus+Jupiter conjunct — beauty with wisdom; artistic spirituality; idealized love and creativity",
        "benefic",
    ),
    (
        "Moon",
        "Mars",
        "Chandra-Mangal Conjunction",
        "चंद्र-मंगल युति",
        "Moon+Mars conjunct — emotional courage, drive; wealth through determination; passionate temperament",
        "mixed",
    ),
    (
        "Sun",
        "Jupiter",
        "Sun-Jupiter Conjunction Yoga",
        "सूर्य-गुरु युति योग",
        "Sun+Jupiter conjunct — kingly wisdom; philosophical authority; benefic except when Jupiter combust",
        "benefic",
    ),
    (
        "Sun",
        "Venus",
        "Sun-Venus Conjunction Yoga",
        "सूर्य-शुक्र युति योग",
        "Sun+Venus conjunct — often combust Venus; artistic ego; charm in authority; fame through aesthetics",
        "mixed",
    ),
]


def detect_conjunction_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect classical two-planet conjunction yogas.

    Args:
        chart: Computed birth chart.

    Returns:
        List of detected conjunction YogaResults.
    """
    yogas: list[YogaResult] = []

    for p1, p2, name, name_hi, desc, effect in _CONJUNCTION_YOGAS:
        planet1 = chart.planets.get(p1)
        planet2 = chart.planets.get(p2)
        if not planet1 or not planet2:
            continue
        if planet1.sign_index != planet2.sign_index:
            continue

        # Adjust effect based on house position (upachaya is better for malefics)
        final_effect = effect
        if effect == "malefic" and planet1.house in (3, 6, 10, 11):
            final_effect = "mixed"

        # Adjust Visha Yoga based on Moon phase
        if name.startswith("Visha"):
            moon_sun_diff = (chart.planets["Moon"].longitude - chart.planets["Sun"].longitude) % 360
            if moon_sun_diff > 120:
                final_effect = "mixed"  # Bright Moon reduces Visha severity
                desc = desc + " [reduced: bright Moon]"

        yogas.append(
            YogaResult(
                name=name,
                name_hindi=name_hi,
                is_present=True,
                planets_involved=[p1, p2],
                houses_involved=[planet1.house],
                description=f"{desc} (H{planet1.house})",
                effect=final_effect,
            )
        )

    return yogas


def detect_sunapha_anapha_specific(chart: ChartData) -> list[YogaResult]:
    """Detect Sunapha and Anapha with planet-specific effect descriptions.

    Phaladeepika Ch.7 gives specific effects based on which planet is
    in the 2nd or 12th from Moon. This enhances the generic detection
    in yoga_extended with individual planet effects.

    Args:
        chart: Computed birth chart.

    Returns:
        List of YogaResults with planet-specific Sunapha/Anapha descriptions.
    """
    yogas: list[YogaResult] = []
    moon = chart.planets["Moon"]
    moon_sign = moon.sign_index

    # Planet-specific Sunapha effects (2nd from Moon) — Phaladeepika 7.1
    sunapha_effects = {
        "Mars": ("warrior wealth, land/property, physical labor income", "mixed"),
        "Mercury": ("trade wealth, commerce, communication skills, eloquence", "benefic"),
        "Jupiter": ("scholarly wealth, respect, wisdom, spiritual prosperity", "benefic"),
        "Venus": ("artistic wealth, comforts, beautiful spouse, luxury", "benefic"),
        "Saturn": ("wealth through hard work, mining, land; austere prosperity", "mixed"),
    }
    sign_2nd = (moon_sign + 1) % 12
    for planet_name, (effect_desc, effect) in sunapha_effects.items():
        p = chart.planets[planet_name]
        if p.sign_index == sign_2nd:
            yogas.append(
                YogaResult(
                    name=f"Sunapha Yoga ({planet_name})",
                    name_hindi="सुनफा योग",
                    is_present=True,
                    planets_involved=[planet_name, "Moon"],
                    houses_involved=[moon.house],
                    description=f"{planet_name} in 2nd from Moon — {effect_desc}",
                    effect=effect,
                )
            )

    # Planet-specific Anapha effects (12th from Moon) — Phaladeepika 7.2
    anapha_effects = {
        "Mars": ("courageous renunciation, physical independence, athletic withdrawal", "mixed"),
        "Mercury": ("scholarly retreat, writing, learned communication gifts", "benefic"),
        "Jupiter": ("wise generosity, spiritual expression, philosophical sharing", "benefic"),
        "Venus": ("graceful expression, artistic generosity, charming personality", "benefic"),
        "Saturn": ("austere expression, detached giving, philosophical independence", "mixed"),
    }
    sign_12th = (moon_sign - 1) % 12
    for planet_name, (effect_desc, effect) in anapha_effects.items():
        p = chart.planets[planet_name]
        if p.sign_index == sign_12th:
            yogas.append(
                YogaResult(
                    name=f"Anapha Yoga ({planet_name})",
                    name_hindi="अनफा योग",
                    is_present=True,
                    planets_involved=[planet_name, "Moon"],
                    houses_involved=[moon.house],
                    description=f"{planet_name} in 12th from Moon — {effect_desc}",
                    effect=effect,
                )
            )

    return yogas
