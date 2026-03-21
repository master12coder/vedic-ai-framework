"""D60 Shashtyamsha deity analysis — the 'most telling chart' per BPHS.

Implements:
  - Deity lookup from shashtyamsha_data.yaml (60 divisions of 0.5° each)
  - Full D60 chart analysis for all planets
  - D1 vs D60 cross-validation (if both agree, result is certain)

Odd-sign rule (BPHS Ch.6):
  ODD signs (Mesha, Mithuna, Simha, Tula, Dhanu, Kumbha):
    Deities run 1→60 in forward order (part 0 = deity 1)
  EVEN signs (Vrishabha, Karka, Kanya, Vrischika, Makara, Meena):
    Deities run 60→1 in reverse order (part 0 = deity 60)

Key BPHS rule:
  "If D1 and D60 agree, the result is certain."
  Planet in benefic Shashtyamsha → gives good results even if otherwise afflicted.
  Planet in malefic Shashtyamsha → gives trouble even if otherwise well-placed.

Source: BPHS Ch.6 Shashtyamsha Adhyaya.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from daivai_engine.compute.divisional import compute_shashtyamsha_sign
from daivai_engine.constants import PLANETS, SIGN_LORDS, SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.shashtyamsha import (
    D1D60Comparison,
    D1D60ComparisonResult,
    D60Analysis,
    ShashtyamshaDeity,
    ShashtyamshaPosition,
)


_DATA_FILE = Path(__file__).parent.parent / "knowledge" / "shashtyamsha_data.yaml"

# D1 dignities that map to "benefic" for comparison purposes
_BENEFIC_DIGNITIES = {"exalted", "mooltrikona", "own", "friend"}
_MALEFIC_DIGNITIES = {"debilitated", "enemy"}


@lru_cache(maxsize=1)
def _load_deities() -> list[ShashtyamshaDeity]:
    """Load all 60 Shashtyamsha deities from YAML (cached)."""
    with _DATA_FILE.open() as fh:
        data: dict = yaml.safe_load(fh)  # type: ignore[assignment]
    return [ShashtyamshaDeity(**entry) for entry in data["deities"]]


def _get_deity_for_part(sign_index: int, part: int) -> ShashtyamshaDeity:
    """Return the presiding deity for a given sign and part (0-59).

    Odd signs (0-indexed even) use forward order 1-60.
    Even signs (0-indexed odd) use reverse order 60-1.

    Args:
        sign_index: D1 sign index (0=Mesha … 11=Meena)
        part: 0-based division index within the sign (0-59)

    Returns:
        ShashtyamshaDeity for that position.
    """
    deities = _load_deities()
    if sign_index % 2 == 0:  # Odd signs (Aries, Gemini, … — 0-indexed even)
        deity_index = part  # deity 1 = part 0, deity 60 = part 59
    else:  # Even signs (Taurus, Cancer, … — 0-indexed odd)
        deity_index = 59 - part  # deity 60 = part 0, deity 1 = part 59
    return deities[deity_index]


def get_d60_position(planet_longitude: float, planet_name: str = "") -> ShashtyamshaPosition:
    """Map a planet's sidereal longitude to its D60 Shashtyamsha position.

    Determines which of the 60 Shashtyamsha deities the planet falls in,
    the D60 sign it occupies, and whether it is vargottam.

    Args:
        planet_longitude: Sidereal longitude (0-360°).
        planet_name: Optional planet name for labelling.

    Returns:
        ShashtyamshaPosition with full deity, sign, and lordship data.
    """
    d1_sign_index = int(planet_longitude / 30.0)
    degree_in_sign = planet_longitude - d1_sign_index * 30.0
    part = int(degree_in_sign / 0.5)
    if part > 59:
        part = 59

    d60_sign_index = compute_shashtyamsha_sign(planet_longitude)
    deity = _get_deity_for_part(d1_sign_index, part)

    return ShashtyamshaPosition(
        planet=planet_name,
        longitude=planet_longitude,
        d1_sign_index=d1_sign_index,
        d1_sign=SIGNS[d1_sign_index],
        d60_sign_index=d60_sign_index,
        d60_sign=SIGNS[d60_sign_index],
        d60_lord=SIGN_LORDS[d60_sign_index],
        part=part,
        deity=deity,
        is_vargottam=(d1_sign_index == d60_sign_index),
    )


def analyze_d60_chart(chart: ChartData) -> D60Analysis:
    """Compute full D60 Shashtyamsha analysis for all planets in a chart.

    For each planet, identifies the presiding Shashtyamsha deity and
    classifies it as Saumya (benefic), Krura (malefic), or Mishra (mixed).
    Planets in benefic Shashtyamshas give good results despite other afflictions;
    planets in malefic Shashtyamshas create trouble despite good placement.

    Args:
        chart: Computed birth chart with all planet longitudes.

    Returns:
        D60Analysis with per-planet positions and summary classifications.
    """
    positions: list[ShashtyamshaPosition] = []
    benefic: list[str] = []
    malefic: list[str] = []
    mixed: list[str] = []
    vargottam: list[str] = []

    for planet_name in PLANETS:
        p = chart.planets[planet_name]
        pos = get_d60_position(p.longitude, planet_name)
        positions.append(pos)

        match pos.deity.nature:
            case "Saumya":
                benefic.append(planet_name)
            case "Krura":
                malefic.append(planet_name)
            case "Mishra":
                mixed.append(planet_name)

        if pos.is_vargottam:
            vargottam.append(planet_name)

    findings = _build_findings(positions, benefic, malefic, vargottam)

    return D60Analysis(
        planets=positions,
        benefic_planets=benefic,
        malefic_planets=malefic,
        mixed_planets=mixed,
        vargottam_planets=vargottam,
        key_findings=findings,
    )


def _build_findings(
    positions: list[ShashtyamshaPosition],
    benefic: list[str],
    malefic: list[str],
    vargottam: list[str],
) -> list[str]:
    """Derive key textual findings from D60 positions."""
    findings: list[str] = []

    if vargottam:
        findings.append(
            f"Vargottam in D60 (D1=D60 sign): {', '.join(vargottam)} — "
            "extraordinary karmic continuity, results extremely consistent"
        )

    for pos in positions:
        findings.append(
            f"{pos.planet}: {pos.deity.name} ({pos.deity.nature}) in {pos.d60_sign}"
            f" — {pos.deity.signification.split(';')[0]}"
        )

    if benefic:
        findings.append(
            f"Planets in benefic Shashtyamsha: {', '.join(benefic)} — "
            "give good results even when otherwise afflicted"
        )
    if malefic:
        findings.append(
            f"Planets in malefic Shashtyamsha: {', '.join(malefic)} — "
            "create trouble even when otherwise well-placed"
        )

    return findings


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


def compare_d1_d60(chart: ChartData) -> D1D60ComparisonResult:
    """Cross-validate D1 and D60 for all planets per the BPHS rule.

    BPHS states: 'If D1 and D60 agree, the result is certain.'
    This function checks agreement for each planet:
      - D1 benefic + D60 Saumya → certain benefic
      - D1 malefic + D60 Krura  → certain malefic
      - Disagreement             → uncertain result

    Args:
        chart: Computed birth chart.

    Returns:
        D1D60ComparisonResult with per-planet comparisons and summary.
    """
    d60 = analyze_d60_chart(chart)
    positions_by_planet = {pos.planet: pos for pos in d60.planets}

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
