"""Yoga detection engine — 30+ Vedic yogas."""

from __future__ import annotations


from jyotish.utils.constants import (
    KENDRAS, TRIKONAS, DUSTHANAS, SIGN_LORDS, PLANETS,
    EXALTATION, OWN_SIGNS,
)
from jyotish.compute.chart import ChartData, get_house_lord, get_planets_in_house, has_aspect
from jyotish.domain.models.yoga import YogaResult


def _is_in_kendra(house: int) -> bool:
    return house in KENDRAS


def _is_in_trikona(house: int) -> bool:
    return house in TRIKONAS


def _is_in_own_or_exalted(planet_name: str, sign_index: int) -> bool:
    if planet_name in EXALTATION and EXALTATION[planet_name] == sign_index:
        return True
    if planet_name in OWN_SIGNS and sign_index in OWN_SIGNS[planet_name]:
        return True
    return False


def _planet_in_kendra_from_reference(chart: ChartData, planet: str, ref_planet: str) -> bool:
    """Check if planet is in kendra (1/4/7/10) from reference planet."""
    p_sign = chart.planets[planet].sign_index
    ref_sign = chart.planets[ref_planet].sign_index
    distance = ((p_sign - ref_sign) % 12) + 1
    return distance in KENDRAS


def detect_all_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all yogas in a chart."""
    yogas: list[YogaResult] = []

    yogas.extend(_detect_panch_mahapurush(chart))
    yogas.extend(_detect_raj_yogas(chart))
    yogas.extend(_detect_dhan_yogas(chart))
    yogas.extend(_detect_other_yogas(chart))

    return yogas


def _detect_panch_mahapurush(chart: ChartData) -> list[YogaResult]:
    """Detect the 5 Panch Mahapurush Yogas."""
    yogas = []

    checks = [
        ("Jupiter", "Hamsa", "हंस योग",
         "Jupiter in own/exalted sign in kendra — wisdom, spirituality, fame"),
        ("Venus", "Malavya", "मालव्य योग",
         "Venus in own/exalted sign in kendra — luxury, beauty, artistic talent"),
        ("Saturn", "Sasa", "शश योग",
         "Saturn in own/exalted sign in kendra — authority, discipline, power"),
        ("Mars", "Ruchaka", "रुचक योग",
         "Mars in own/exalted sign in kendra — courage, leadership, military success"),
        ("Mercury", "Bhadra", "भद्र योग",
         "Mercury in own/exalted sign in kendra — intelligence, eloquence, commerce"),
    ]

    for planet, name, name_hi, desc in checks:
        p = chart.planets[planet]
        if _is_in_kendra(p.house) and _is_in_own_or_exalted(planet, p.sign_index):
            yogas.append(YogaResult(
                name=name,
                name_hindi=name_hi,
                is_present=True,
                planets_involved=[planet],
                houses_involved=[p.house],
                description=desc,
                effect="benefic",
            ))

    return yogas


def _detect_raj_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Raj Yogas — kendra lord + trikona lord connections."""
    yogas = []

    # Get lords of kendras and trikonas
    kendra_lords = set()
    trikona_lords = set()
    for h in KENDRAS:
        kendra_lords.add(get_house_lord(chart, h))
    for h in TRIKONAS:
        trikona_lords.add(get_house_lord(chart, h))

    # Planets that own both kendra and trikona (yogakaraka)
    yogakaraka_planets = kendra_lords & trikona_lords
    # Remove Lagna lord from kendra-trikona overlap check as it's always both
    # but we still want to report it
    for yk in yogakaraka_planets:
        p = chart.planets.get(yk)
        if p and (p.dignity in ("exalted", "own", "mooltrikona") or _is_in_kendra(p.house)):
            yogas.append(YogaResult(
                name="Yogakaraka Raj Yoga",
                name_hindi="योगकारक राज योग",
                is_present=True,
                planets_involved=[yk],
                houses_involved=[p.house],
                description=f"{yk} owns both kendra and trikona — powerful raj yoga",
                effect="benefic",
            ))

    # Conjunction of kendra lord + trikona lord
    kendra_only = kendra_lords - trikona_lords
    trikona_only = trikona_lords - kendra_lords
    for kl in kendra_only:
        for tl in trikona_only:
            if kl == tl:
                continue
            kp = chart.planets.get(kl)
            tp = chart.planets.get(tl)
            if kp and tp and kp.sign_index == tp.sign_index:
                yogas.append(YogaResult(
                    name="Raj Yoga",
                    name_hindi="राज योग",
                    is_present=True,
                    planets_involved=[kl, tl],
                    houses_involved=[kp.house],
                    description=f"Kendra lord {kl} conjunct trikona lord {tl}",
                    effect="benefic",
                ))

    # 9th lord + 10th lord conjunction
    lord_9 = get_house_lord(chart, 9)
    lord_10 = get_house_lord(chart, 10)
    if lord_9 != lord_10:
        p9 = chart.planets.get(lord_9)
        p10 = chart.planets.get(lord_10)
        if p9 and p10 and p9.sign_index == p10.sign_index:
            yogas.append(YogaResult(
                name="Dharma Karmadhipati Yoga",
                name_hindi="धर्म कर्माधिपति योग",
                is_present=True,
                planets_involved=[lord_9, lord_10],
                houses_involved=[9, 10, p9.house],
                description=f"9th lord ({lord_9}) conjunct 10th lord ({lord_10}) — fortune meets action",
                effect="benefic",
            ))

    return yogas


def _detect_dhan_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect wealth yogas."""
    yogas = []

    # 2nd lord + 11th lord conjunction
    lord_2 = get_house_lord(chart, 2)
    lord_11 = get_house_lord(chart, 11)
    if lord_2 != lord_11:
        p2 = chart.planets.get(lord_2)
        p11 = chart.planets.get(lord_11)
        if p2 and p11 and p2.sign_index == p11.sign_index:
            yogas.append(YogaResult(
                name="Dhan Yoga (2-11)",
                name_hindi="धन योग",
                is_present=True,
                planets_involved=[lord_2, lord_11],
                houses_involved=[2, 11],
                description=f"2nd lord ({lord_2}) conjunct 11th lord ({lord_11}) — wealth accumulation",
                effect="benefic",
            ))

    # 5th lord + 9th lord conjunction
    lord_5 = get_house_lord(chart, 5)
    lord_9 = get_house_lord(chart, 9)
    if lord_5 != lord_9:
        p5 = chart.planets.get(lord_5)
        p9 = chart.planets.get(lord_9)
        if p5 and p9 and p5.sign_index == p9.sign_index:
            yogas.append(YogaResult(
                name="Dhan Yoga (5-9)",
                name_hindi="धन योग (५-९)",
                is_present=True,
                planets_involved=[lord_5, lord_9],
                houses_involved=[5, 9],
                description=f"5th lord ({lord_5}) conjunct 9th lord ({lord_9}) — purva punya wealth",
                effect="benefic",
            ))

    # Jupiter in 2nd or 11th in good dignity
    jup = chart.planets["Jupiter"]
    if jup.house in (2, 11) and jup.dignity in ("exalted", "own", "mooltrikona"):
        yogas.append(YogaResult(
            name="Dhan Yoga (Jupiter)",
            name_hindi="धन योग (बृहस्पति)",
            is_present=True,
            planets_involved=["Jupiter"],
            houses_involved=[jup.house],
            description=f"Jupiter in {jup.house}th house in {jup.dignity} dignity — natural wealth indicator",
            effect="benefic",
        ))

    return yogas


def _detect_other_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect other important yogas."""
    yogas = []

    # Gajakesari: Jupiter in kendra from Moon
    if _planet_in_kendra_from_reference(chart, "Jupiter", "Moon"):
        yogas.append(YogaResult(
            name="Gajakesari Yoga",
            name_hindi="गजकेसरी योग",
            is_present=True,
            planets_involved=["Jupiter", "Moon"],
            houses_involved=[chart.planets["Jupiter"].house, chart.planets["Moon"].house],
            description="Jupiter in kendra from Moon — wisdom, fame, long life, leadership",
            effect="benefic",
        ))

    # Budhaditya: Sun-Mercury conjunction
    sun = chart.planets["Sun"]
    mercury = chart.planets["Mercury"]
    if sun.sign_index == mercury.sign_index:
        yogas.append(YogaResult(
            name="Budhaditya Yoga",
            name_hindi="बुधादित्य योग",
            is_present=True,
            planets_involved=["Sun", "Mercury"],
            houses_involved=[sun.house],
            description="Sun-Mercury conjunction — intelligence, analytical mind, communication",
            effect="benefic",
        ))

    # Chandra-Mangal: Moon-Mars conjunction
    moon = chart.planets["Moon"]
    mars = chart.planets["Mars"]
    if moon.sign_index == mars.sign_index:
        yogas.append(YogaResult(
            name="Chandra-Mangal Yoga",
            name_hindi="चन्द्र-मंगल योग",
            is_present=True,
            planets_involved=["Moon", "Mars"],
            houses_involved=[moon.house],
            description="Moon-Mars conjunction — courage, wealth through effort, emotional strength",
            effect="benefic",
        ))

    # Vipreet Raj Yoga: 6th/8th/12th lord in another dusthana
    for h in DUSTHANAS:
        lord = get_house_lord(chart, h)
        p = chart.planets.get(lord)
        if p and p.house in DUSTHANAS and p.house != h:
            yogas.append(YogaResult(
                name="Vipreet Raj Yoga",
                name_hindi="विपरीत राज योग",
                is_present=True,
                planets_involved=[lord],
                houses_involved=[h, p.house],
                description=f"{h}th lord ({lord}) in {p.house}th house — rise through adversity",
                effect="mixed",
            ))

    # Neech Bhanga Raj Yoga: debilitated planet with cancellation
    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        if p.dignity == "debilitated":
            # Check cancellation conditions
            debil_sign_lord = SIGN_LORDS[p.sign_index]
            dsl = chart.planets.get(debil_sign_lord)
            cancelled = False
            reason = ""

            # Condition 1: Lord of debilitation sign in kendra from lagna
            if dsl and _is_in_kendra(dsl.house):
                cancelled = True
                reason = f"Lord of debilitation sign ({debil_sign_lord}) in kendra"

            # Condition 2: Lord of debilitation sign in kendra from Moon
            if dsl and _planet_in_kendra_from_reference(chart, debil_sign_lord, "Moon"):
                cancelled = True
                reason = f"Lord of debilitation sign ({debil_sign_lord}) in kendra from Moon"

            # Condition 3: Debilitated planet exaltation lord in kendra
            if planet_name in EXALTATION:
                exalt_sign = EXALTATION[planet_name]
                exalt_lord = SIGN_LORDS[exalt_sign]
                el = chart.planets.get(exalt_lord)
                if el and _is_in_kendra(el.house):
                    cancelled = True
                    reason = f"Exaltation lord ({exalt_lord}) in kendra"

            if cancelled:
                yogas.append(YogaResult(
                    name="Neech Bhanga Raj Yoga",
                    name_hindi="नीच भंग राज योग",
                    is_present=True,
                    planets_involved=[planet_name],
                    houses_involved=[p.house],
                    description=f"Debilitated {planet_name} with cancellation: {reason}",
                    effect="benefic",
                ))

    # Kemdrum Dosha: no planet in 2nd/12th from Moon
    moon_sign = moon.sign_index
    sign_before = (moon_sign - 1) % 12
    sign_after = (moon_sign + 1) % 12
    has_planet_adjacent = False
    for pname in ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p = chart.planets[pname]
        if p.sign_index in (sign_before, sign_after):
            has_planet_adjacent = True
            break
    if not has_planet_adjacent:
        yogas.append(YogaResult(
            name="Kemdrum Yoga",
            name_hindi="केमद्रुम योग",
            is_present=True,
            planets_involved=["Moon"],
            houses_involved=[moon.house],
            description="No planet in 2nd or 12th from Moon — loneliness, financial fluctuations",
            effect="malefic",
        ))

    # Saraswati Yoga: Jupiter, Venus, Mercury in kendra/trikona
    jup = chart.planets["Jupiter"]
    ven = chart.planets["Venus"]
    mer = chart.planets["Mercury"]
    kendra_trikona = set(KENDRAS) | set(TRIKONAS)
    if (jup.house in kendra_trikona and ven.house in kendra_trikona
            and mer.house in kendra_trikona):
        yogas.append(YogaResult(
            name="Saraswati Yoga",
            name_hindi="सरस्वती योग",
            is_present=True,
            planets_involved=["Jupiter", "Venus", "Mercury"],
            houses_involved=[jup.house, ven.house, mer.house],
            description="Jupiter, Venus, Mercury in kendra/trikona — learning, wisdom, arts",
            effect="benefic",
        ))

    # Amala Yoga: natural benefic in 10th from lagna
    planets_in_10 = get_planets_in_house(chart, 10)
    natural_benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    for p in planets_in_10:
        if p.name in natural_benefics:
            yogas.append(YogaResult(
                name="Amala Yoga",
                name_hindi="अमल योग",
                is_present=True,
                planets_involved=[p.name],
                houses_involved=[10],
                description=f"Natural benefic {p.name} in 10th house — virtuous reputation, clean livelihood",
                effect="benefic",
            ))
            break

    # Adhi Yoga: benefics in 6th/7th/8th from Moon
    moon_house = moon.house
    adhi_houses = [
        ((moon_house - 1 + 5) % 12) + 1,
        ((moon_house - 1 + 6) % 12) + 1,
        ((moon_house - 1 + 7) % 12) + 1,
    ]
    benefics_in_adhi = []
    for pname in ["Jupiter", "Venus", "Mercury"]:
        p = chart.planets[pname]
        if p.house in adhi_houses:
            benefics_in_adhi.append(pname)
    if len(benefics_in_adhi) >= 2:
        yogas.append(YogaResult(
            name="Adhi Yoga",
            name_hindi="अधि योग",
            is_present=True,
            planets_involved=benefics_in_adhi,
            houses_involved=adhi_houses,
            description="Benefics in 6th/7th/8th from Moon — leadership, authority, wealth",
            effect="benefic",
        ))

    # Lakshmi Yoga: 9th lord in own/exalted in kendra
    lord_9 = get_house_lord(chart, 9)
    p9 = chart.planets.get(lord_9)
    if p9 and _is_in_kendra(p9.house) and _is_in_own_or_exalted(lord_9, p9.sign_index):
        yogas.append(YogaResult(
            name="Lakshmi Yoga",
            name_hindi="लक्ष्मी योग",
            is_present=True,
            planets_involved=[lord_9],
            houses_involved=[9, p9.house],
            description=f"9th lord ({lord_9}) in own/exalted in kendra — fortune, prosperity, divine grace",
            effect="benefic",
        ))

    return yogas
