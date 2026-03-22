"""Extended Daridra (poverty) Yoga detection from Phaladeepika Ch.12."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import DUSTHANAS
from daivai_engine.models.yoga import YogaResult


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
