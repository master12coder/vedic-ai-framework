"""Extended yoga detection — wealth, spiritual, marriage yogas.

Covers: Wealth yogas (Vasumati, Lakshmi, Saraswati),
Spiritual yogas, Marriage yogas.

Source: BPHS, Phaladeepika, Saravali.
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import (
    DUSTHANAS,
    KENDRAS,
    TRIKONAS,
)
from daivai_engine.models.yoga import YogaResult


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
