"""Cross-chart validation: D1 (Rashi) vs D9 (Navamsha) consistency.

Compares each planet's dignity across the birth chart and Navamsha to identify
confirmed strengths, hidden weaknesses, Neech Bhanga potential, and vargottam
reinforcement. Source: BPHS Ch.7, Phala Deepika Ch.2, Saravali Ch.33.
"""

from __future__ import annotations

from daivai_engine.constants import (
    DEBILITATION,
    EXALTATION,
    KENDRAS,
    OWN_SIGNS,
    SIGNS,
    TRIKONAS,
)
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.models import CrossChartCheck, CrossChartValidation


# Seven classical planets for cross-chart comparison (exclude shadow planets)
_SEVEN_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Dignity levels ordered from strongest to weakest
_STRONG_DIGNITIES = {"exalted", "mooltrikona", "own"}
_WEAK_DIGNITIES = {"debilitated"}


def _get_d9_sign_index(analysis: FullChartAnalysis, planet_name: str) -> int | None:
    """Extract D9 sign index for a planet from navamsha_positions.

    Returns None if the planet is not found in navamsha data.
    """
    for pos in analysis.navamsha_positions:
        # DivisionalPosition has .planet and .divisional_sign_index attrs,
        # but navamsha_positions is list[Any] so handle both dict and object.
        if isinstance(pos, dict):
            if pos.get("planet") == planet_name:
                return int(pos["divisional_sign_index"])
        elif hasattr(pos, "planet") and pos.planet == planet_name:
            return int(pos.divisional_sign_index)
    return None


def _compute_d9_dignity(planet_name: str, d9_sign_index: int) -> str:
    """Determine a planet's dignity in D9 based on sign placement.

    Uses the same exaltation/debilitation/own-sign tables as D1.
    """
    if EXALTATION.get(planet_name) == d9_sign_index:
        return "exalted"
    if DEBILITATION.get(planet_name) == d9_sign_index:
        return "debilitated"
    if d9_sign_index in OWN_SIGNS.get(planet_name, []):
        return "own"
    return "neutral"


def _classify_pattern(
    planet_name: str,
    d1_dignity: str,
    d9_dignity: str,
    is_vargottam: bool,
    d1_house: int,
) -> tuple[bool, str, str]:
    """Classify the D1-D9 consistency pattern for a planet.

    Returns (is_consistent, pattern_code, explanation).
    """
    d1_strong = d1_dignity in _STRONG_DIGNITIES
    d1_weak = d1_dignity in _WEAK_DIGNITIES
    d9_strong = d9_dignity in _STRONG_DIGNITIES
    d9_weak = d9_dignity in _WEAK_DIGNITIES

    # Vargottam: same sign in D1 and D9 — always a strong confirmer
    if is_vargottam:
        detail = (
            f"with {d1_dignity} dignity — extremely strong"
            if d1_strong
            else "(same sign D1/D9) — D9 reinforces D1"
        )
        return True, "vargottam_strong", f"{planet_name} is vargottam {detail}."

    # Both strong → confirmed (covers own+own, exalted+strong, strong+strong)
    if d1_strong and d9_strong:
        return (
            True,
            "strong_confirmed",
            f"{planet_name} {d1_dignity} in D1 and {d9_dignity} in D9 — confirmed.",
        )

    # Debilitated in D1 but exalted/own in D9 → Neech Bhanga potential
    if d1_weak and d9_strong:
        return (
            True,
            "neech_bhanga_potential",
            f"{planet_name} debilitated in D1 but {d9_dignity} in D9 — Neech Bhanga potential.",
        )
    # Strong in D1 but debilitated in D9 → D1 strength weakened
    if d1_strong and d9_weak:
        return (
            False,
            "d1_weakened",
            f"{planet_name} {d1_dignity} in D1 but debilitated in D9 — strength undercut.",
        )
    # Debilitated in both → weak, no compensation
    if d1_weak and d9_weak:
        return (
            False,
            "mixed",
            f"{planet_name} debilitated in both D1 and D9 — consistently weak.",
        )

    # Both neutral → no strong signal; check house placement
    if not d1_strong and not d9_strong and not d1_weak and not d9_weak:
        if d1_house in KENDRAS or d1_house in TRIKONAS:
            return (
                True,
                "neutral",
                (f"{planet_name} neutral in D1/D9, house {d1_house} (kendra/trikona)."),
            )
        return True, "neutral", f"{planet_name} neutral in both D1 and D9."
    # D1 strong but D9 neutral → partial confirmation
    if d1_strong and not d9_weak:
        return (
            True,
            "neutral",
            (f"{planet_name} {d1_dignity} in D1, neutral in D9 — partial confirmation."),
        )
    # D1 weak, D9 neutral → no compensation
    if d1_weak and not d9_strong:
        return (
            False,
            "mixed",
            (f"{planet_name} debilitated in D1, neutral in D9 — no Neech Bhanga support."),
        )
    # Fallback
    return True, "neutral", f"{planet_name}: D1 {d1_dignity}, D9 {d9_dignity}."


def _build_summary(checks: list[CrossChartCheck], score: float) -> str:
    """Generate a human-readable summary of the cross-chart validation."""
    vargottam = [c.planet for c in checks if c.is_vargottam]
    strong = [c.planet for c in checks if c.pattern == "strong_confirmed"]
    weakened = [c.planet for c in checks if c.pattern == "d1_weakened"]
    neech = [c.planet for c in checks if c.pattern == "neech_bhanga_potential"]

    parts: list[str] = []
    parts.append(f"D1-D9 consistency score: {score:.0%}.")

    if vargottam:
        parts.append(f"Vargottam planets: {', '.join(vargottam)}.")
    if strong:
        parts.append(f"Confirmed strong: {', '.join(strong)}.")
    if neech:
        parts.append(f"Neech Bhanga potential: {', '.join(neech)}.")
    if weakened:
        parts.append(f"D1 strength weakened by D9: {', '.join(weakened)}.")

    if score >= 0.8:
        parts.append("Overall: chart shows high D1-D9 consistency.")
    elif score >= 0.5:
        parts.append("Overall: moderate consistency between D1 and D9.")
    else:
        parts.append("Overall: significant D1-D9 discrepancies detected.")

    return " ".join(parts)


def validate_cross_chart(
    analysis: FullChartAnalysis,
) -> CrossChartValidation:
    """Compare D1 (Rashi) with D9 (Navamsha) for all seven planets.

    For each planet (Sun through Saturn), checks whether the D1 dignity is
    confirmed, contradicted, or shows special patterns in the Navamsha chart.

    Args:
        analysis: Pre-computed FullChartAnalysis containing chart data,
            navamsha_positions, and vargottam_planets.

    Returns:
        CrossChartValidation with per-planet checks and overall score.
    """
    if not analysis.navamsha_positions:
        return CrossChartValidation(
            checks=[],
            consistency_score=0.0,
            vargottam_count=0,
            strong_confirmations=0,
            weakened_count=0,
            neech_bhanga_count=0,
            summary="No Navamsha data available — cross-chart validation skipped.",
        )

    vargottam_set = set(analysis.vargottam_planets)
    checks: list[CrossChartCheck] = []

    for planet_name in _SEVEN_PLANETS:
        planet_data = analysis.chart.planets.get(planet_name)
        if planet_data is None:
            continue

        d9_sign_idx = _get_d9_sign_index(analysis, planet_name)
        if d9_sign_idx is None:
            continue

        d1_sign = SIGNS[planet_data.sign_index]
        d9_sign = SIGNS[d9_sign_idx]
        d1_dignity = planet_data.dignity
        d9_dignity = _compute_d9_dignity(planet_name, d9_sign_idx)
        is_vargottam = planet_name in vargottam_set

        is_consistent, pattern, explanation = _classify_pattern(
            planet_name, d1_dignity, d9_dignity, is_vargottam, planet_data.house
        )

        checks.append(
            CrossChartCheck(
                planet=planet_name,
                d1_sign=d1_sign,
                d1_dignity=d1_dignity,
                d9_sign=d9_sign,
                d9_dignity=d9_dignity,
                is_vargottam=is_vargottam,
                is_consistent=is_consistent,
                pattern=pattern,
                explanation=explanation,
            )
        )

    total = len(checks)
    consistent_count = sum(1 for c in checks if c.is_consistent)
    score = consistent_count / total if total > 0 else 0.0

    vargottam_count = sum(1 for c in checks if c.is_vargottam)
    strong_count = sum(1 for c in checks if c.pattern == "strong_confirmed")
    weakened_count = sum(1 for c in checks if c.pattern == "d1_weakened")
    neech_count = sum(1 for c in checks if c.pattern == "neech_bhanga_potential")

    summary = _build_summary(checks, score)

    return CrossChartValidation(
        checks=checks,
        consistency_score=round(score, 4),
        vargottam_count=vargottam_count,
        strong_confirmations=strong_count,
        weakened_count=weakened_count,
        neech_bhanga_count=neech_count,
        summary=summary,
    )
