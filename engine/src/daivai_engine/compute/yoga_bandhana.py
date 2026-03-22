"""Bandhana (bondage/imprisonment) Yoga detection — BPHS Ch.32."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData, get_house_lord
from daivai_engine.constants import DUSTHANAS, KENDRAS
from daivai_engine.models.yoga import YogaResult


_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}


def _detect_bandhana_yogas(chart: ChartData) -> list[YogaResult]:
    """Detect Bandhana (bondage/imprisonment) Yogas — BPHS Ch.32."""
    yogas: list[YogaResult] = []
    lagna_lord = get_house_lord(chart, 1)
    lord_6 = get_house_lord(chart, 6)
    lord_12 = get_house_lord(chart, 12)
    p_ll = chart.planets.get(lagna_lord)
    p_6 = chart.planets.get(lord_6)
    sat = chart.planets["Saturn"]
    rahu = chart.planets["Rahu"]

    # Rule 1: Lagna lord + 6th lord in kendra with Saturn/Rahu present
    if (
        p_ll
        and p_6
        and p_ll.house in KENDRAS
        and p_6.house in KENDRAS
        and (
            sat.sign_index in (p_ll.sign_index, p_6.sign_index)
            or rahu.sign_index in (p_ll.sign_index, p_6.sign_index)
        )
    ):
        afflictors = []
        if sat.sign_index in (p_ll.sign_index, p_6.sign_index):
            afflictors.append("Saturn")
        if rahu.sign_index in (p_ll.sign_index, p_6.sign_index):
            afflictors.append("Rahu")
        yogas.append(
            YogaResult(
                name="Bandhana Yoga",
                name_hindi="बंधन योग",
                is_present=True,
                planets_involved=[lagna_lord, lord_6, *afflictors],
                houses_involved=[p_ll.house, p_6.house],
                description=(
                    f"Lagna lord ({lagna_lord}) and 6th lord ({lord_6}) "
                    f"in kendra with {', '.join(afflictors)} — bondage, legal troubles"
                ),
                effect="malefic",
            )
        )

    # Rule 3: Mars + Saturn + Rahu all in dusthana
    mars = chart.planets["Mars"]
    if mars.house in DUSTHANAS and sat.house in DUSTHANAS and rahu.house in DUSTHANAS:
        yogas.append(
            YogaResult(
                name="Bandhana Yoga (Triple Malefic Dusthana)",
                name_hindi="बंधन योग (त्रिदोष दुस्थान)",
                is_present=True,
                planets_involved=["Mars", "Saturn", "Rahu"],
                houses_involved=[mars.house, sat.house, rahu.house],
                description="Mars, Saturn, Rahu all in dusthanas — danger of forced confinement",
                effect="malefic",
            )
        )

    # Rule 4: 12th lord + Rahu aspecting lagna
    p_12 = chart.planets.get(lord_12)
    if p_12 and p_12.sign_index == rahu.sign_index:
        # Check if this conjunction aspects lagna
        conj_house = p_12.house
        lagna_from_conj = ((chart.lagna_sign_index - p_12.sign_index) % 12) + 1
        if lagna_from_conj == 7:  # 7th aspect
            yogas.append(
                YogaResult(
                    name="Bandhana Yoga (12th Lord-Rahu on Lagna)",
                    name_hindi="बंधन योग (द्वादशेश-राहु लग्न दृष्टि)",
                    is_present=True,
                    planets_involved=[lord_12, "Rahu"],
                    houses_involved=[conj_house],
                    description=(
                        f"12th lord ({lord_12}) conjunct Rahu aspecting lagna — "
                        "isolation and confinement energy attacks the self"
                    ),
                    effect="malefic",
                )
            )

    return yogas
