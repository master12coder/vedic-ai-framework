"""Extended yoga detection — 70+ additional yogas beyond the basic set.

Covers: Nabhasa yogas, lunar yogas, solar yogas, Neech Bhanga,
Kartari yogas, Daridra yogas, marriage yogas, spiritual yogas.

Source: BPHS, Phaladeepika, Saravali.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.compute.yoga_nabhasa import detect_nabhasa_yogas
from daivai_engine.constants import (
    DEBILITATION,
    DUSTHANAS,
    EXALTATION,
    KENDRAS,
    SIGN_LORDS,
    TRIKONAS,
)
from daivai_engine.models.yoga import YogaResult


_BENEFICS = {"Jupiter", "Venus"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def detect_extended_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect 70+ additional yogas beyond the basic Panch Mahapurush/Raj/Dhan set.

    Args:
        chart: Computed birth chart.

    Returns:
        List of YogaResult for all detected yogas.
    """
    yogas: list[YogaResult] = []
    yogas.extend(_detect_lunar_yogas(chart))
    yogas.extend(_detect_solar_yogas(chart))
    yogas.extend(_detect_neech_bhanga(chart))
    yogas.extend(_detect_kartari_yogas(chart))
    yogas.extend(_detect_conjunction_doshas(chart))
    yogas.extend(_detect_vipreet_detailed(chart))
    yogas.extend(_detect_nabhasa_yogas(chart))
    yogas.extend(_detect_wealth_yogas(chart))
    yogas.extend(_detect_spiritual_yogas(chart))
    yogas.extend(_detect_marriage_yogas(chart))
    return yogas


# ── Lunar Yogas (from Moon) ──────────────────────────────────────────────


def _detect_lunar_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect yogas based on Moon's position — Phaladeepika Ch.7."""
    yogas: list[YogaResult] = []
    moon = chart.planets["Moon"]
    moon_sign = moon.sign_index

    # Planets in 2nd and 12th from Moon
    sign_2nd = (moon_sign + 1) % 12
    sign_12th = (moon_sign - 1) % 12
    in_2nd = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_2nd and n not in ("Rahu", "Ketu", "Moon")
    ]
    in_12th = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_12th and n not in ("Rahu", "Ketu", "Moon")
    ]

    # Sunapha: planet in 2nd from Moon (not Sun) — Phaladeepika 7.1
    sunapha_planets = [p for p in in_2nd if p != "Sun"]
    if sunapha_planets:
        yogas.append(
            YogaResult(
                name="Sunapha Yoga",
                name_hindi="सुनफा योग",
                is_present=True,
                planets_involved=sunapha_planets,
                houses_involved=[],
                description=f"{', '.join(sunapha_planets)} in 2nd from Moon — self-made wealth, good reputation",
                effect="benefic",
            )
        )

    # Anapha: planet in 12th from Moon (not Sun) — Phaladeepika 7.2
    anapha_planets = [p for p in in_12th if p != "Sun"]
    if anapha_planets:
        yogas.append(
            YogaResult(
                name="Anapha Yoga",
                name_hindi="अनफा योग",
                is_present=True,
                planets_involved=anapha_planets,
                houses_involved=[],
                description=f"{', '.join(anapha_planets)} in 12th from Moon — generous, expressive personality",
                effect="benefic",
            )
        )

    # Durudhura: planets in BOTH 2nd and 12th from Moon — Phaladeepika 7.3
    if sunapha_planets and anapha_planets:
        yogas.append(
            YogaResult(
                name="Durudhura Yoga",
                name_hindi="दुरुधुरा योग",
                is_present=True,
                planets_involved=sunapha_planets + anapha_planets,
                houses_involved=[],
                description="Planets on both sides of Moon — wealth, vehicles, fame, generous nature",
                effect="benefic",
            )
        )

    # Shakata: Jupiter in 6/8/12 from Moon — Phaladeepika 7.12
    jup = chart.planets["Jupiter"]
    jup_from_moon = ((jup.sign_index - moon_sign) % 12) + 1
    if jup_from_moon in (6, 8, 12):
        yogas.append(
            YogaResult(
                name="Shakata Yoga",
                name_hindi="शकट योग",
                is_present=True,
                planets_involved=["Jupiter", "Moon"],
                houses_involved=[jup_from_moon],
                description=f"Jupiter in {jup_from_moon}th from Moon — ups and downs in fortune, unstable wealth",
                effect="malefic",
            )
        )

    # Amala: benefic in 10th from Moon or Lagna — Phaladeepika 7.14
    sign_10_from_moon = (moon_sign + 9) % 12
    sign_10_from_lagna = (chart.lagna_sign_index + 9) % 12
    for name, p in chart.planets.items():
        if name in _BENEFICS and (
            p.sign_index == sign_10_from_moon or p.sign_index == sign_10_from_lagna
        ):
            yogas.append(
                YogaResult(
                    name="Amala Yoga",
                    name_hindi="अमल योग",
                    is_present=True,
                    planets_involved=[name],
                    houses_involved=[10],
                    description=f"{name} in 10th — spotless reputation, ethical conduct, fame through good deeds",
                    effect="benefic",
                )
            )
            break

    # Adhi: benefics in 6/7/8 from Moon — BPHS
    sign_6 = (moon_sign + 5) % 12
    sign_7 = (moon_sign + 6) % 12
    sign_8 = (moon_sign + 7) % 12
    adhi_benefics = [
        n
        for n, p in chart.planets.items()
        if n in _BENEFICS and p.sign_index in (sign_6, sign_7, sign_8)
    ]
    if len(adhi_benefics) >= 2:
        yogas.append(
            YogaResult(
                name="Adhi Yoga",
                name_hindi="अधि योग",
                is_present=True,
                planets_involved=adhi_benefics,
                houses_involved=[6, 7, 8],
                description="Multiple benefics in 6/7/8 from Moon — leadership, minister-level power",
                effect="benefic",
            )
        )

    return yogas


# ── Solar Yogas ──────────────────────────────────────────────────────────


def _detect_solar_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect yogas based on Sun's position — Phaladeepika Ch.8."""
    yogas: list[YogaResult] = []
    sun = chart.planets["Sun"]
    sun_sign = sun.sign_index

    # Veshi: planet (not Moon) in 2nd from Sun — Phaladeepika 8.1
    sign_2nd = (sun_sign + 1) % 12
    veshi = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_2nd and n not in ("Moon", "Rahu", "Ketu", "Sun")
    ]
    if veshi:
        yogas.append(
            YogaResult(
                name="Veshi Yoga",
                name_hindi="वेशी योग",
                is_present=True,
                planets_involved=veshi,
                houses_involved=[],
                description=f"{', '.join(veshi)} in 2nd from Sun — eloquent, learned, wealthy",
                effect="benefic" if any(v in _BENEFICS for v in veshi) else "mixed",
            )
        )

    # Voshi: planet (not Moon) in 12th from Sun — Phaladeepika 8.2
    sign_12th = (sun_sign - 1) % 12
    voshi = [
        n
        for n, p in chart.planets.items()
        if p.sign_index == sign_12th and n not in ("Moon", "Rahu", "Ketu", "Sun")
    ]
    if voshi:
        yogas.append(
            YogaResult(
                name="Voshi Yoga",
                name_hindi="वोशी योग",
                is_present=True,
                planets_involved=voshi,
                houses_involved=[],
                description=f"{', '.join(voshi)} in 12th from Sun — charitable, skilled, influential",
                effect="benefic" if any(v in _BENEFICS for v in voshi) else "mixed",
            )
        )

    # Ubhayachari: planets on BOTH sides of Sun — Phaladeepika 8.3
    if veshi and voshi:
        yogas.append(
            YogaResult(
                name="Ubhayachari Yoga",
                name_hindi="उभयचरी योग",
                is_present=True,
                planets_involved=veshi + voshi,
                houses_involved=[],
                description="Planets flanking Sun — kingly status, balanced personality, eloquent",
                effect="benefic",
            )
        )

    return yogas


# ── Neech Bhanga Raj Yoga ────────────────────────────────────────────────


def _detect_neech_bhanga(chart: ChartData) -> list[YogaResult]:
    """Detect Neech Bhanga (debilitation cancellation) — BPHS Ch.28."""
    yogas: list[YogaResult] = []

    for name, p in chart.planets.items():
        if name in ("Rahu", "Ketu"):
            continue
        if DEBILITATION.get(name) != p.sign_index:
            continue

        cancellation_reasons: list[str] = []

        # Rule 1: debilitation lord in kendra from Lagna or Moon
        debil_sign_lord = SIGN_LORDS[p.sign_index]
        lord_planet = chart.planets.get(debil_sign_lord)
        if lord_planet:
            lord_from_lagna = ((lord_planet.sign_index - chart.lagna_sign_index) % 12) + 1
            lord_from_moon = ((lord_planet.sign_index - chart.planets["Moon"].sign_index) % 12) + 1
            if lord_from_lagna in KENDRAS:
                cancellation_reasons.append(
                    f"Debilitation lord {debil_sign_lord} in kendra from Lagna"
                )
            if lord_from_moon in KENDRAS:
                cancellation_reasons.append(
                    f"Debilitation lord {debil_sign_lord} in kendra from Moon"
                )

        # Rule 2: exaltation lord of the debilitated planet in kendra
        exalt_sign = EXALTATION.get(name)
        if exalt_sign is not None:
            exalt_lord = SIGN_LORDS[exalt_sign]
            el_planet = chart.planets.get(exalt_lord)
            if el_planet:
                el_from_lagna = ((el_planet.sign_index - chart.lagna_sign_index) % 12) + 1
                if el_from_lagna in KENDRAS:
                    cancellation_reasons.append(f"Exaltation lord {exalt_lord} in kendra")

        # Rule 3: debilitated planet itself in kendra
        if p.house in KENDRAS:
            cancellation_reasons.append(f"{name} debilitated but in kendra house {p.house}")

        if cancellation_reasons:
            yogas.append(
                YogaResult(
                    name="Neech Bhanga Raj Yoga",
                    name_hindi="नीच भंग राज योग",
                    is_present=True,
                    planets_involved=[name],
                    houses_involved=[p.house],
                    description=f"{name} debilitated but cancelled: {'; '.join(cancellation_reasons)}",
                    effect="benefic",
                )
            )

    return yogas


# ── Kartari Yogas ────────────────────────────────────────────────────────


def _detect_kartari_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Shubha and Papa Kartari yogas — BPHS."""
    yogas: list[YogaResult] = []

    # Check each house for hemming
    for house in range(1, 13):
        house_sign = (chart.lagna_sign_index + house - 1) % 12
        sign_before = (house_sign - 1) % 12
        sign_after = (house_sign + 1) % 12

        planets_before = {n for n, p in chart.planets.items() if p.sign_index == sign_before}
        planets_after = {n for n, p in chart.planets.items() if p.sign_index == sign_after}

        benefics_before = planets_before & _BENEFICS
        benefics_after = planets_after & _BENEFICS
        malefics_before = planets_before & _MALEFICS
        malefics_after = planets_after & _MALEFICS

        if benefics_before and benefics_after:
            yogas.append(
                YogaResult(
                    name=f"Shubha Kartari (H{house})",
                    name_hindi="शुभ कर्तरी योग",
                    is_present=True,
                    planets_involved=list(benefics_before | benefics_after),
                    houses_involved=[house],
                    description=f"House {house} hemmed by benefics — protection and growth for this house",
                    effect="benefic",
                )
            )

        if malefics_before and malefics_after:
            yogas.append(
                YogaResult(
                    name=f"Papa Kartari (H{house})",
                    name_hindi="पाप कर्तरी योग",
                    is_present=True,
                    planets_involved=list(malefics_before | malefics_after),
                    houses_involved=[house],
                    description=f"House {house} hemmed by malefics — restriction and challenges for this house",
                    effect="malefic",
                )
            )

    return yogas


# ── Conjunction-Based Doshas ─────────────────────────────────────────────


def _detect_conjunction_doshas(chart: ChartData) -> list[YogaResult]:
    """Detect Guru Chandal, Shrapit, Grahan, Angarak doshas."""
    yogas: list[YogaResult] = []

    # Build same-sign pairs
    for p1_name, p1 in chart.planets.items():
        for p2_name, p2 in chart.planets.items():
            if p1_name >= p2_name:
                continue
            if p1.sign_index != p2.sign_index:
                continue

            pair = frozenset({p1_name, p2_name})

            # Guru Chandal: Jupiter + Rahu — BPHS
            if pair == frozenset({"Jupiter", "Rahu"}):
                yogas.append(
                    YogaResult(
                        name="Guru Chandal Yoga",
                        name_hindi="गुरु चण्डाल योग",
                        is_present=True,
                        planets_involved=["Jupiter", "Rahu"],
                        houses_involved=[p1.house],
                        description="Jupiter conjunct Rahu — wisdom clouded by illusions, unconventional beliefs",
                        effect="malefic",
                    )
                )

            # Shrapit Dosha: Saturn + Rahu — Phaladeepika
            if pair == frozenset({"Saturn", "Rahu"}):
                yogas.append(
                    YogaResult(
                        name="Shrapit Dosha",
                        name_hindi="शापित दोष",
                        is_present=True,
                        planets_involved=["Saturn", "Rahu"],
                        houses_involved=[p1.house],
                        description="Saturn conjunct Rahu — karmic debts from past life, delays and obstacles",
                        effect="malefic",
                    )
                )

            # Angarak Dosha: Mars + Rahu — traditional
            if pair == frozenset({"Mars", "Rahu"}):
                yogas.append(
                    YogaResult(
                        name="Angarak Yoga",
                        name_hindi="अंगारक योग",
                        is_present=True,
                        planets_involved=["Mars", "Rahu"],
                        houses_involved=[p1.house],
                        description="Mars conjunct Rahu — aggression amplified, accident-prone, sudden events",
                        effect="malefic",
                    )
                )

            # Grahan Dosha: Sun or Moon with Rahu/Ketu — BPHS
            if pair & {"Sun", "Moon"} and pair & {"Rahu", "Ketu"}:
                luminary = "Sun" if "Sun" in pair else "Moon"
                node = "Rahu" if "Rahu" in pair else "Ketu"
                yogas.append(
                    YogaResult(
                        name="Grahan Yoga",
                        name_hindi="ग्रहण योग",
                        is_present=True,
                        planets_involved=[luminary, node],
                        houses_involved=[p1.house],
                        description=f"{luminary} conjunct {node} — eclipse-like effect, identity/emotional challenges",
                        effect="malefic",
                    )
                )

    return yogas


# ── Vipreet Raj Yoga (detailed) ──────────────────────────────────────────


def _detect_vipreet_detailed(chart: ChartData) -> list[YogaResult]:
    """Detect all 3 types of Vipreet Raj Yoga — BPHS Ch.37."""
    yogas: list[YogaResult] = []
    lord_6 = get_house_lord(chart, 6)
    lord_8 = get_house_lord(chart, 8)
    lord_12 = get_house_lord(chart, 12)

    for lord, name, lord_house in [
        (lord_6, "Harsha", 6),
        (lord_8, "Sarala", 8),
        (lord_12, "Vimala", 12),
    ]:
        p = chart.planets.get(lord)
        if p and p.house in DUSTHANAS:
            yogas.append(
                YogaResult(
                    name=f"{name} Vipreet Raj Yoga",
                    name_hindi=f"{name} विपरीत राज योग",
                    is_present=True,
                    planets_involved=[lord],
                    houses_involved=[lord_house, p.house],
                    description=f"{lord_house}th lord ({lord}) in dusthana house {p.house} — rise through adversity",
                    effect="mixed",
                )
            )

    return yogas


# ── Nabhasa Yogas (pattern-based) ────────────────────────────────────────


def _detect_nabhasa_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect all 32 Nabhasa (sky pattern) yogas — delegates to yoga_nabhasa.

    Also detects Daridra Yoga (11th lord in dusthana), which is a traditional
    poverty yoga kept separate from the BPHS Ch.13 Nabhasa system.
    """
    yogas: list[YogaResult] = list(detect_nabhasa_yogas(chart))

    # Daridra: lord of 11th in 6/8/12 — poverty yoga (not a BPHS Nabhasa yoga)
    lord_11 = get_house_lord(chart, 11)
    p11 = chart.planets.get(lord_11)
    if p11 and p11.house in DUSTHANAS:
        yogas.append(
            YogaResult(
                name="Daridra Yoga",
                name_hindi="दरिद्र योग",
                is_present=True,
                planets_involved=[lord_11],
                houses_involved=[11, p11.house],
                description=f"11th lord ({lord_11}) in dusthana house {p11.house} — financial struggles",
                effect="malefic",
            )
        )

    return yogas


# ── Additional Wealth Yogas ──────────────────────────────────────────────


def _detect_wealth_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect additional wealth yogas — Phaladeepika, Saravali."""
    yogas: list[YogaResult] = []

    # Vasumati: benefics in upachaya (3,6,10,11) from Moon — Phaladeepika
    moon_sign = chart.planets["Moon"].sign_index
    upachaya_signs = {(moon_sign + h - 1) % 12 for h in (3, 6, 10, 11)}
    benefics_in_upachaya = [
        n for n, p in chart.planets.items() if n in _BENEFICS and p.sign_index in upachaya_signs
    ]
    if len(benefics_in_upachaya) >= 2:
        yogas.append(
            YogaResult(
                name="Vasumati Yoga",
                name_hindi="वसुमती योग",
                is_present=True,
                planets_involved=benefics_in_upachaya,
                houses_involved=[3, 6, 10, 11],
                description="Benefics in upachaya from Moon — enduring wealth, financial security",
                effect="benefic",
            )
        )

    # Lakshmi: 9th lord strong + Venus in own/exalted in kendra/trikona
    lord_9 = get_house_lord(chart, 9)
    p9 = chart.planets.get(lord_9)
    venus = chart.planets["Venus"]
    if (
        p9
        and p9.house in KENDRAS + TRIKONAS[1:]
        and venus.dignity in ("exalted", "own", "mooltrikona")
        and venus.house in KENDRAS + TRIKONAS[1:]
    ):
        yogas.append(
            YogaResult(
                name="Lakshmi Yoga",
                name_hindi="लक्ष्मी योग",
                is_present=True,
                planets_involved=[lord_9, "Venus"],
                houses_involved=[9, venus.house],
                description="9th lord strong + Venus dignified — blessed by Lakshmi, lasting prosperity",
                effect="benefic",
            )
        )

    # Saraswati: Jupiter/Venus/Mercury in kendra/trikona in dignity — BPHS
    jup = chart.planets["Jupiter"]
    merc = chart.planets["Mercury"]
    good_positions = KENDRAS + TRIKONAS[1:]
    saras_count = sum(
        1
        for p in (jup, venus, merc)
        if p.house in good_positions and p.dignity in ("exalted", "own", "mooltrikona")
    )
    if saras_count >= 2:
        yogas.append(
            YogaResult(
                name="Saraswati Yoga",
                name_hindi="सरस्वती योग",
                is_present=True,
                planets_involved=["Jupiter", "Venus", "Mercury"],
                houses_involved=[],
                description="Jupiter/Venus/Mercury strong — learning, arts, wisdom, eloquence",
                effect="benefic",
            )
        )

    return yogas


# ── Spiritual Yogas ──────────────────────────────────────────────────────


def _detect_spiritual_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect spiritual and renunciation yogas — BPHS."""
    yogas: list[YogaResult] = []

    # Pravrajya: 4+ planets in one sign including lord of 10th — BPHS
    sign_planets: dict[int, list[str]] = {}
    for n, p in chart.planets.items():
        if n in ("Rahu", "Ketu"):
            continue
        sign_planets.setdefault(p.sign_index, []).append(n)

    lord_10 = get_house_lord(chart, 10)
    for _sign, planets in sign_planets.items():
        if len(planets) >= 4 and lord_10 in planets:
            yogas.append(
                YogaResult(
                    name="Pravrajya Yoga",
                    name_hindi="प्रवज्या योग",
                    is_present=True,
                    planets_involved=planets,
                    houses_involved=[],
                    description=f"{len(planets)} planets with 10th lord in one sign — renunciation, spiritual path",
                    effect="mixed",
                )
            )

    # Ketu in 12th or 9th in good dignity — moksha indicator
    ketu = chart.planets["Ketu"]
    if ketu.house in (9, 12):
        yogas.append(
            YogaResult(
                name="Moksha Yoga (Ketu)",
                name_hindi="मोक्ष योग",
                is_present=True,
                planets_involved=["Ketu"],
                houses_involved=[ketu.house],
                description=f"Ketu in house {ketu.house} — spiritual liberation, detachment, past-life merit",
                effect="mixed",
            )
        )

    return yogas


# ── Marriage Yogas ───────────────────────────────────────────────────────


def _detect_marriage_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect marriage-related yogas — Saravali, Phaladeepika."""
    yogas: list[YogaResult] = []

    venus = chart.planets["Venus"]
    lord_7 = get_house_lord(chart, 7)
    p7 = chart.planets.get(lord_7)

    # Early marriage: Venus + 7th lord in kendra/trikona, strong
    if (
        p7
        and p7.house in KENDRAS + TRIKONAS[1:]
        and venus.house in KENDRAS + TRIKONAS[1:]
        and venus.dignity in ("exalted", "own", "mooltrikona", "neutral")
    ):
        yogas.append(
            YogaResult(
                name="Early Marriage Yoga",
                name_hindi="शीघ्र विवाह योग",
                is_present=True,
                planets_involved=["Venus", lord_7],
                houses_involved=[7],
                description="Venus and 7th lord well-placed — marriage in favorable dasha period",
                effect="benefic",
            )
        )

    # Delayed marriage: 7th lord in 6/8/12 or Saturn aspects 7th
    if p7 and p7.house in DUSTHANAS:
        yogas.append(
            YogaResult(
                name="Delayed Marriage",
                name_hindi="विवाह विलम्ब योग",
                is_present=True,
                planets_involved=[lord_7],
                houses_involved=[7, p7.house],
                description=f"7th lord ({lord_7}) in dusthana {p7.house} — marriage may be delayed",
                effect="malefic",
            )
        )

    return yogas
