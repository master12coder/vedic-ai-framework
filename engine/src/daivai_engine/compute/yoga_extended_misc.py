"""Extended yoga detection — kartari, conjunction, vipreet, wealth, spiritual, marriage.

Covers: Kartari yogas, Conjunction doshas, Vipreet Raj Yoga,
Nabhasa/Daridra, Wealth yogas (Vasumati, Lakshmi, Saraswati),
Spiritual yogas, Marriage yogas.

Source: BPHS, Phaladeepika, Saravali.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.compute.yoga_nabhasa import detect_nabhasa_yogas
from daivai_engine.constants import (
    DUSTHANAS,
    KENDRAS,
    TRIKONAS,
)
from daivai_engine.models.yoga import YogaResult


_BENEFICS = {"Jupiter", "Venus"}
_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


# ── Kartari Yogas ────────────────────────────────────────────────────────


def detect_kartari_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Shubha and Papa Kartari yogas — BPHS."""
    yogas: list[YogaResult] = []

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


def detect_conjunction_doshas(chart: ChartData) -> list[YogaResult]:
    """Detect Guru Chandal, Shrapit, Grahan, Angarak doshas."""
    yogas: list[YogaResult] = []

    for p1_name, p1 in chart.planets.items():
        for p2_name, p2 in chart.planets.items():
            if p1_name >= p2_name:
                continue
            if p1.sign_index != p2.sign_index:
                continue

            pair = frozenset({p1_name, p2_name})

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


def detect_vipreet_detailed(chart: ChartData) -> list[YogaResult]:
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


def detect_nabhasa_extended(chart: ChartData) -> list[YogaResult]:
    """Detect all 32 Nabhasa (sky pattern) yogas plus Daridra Yoga.

    Delegates to yoga_nabhasa and adds Daridra Yoga (11th lord in dusthana).
    """
    yogas: list[YogaResult] = list(detect_nabhasa_yogas(chart))

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


def detect_wealth_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect additional wealth yogas — Phaladeepika, Saravali."""
    yogas: list[YogaResult] = []

    moon_sign = chart.planets["Moon"].sign_index
    upachaya_signs = {(moon_sign + h - 1) % 12 for h in (3, 6, 10, 11)}
    vasumati_benefics = ("Jupiter", "Venus", "Mercury")
    benefics_in_upachaya = [
        n for n in vasumati_benefics if chart.planets[n].sign_index in upachaya_signs
    ]
    if len(benefics_in_upachaya) >= 2:
        vasu_strength = "full" if len(benefics_in_upachaya) >= 3 else "partial"
        vasu_grade = "Purna" if len(benefics_in_upachaya) >= 3 else "Partial"
        yogas.append(
            YogaResult(
                name="Vasumati Yoga",
                name_hindi="वसुमती योग",
                is_present=True,
                planets_involved=benefics_in_upachaya,
                houses_involved=[3, 6, 10, 11],
                description=(
                    f"{vasu_grade}: {', '.join(benefics_in_upachaya)} in upachaya (3/6/10/11) "
                    "from Moon — enduring wealth, financial security, material abundance"
                ),
                effect="benefic",
                strength=vasu_strength,
            )
        )

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


def detect_spiritual_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect spiritual and renunciation yogas — BPHS."""
    yogas: list[YogaResult] = []

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


def detect_marriage_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect marriage-related yogas — Saravali, Phaladeepika."""
    yogas: list[YogaResult] = []

    venus = chart.planets["Venus"]
    lord_7 = get_house_lord(chart, 7)
    p7 = chart.planets.get(lord_7)

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
