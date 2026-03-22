"""Planetary conjunction yoga detection — classical pair combinations.

Detects specific two-planet conjunctions that carry traditional yoga significance:
  Mars-Saturn, Mercury-Saturn, Venus-Saturn, Jupiter-Saturn,
  Mars-Mercury, Moon-Saturn (Visha), Sun-Saturn, Mars-Jupiter.

Also detects enhanced Sunapha/Anapha/Veshi/Voshi with planet-specific effects.

Source: Phaladeepika Ch.9; Saravali; BPHS.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import DUSTHANAS
from daivai_engine.models.yoga import YogaResult


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


def detect_daridra_extended(chart: ChartData) -> list[YogaResult]:
    """Detect additional Daridra (poverty) Yogas from Phaladeepika Ch.12.

    Supplements the basic Daridra Yoga (11th lord in dusthana) in yoga_extended
    with additional poverty combination patterns.

    Args:
        chart: Computed birth chart.

    Returns:
        List of detected Daridra YogaResults.
    """
    yogas: list[YogaResult] = []

    # 6th lord in 11th + 11th lord in 6th (mutual exchange between debts and gains)
    lord_6 = get_house_lord(chart, 6)
    lord_11 = get_house_lord(chart, 11)
    if lord_6 != lord_11:
        p6 = chart.planets.get(lord_6)
        p11 = chart.planets.get(lord_11)
        if p6 and p11 and p6.house == 11 and p11.house == 6:
            yogas.append(
                YogaResult(
                    name="Daridra Yoga (6th-11th Exchange)",
                    name_hindi="दरिद्र योग (षष्ठ-एकादश परिवर्तन)",
                    is_present=True,
                    planets_involved=[lord_6, lord_11],
                    houses_involved=[6, 11],
                    description=(
                        f"6th lord ({lord_6}) in 11th, 11th lord ({lord_11}) in 6th — "
                        "income consumed by debts and enemies"
                    ),
                    effect="malefic",
                )
            )

    # Lagna lord in 12th + 12th lord in lagna exchange
    lord_1 = get_house_lord(chart, 1)
    lord_12 = get_house_lord(chart, 12)
    if lord_1 != lord_12:
        p1 = chart.planets.get(lord_1)
        p12 = chart.planets.get(lord_12)
        if p1 and p12 and p1.house == 12 and p12.house == 1:
            yogas.append(
                YogaResult(
                    name="Daridra Yoga (Lagna-12th Exchange)",
                    name_hindi="दरिद्र योग (लग्न-द्वादश परिवर्तन)",
                    is_present=True,
                    planets_involved=[lord_1, lord_12],
                    houses_involved=[1, 12],
                    description=(
                        f"Lagna lord ({lord_1}) in 12th, 12th lord ({lord_12}) in lagna — "
                        "identity colored by loss; expenditure exceeds income"
                    ),
                    effect="malefic",
                )
            )

    # 2nd lord in 8th + 8th lord in 2nd
    lord_2 = get_house_lord(chart, 2)
    lord_8 = get_house_lord(chart, 8)
    if lord_2 != lord_8:
        p2 = chart.planets.get(lord_2)
        p8 = chart.planets.get(lord_8)
        if p2 and p8 and p2.house == 8 and p8.house == 2:
            yogas.append(
                YogaResult(
                    name="Daridra Yoga (2nd-8th Exchange)",
                    name_hindi="दरिद्र योग (द्वितीय-अष्टम परिवर्तन)",
                    is_present=True,
                    planets_involved=[lord_2, lord_8],
                    houses_involved=[2, 8],
                    description=(
                        f"2nd lord ({lord_2}) in 8th, 8th lord ({lord_8}) in 2nd — "
                        "wealth repeatedly disrupted by sudden events"
                    ),
                    effect="malefic",
                )
            )

    # 5th and 9th lords both in dusthana with malefics
    lord_5 = get_house_lord(chart, 5)
    lord_9 = get_house_lord(chart, 9)
    p5 = chart.planets.get(lord_5)
    p9 = chart.planets.get(lord_9)
    _malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
    if p5 and p9 and p5.house in DUSTHANAS and p9.house in DUSTHANAS:
        # Check malefic affliction
        malefics_with_5 = [
            n
            for n, pl in chart.planets.items()
            if n in _malefics and pl.sign_index == p5.sign_index
        ]
        malefics_with_9 = [
            n
            for n, pl in chart.planets.items()
            if n in _malefics and pl.sign_index == p9.sign_index
        ]
        if malefics_with_5 or malefics_with_9:
            yogas.append(
                YogaResult(
                    name="Daridra Yoga (5th-9th Dusthana Affliction)",
                    name_hindi="दरिद्र योग (पञ्चम-नवम दुस्थान)",
                    is_present=True,
                    planets_involved=[lord_5, lord_9],
                    houses_involved=[p5.house, p9.house],
                    description=(
                        f"5th lord ({lord_5}) and 9th lord ({lord_9}) both in dusthana "
                        "with malefic — past merit and fortune both blocked"
                    ),
                    effect="malefic",
                )
            )

    return yogas
