"""Helper functions for confidence scoring.

Extracts reusable planet/house assessment logic used by the confidence
scoring module. Keeps the main confidence.py under the 300-line limit.
"""

from __future__ import annotations

from daivai_engine.constants import DUSTHANAS, KENDRAS, SIGN_LORDS, TRIKONAS
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import PlanetData


def planet_in_good_house(planet: PlanetData) -> bool:
    """Check if planet is in kendra or trikona."""
    return planet.house in KENDRAS or planet.house in TRIKONAS


def planet_in_dusthana(planet: PlanetData) -> bool:
    """Check if planet is in 6th, 8th, or 12th house."""
    return planet.house in DUSTHANAS


def is_dignity_strong(planet: PlanetData) -> bool:
    """Check if planet has exalted, own, or mooltrikona dignity."""
    return planet.dignity in {"exalted", "own", "mooltrikona"}


def assess_birth_time(tob: str) -> tuple[str, int, list[str]]:
    """Assess birth-time quality from the time-of-birth string.

    Returns:
        Tuple of (quality_label, score_penalty, caveats).
    """
    if not tob or not tob.strip():
        return "unknown", -30, ["Birth time unknown -- all house-based predictions unreliable."]

    # If time ends in :00 exactly, it's likely rounded/approximate
    stripped = tob.strip()
    if stripped.endswith(":00") and not stripped.endswith(":00:00"):
        return (
            "approximate",
            -15,
            [
                "Birth time ends in :00 -- likely approximate. "
                "Lagna and house cusps may shift. Consider rectification."
            ],
        )

    # HH:MM:SS format with non-zero seconds -> more precise
    return "exact", 0, []


def count_relevant_yogas(analysis: FullChartAnalysis, keywords: list[str]) -> int:
    """Count present yogas whose name matches any of the given keywords."""
    count = 0
    for yoga in analysis.yogas:
        if not yoga.is_present:
            continue
        name_lower = yoga.name.lower()
        if any(kw in name_lower for kw in keywords):
            count += 1
    return count


def get_shadbala_strong(analysis: FullChartAnalysis, planet_name: str) -> bool:
    """Check if a planet passes Shadbala minimum threshold."""
    for sb in analysis.shadbala:
        if sb.planet == planet_name:
            return bool(sb.is_strong)
    return False


def get_vimshopaka_strong(analysis: FullChartAnalysis, planet_name: str, threshold: float) -> bool:
    """Check if a planet's Vimshopaka (shodashavarga) score meets threshold."""
    for vb in analysis.vimshopaka:
        if vb.planet == planet_name:
            return bool(vb.shodashavarga_score >= threshold)
    return False


def get_house_lord(analysis: FullChartAnalysis, house_num: int) -> PlanetData | None:
    """Get the PlanetData for the lord of a given house.

    House N from lagna -> sign at that house -> lord of that sign.
    """
    lagna_idx = analysis.chart.lagna_sign_index
    house_sign_idx = (lagna_idx + house_num - 1) % 12
    lord_name = SIGN_LORDS.get(house_sign_idx)
    if lord_name is None:
        return None
    return analysis.chart.planets.get(lord_name)
