"""Wealth flow classification — earner, accumulator, distributor, or mixed.

Analyses the 2nd lord (stored wealth / family), 10th lord (career / karma
income), and 11th lord (gains / profit) placements to classify a native's
financial archetype.  This is used in Family Bond Kundali to determine
which family member should manage finances vs. focus on income growth.

Source: Traditional Parashari house-signification analysis.
"""

from __future__ import annotations

from daivai_engine.compute.chart import get_house_lord, get_planet_house
from daivai_engine.constants.houses import DUSTHANAS, KENDRAS, TRIKONAS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.family_bond import WealthFlowProfile


# Houses where wealth lords retain or grow money
_ACCUMULATE_HOUSES = set(KENDRAS) | set(TRIKONAS) | {2, 11}

# 12th house = vyay (expenditure) — money flows out
_FLOW_HOUSE = 12

# Per-factor scores (max 100 total)
_HOUSE_SCORE: dict[str, float] = {
    "accumulate": 30.0,  # lord in kendra/trikona/2/11
    "flow": 5.0,  # lord in 12th
    "dusthana": 10.0,  # lord in 6/8/12
    "neutral": 18.0,  # any other house
}


def classify_wealth_flow(chart: ChartData) -> WealthFlowProfile:
    """Classify a person's financial archetype from chart indicators.

    Checks where the 2nd, 10th, and 11th lords sit and scores each
    placement.  High score → accumulator archetype.  Low score (lords
    in 12th / dusthanas) → distributor archetype.

    Args:
        chart: Computed birth chart.

    Returns:
        WealthFlowProfile with archetype, lord placements, score, and
        descriptive text.
    """
    second_lord = get_house_lord(chart, 2)
    tenth_lord = get_house_lord(chart, 10)
    eleventh_lord = get_house_lord(chart, 11)

    second_house = get_planet_house(chart, second_lord)
    tenth_house = get_planet_house(chart, tenth_lord)
    eleventh_house = get_planet_house(chart, eleventh_lord)

    placements = [
        (second_lord, second_house, "2nd"),
        (tenth_lord, tenth_house, "10th"),
        (eleventh_lord, eleventh_house, "11th"),
    ]

    score = 0.0
    flow_count = 0
    accum_count = 0
    reasons: list[str] = []

    for lord, house, label in placements:
        if house == _FLOW_HOUSE:
            score += _HOUSE_SCORE["flow"]
            flow_count += 1
            reasons.append(f"{label}L ({lord}) in 12th (vyay)")
        elif house in DUSTHANAS:
            score += _HOUSE_SCORE["dusthana"]
            reasons.append(f"{label}L ({lord}) in {house}th (dusthana)")
        elif house in _ACCUMULATE_HOUSES:
            score += _HOUSE_SCORE["accumulate"]
            accum_count += 1
            reasons.append(f"{label}L ({lord}) in {house}th (kendra/trikona/wealth)")
        else:
            score += _HOUSE_SCORE["neutral"]
            reasons.append(f"{label}L ({lord}) in {house}th")

    archetype = _determine_archetype(flow_count, accum_count)
    description = _build_description(archetype, reasons)

    return WealthFlowProfile(
        name=chart.name,
        archetype=archetype,
        second_lord=second_lord,
        second_lord_house=second_house,
        tenth_lord=tenth_lord,
        tenth_lord_house=tenth_house,
        eleventh_lord=eleventh_lord,
        eleventh_lord_house=eleventh_house,
        wealth_score=round(score, 1),
        description=description,
    )


def _determine_archetype(flow_count: int, accum_count: int) -> str:
    """Determine archetype from placement counts."""
    if flow_count >= 2:
        return "distributor"
    if accum_count >= 2:
        return "accumulator"
    if flow_count >= 1 and accum_count >= 1:
        return "mixed"
    if flow_count == 1:
        return "distributor"
    if accum_count == 1:
        return "mixed"
    return "mixed"


def _build_description(archetype: str, reasons: list[str]) -> str:
    """Build a human-readable description."""
    detail = "; ".join(reasons)
    labels = {
        "earner": "Strong income potential — wealth comes easily but must be managed.",
        "accumulator": "Natural saver — money sticks and grows over time.",
        "distributor": "Wealth flows through — earns well but spends or distributes freely.",
        "mixed": "Mixed wealth pattern — needs conscious financial discipline.",
    }
    return f"{labels.get(archetype, '')} [{detail}]"
