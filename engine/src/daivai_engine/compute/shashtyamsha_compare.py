"""D1 vs D60 cross-validation helpers for Shashtyamsha analysis.

BPHS rule: 'If D1 and D60 agree, the result is certain.'

Source: BPHS Ch.6 Shashtyamsha Adhyaya.
"""

from __future__ import annotations

from daivai_engine.constants import PLANETS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.shashtyamsha import D1D60Comparison, D1D60ComparisonResult, D60Analysis


__all__ = [
    "compare_d1_d60",
]

# D1 dignities that map to "benefic" for comparison purposes
_BENEFIC_DIGNITIES = {"exalted", "mooltrikona", "own", "friend"}
_MALEFIC_DIGNITIES = {"debilitated", "enemy"}


def _assess_d1(dignity: str) -> str:
    """Convert a planet's D1 dignity to benefic/malefic/neutral assessment."""
    if dignity in _BENEFIC_DIGNITIES:
        return "benefic"
    if dignity in _MALEFIC_DIGNITIES:
        return "malefic"
    return "neutral"


def _assess_d60(nature: str) -> str:
    """Normalise Shashtyamsha deity nature to benefic/malefic/mixed."""
    match nature:
        case "Saumya":
            return "benefic"
        case "Krura":
            return "malefic"
        case _:
            return "mixed"


def _build_comparison_summary(
    certain_benefics: list[str],
    certain_malefics: list[str],
    conflicting: list[str],
) -> str:
    """Compose a one-paragraph D1-D60 agreement summary."""
    parts: list[str] = []
    if certain_benefics:
        parts.append(f"Certain benefics (D1+D60 agree): {', '.join(certain_benefics)}")
    if certain_malefics:
        parts.append(f"Certain malefics (D1+D60 agree): {', '.join(certain_malefics)}")
    if conflicting:
        parts.append(f"Uncertain (D1-D60 conflict): {', '.join(conflicting)}")
    total = len(certain_benefics) + len(certain_malefics)
    parts.append(
        f"{total} of 9 planets show D1-D60 agreement — "
        "those give the most predictable and certain results"
    )
    return ". ".join(parts) + "."


def compare_d1_d60(chart: ChartData, d60_analysis: D60Analysis) -> D1D60ComparisonResult:
    """Cross-validate D1 and D60 for all planets per the BPHS rule.

    BPHS states: 'If D1 and D60 agree, the result is certain.'
    This function checks agreement for each planet:
      - D1 benefic + D60 Saumya → certain benefic
      - D1 malefic + D60 Krura  → certain malefic
      - Disagreement             → uncertain result

    Args:
        chart: Computed birth chart.
        d60_analysis: D60Analysis result from analyze_d60_chart.

    Returns:
        D1D60ComparisonResult with per-planet comparisons and summary.
    """
    positions_by_planet = {pos.planet: pos for pos in d60_analysis.planets}

    comparisons: list[D1D60Comparison] = []
    certain_benefics: list[str] = []
    certain_malefics: list[str] = []
    conflicting: list[str] = []

    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        pos = positions_by_planet[planet_name]

        d1_val = _assess_d1(p.dignity)
        d60_val = _assess_d60(pos.deity.nature)

        agree = (d1_val == "benefic" and d60_val == "benefic") or (
            d1_val == "malefic" and d60_val == "malefic"
        )
        certainty = "certain" if agree else "uncertain"

        if agree and d1_val == "benefic":
            certain_benefics.append(planet_name)
            interpretation = (
                f"{planet_name} is benefic in D1 ({p.dignity}) and in D60 "
                f"({pos.deity.name}, {pos.deity.nature}) — result CERTAIN to be good"
            )
        elif agree and d1_val == "malefic":
            certain_malefics.append(planet_name)
            interpretation = (
                f"{planet_name} is malefic in D1 ({p.dignity}) and in D60 "
                f"({pos.deity.name}, {pos.deity.nature}) — result CERTAIN to be difficult"
            )
        else:
            conflicting.append(planet_name)
            interpretation = (
                f"{planet_name} is {d1_val} in D1 ({p.dignity}) but "
                f"{d60_val} in D60 ({pos.deity.name}, {pos.deity.nature}) — "
                "result uncertain; context and dasha timing determine outcome"
            )

        comparisons.append(
            D1D60Comparison(
                planet=planet_name,
                d1_assessment=d1_val,
                d60_assessment=pos.deity.nature,
                agreement=agree,
                certainty=certainty,
                interpretation=interpretation,
            )
        )

    summary = _build_comparison_summary(certain_benefics, certain_malefics, conflicting)

    return D1D60ComparisonResult(
        comparisons=comparisons,
        certain_benefics=certain_benefics,
        certain_malefics=certain_malefics,
        conflicting=conflicting,
        summary=summary,
    )
