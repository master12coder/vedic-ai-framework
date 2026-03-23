"""Dasha-Transit scoring and favorability — composite scoring algorithm.

Scoring helpers for dasha_transit.py. Not part of the public API.

Source: BPHS Ch.25, Phaladeepika Ch.26.
"""

from __future__ import annotations

from daivai_engine.models.dasha_transit import DashaLordTransit


def compute_score(bav_bindus: int, dignity: str, transit_house: int) -> int:
    """Compute composite 0-100 score for a dasha lord's transit.

    Three components (BPHS Ch.25, Phaladeepika Ch.26):
      - BAV contribution (0-40): higher bindus = stronger transit
      - Dignity contribution (0-30): exalted best, debilitated worst
      - House contribution (0-30): favorable houses score higher

    Args:
        bav_bindus: BAV bindu count (0-8).
        dignity: Transit dignity.
        transit_house: Transit house from lagna (1-12).

    Returns:
        Composite score 0-100.
    """
    # BAV: 0-8 bindus mapped to 0-40
    bav_score = int(bav_bindus * 5)

    # Dignity: exalted=30, own=22, neutral=15, debilitated=5
    dignity_map = {"exalted": 30, "own": 22, "neutral": 15, "debilitated": 5}
    dignity_score = dignity_map.get(dignity, 15)

    # House: kendras and trikonas favorable, dusthanas unfavorable
    if transit_house in {1, 5, 9}:  # trikonas
        house_score = 30
    elif transit_house in {4, 7, 10}:  # kendras (non-lagna)
        house_score = 25
    elif transit_house in {2, 11}:  # wealth houses
        house_score = 22
    elif transit_house == 3:  # upachaya
        house_score = 18
    elif transit_house in {6, 8, 12}:  # dusthanas
        house_score = 8
    else:
        house_score = 15

    return min(100, bav_score + dignity_score + house_score)


def score_to_favorability(score: int) -> str:
    """Convert numeric score to favorability label.

    Args:
        score: Composite score 0-100.

    Returns:
        "favorable" / "neutral" / "unfavorable".
    """
    if score >= 55:
        return "favorable"
    if score >= 35:
        return "neutral"
    return "unfavorable"


def compute_overall_favorability(
    md: DashaLordTransit,
    ad: DashaLordTransit,
    relationship: str,
    active_count: int,
) -> str:
    """Compute overall period favorability from all factors.

    Combines MD score, AD score, their relationship, and double transit
    activation count into a single assessment.

    Args:
        md: MD lord transit analysis.
        ad: AD lord transit analysis.
        relationship: MD-AD natural relationship.
        active_count: Number of double-transit activated dasha houses.

    Returns:
        Overall favorability string.
    """
    # Weighted average: MD=60%, AD=40%
    combined = md.score * 0.6 + ad.score * 0.4

    # Relationship modifier
    rel_mod = {"friends": 10, "neutral": 0, "enemies": -10}
    combined += rel_mod.get(relationship, 0)

    # Double transit activation bonus
    combined += active_count * 5

    if combined >= 70:
        return "highly_favorable"
    if combined >= 55:
        return "favorable"
    if combined >= 40:
        return "mixed"
    if combined >= 25:
        return "challenging"
    return "difficult"


def build_summary(
    md: DashaLordTransit,
    ad: DashaLordTransit,
    relationship: str,
    active_houses: list[int],
    event_domains: list[str],
    overall: str,
) -> str:
    """Build human-readable summary of the dasha-transit analysis.

    Args:
        md: MD lord transit.
        ad: AD lord transit.
        relationship: MD-AD relationship.
        active_houses: Houses activated by both dasha + double transit.
        event_domains: Life domains mapped from active houses.
        overall: Overall favorability label.

    Returns:
        Summary string.
    """
    parts: list[str] = []
    parts.append(
        f"{md.lord} MD ({md.favorability}, BAV {md.bav_bindus}) "
        f"+ {ad.lord} AD ({ad.favorability}, BAV {ad.bav_bindus})"
    )
    parts.append(f"MD-AD: {relationship}")

    if active_houses:
        houses_str = ", ".join(str(h) for h in active_houses)
        parts.append(f"Double transit active on houses: {houses_str}")
    if event_domains:
        parts.append(f"Active domains: {', '.join(event_domains)}")

    parts.append(f"Overall: {overall}")
    return " | ".join(parts)
