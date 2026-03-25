"""Gemstone weight penalty for planets conjunct malefic influences.

When a recommended planet (e.g., Lagnesh) conjuncts Rahu, 6th lord, 8th lord,
or 12th lord, the gemstone amplifies ALL conjunct energies — not just the
target planet.  This module computes a penalty factor (0.0-1.0) to reduce
the recommended stone weight.

Source: BV Raman, *How to Judge a Horoscope* Vol.II — stone activation
risk from malefic conjunction partners.
"""

from __future__ import annotations

from daivai_engine.compute.chart import are_conjunct, get_house_lord
from daivai_engine.models.chart import ChartData
from daivai_engine.models.family_bond import ConjunctionPenalty


# Penalty factors by conjunct partner type.  1.0 = no penalty.
_PENALTY_RAHU = 0.65  # Rahu amplifies obsession / shadow qualities
_PENALTY_KETU = 0.70  # Ketu amplifies detachment / sudden events
_PENALTY_6L = 0.75  # 6th lord = enemies, disease, debt
_PENALTY_8L = 0.70  # 8th lord = sudden events, surgery, accident
_PENALTY_12L = 0.75  # 12th lord = expenditure, loss, foreign lands

# The minimum aggregate penalty factor (floor).
_MIN_PENALTY = 0.50


def compute_conjunction_penalty(chart: ChartData, planet: str) -> ConjunctionPenalty:
    """Check if *planet* conjuncts Rahu, Ketu, 6L, 8L, or 12L and compute penalty.

    The penalty factor is multiplicative: if the planet conjuncts both Rahu
    (0.65) and 12L (0.75) the combined factor is 0.65 * 0.75 = ~0.49, floored
    at 0.50.

    Args:
        chart: Computed birth chart.
        planet: The planet whose gemstone weight we are adjusting.

    Returns:
        ConjunctionPenalty with has_penalty, penalty_factor, conjunct list,
        and reasoning.
    """
    conjunct_with: list[str] = []
    factor = 1.0

    # Check shadow planets
    for shadow, pen in [("Rahu", _PENALTY_RAHU), ("Ketu", _PENALTY_KETU)]:
        if shadow != planet and are_conjunct(chart, planet, shadow):
            conjunct_with.append(shadow)
            factor *= pen

    # Check dusthana lords (6, 8, 12)
    dusthana_map = {6: _PENALTY_6L, 8: _PENALTY_8L, 12: _PENALTY_12L}
    seen_lords: set[str] = set()

    for house, pen in dusthana_map.items():
        lord = get_house_lord(chart, house)
        if lord == planet or lord in seen_lords:
            continue
        seen_lords.add(lord)
        if are_conjunct(chart, planet, lord):
            conjunct_with.append(f"{lord} ({house}L)")
            factor *= pen

    factor = max(factor, _MIN_PENALTY)
    has_penalty = factor < 1.0

    if has_penalty:
        reasoning = (
            f"{planet} conjuncts {', '.join(conjunct_with)} → "
            f"reduce stone weight to {factor:.0%} of base recommendation."
        )
    else:
        reasoning = f"{planet} has no malefic conjunction partners."

    return ConjunctionPenalty(
        planet=planet,
        has_penalty=has_penalty,
        penalty_factor=round(factor, 2),
        conjunct_with=conjunct_with,
        reasoning=reasoning,
    )
