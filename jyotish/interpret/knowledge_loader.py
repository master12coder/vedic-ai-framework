"""Knowledge loader — loads lordship rules, gemstone logic, and scripture
citations from YAML files and the scripture database for prompt injection."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from jyotish.compute.chart import ChartData
from jyotish.scriptures import scripture_db
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)

_KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"

_lordship_cache: dict[str, Any] | None = None
_gemstone_cache: dict[str, Any] | None = None


def reset_caches() -> None:
    """Clear all cached knowledge data. Call between tests."""
    global _lordship_cache, _gemstone_cache
    _lordship_cache = None
    _gemstone_cache = None



def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML knowledge file."""
    path = _KNOWLEDGE_DIR / filename
    if not path.exists():
        logger.warning("Knowledge file not found: %s", path)
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_lordship_data() -> dict[str, Any]:
    """Load and cache lordship rules."""
    global _lordship_cache
    if _lordship_cache is None:
        _lordship_cache = _load_yaml("lordship_rules.yaml")
    return _lordship_cache


def get_gemstone_data() -> dict[str, Any]:
    """Load and cache gemstone logic."""
    global _gemstone_cache
    if _gemstone_cache is None:
        _gemstone_cache = _load_yaml("gemstone_logic.yaml")
    return _gemstone_cache


def build_lordship_context(lagna_sign: str) -> dict[str, Any]:
    """Build lordship context for this specific lagna from YAML rules.

    Returns a dict with keys: sign_lord, yogakaraka, functional_benefics,
    functional_malefics, maraka, house_lords, recommended_stones,
    prohibited_stones, test_stones, gemstone_recommendations.
    """
    lordship_data = get_lordship_data()
    lagna_key = lagna_sign.lower()
    lagna_rules = lordship_data.get("lagnas", {}).get(lagna_key, {})

    if not lagna_rules:
        logger.warning("No lordship rules for lagna: %s", lagna_sign)
        return {}

    # Build recommended / prohibited / test stone lists
    gem_recs = lagna_rules.get("gemstone_recommendations", {})
    recommended_stones: list[dict[str, str]] = []
    prohibited_stones: list[dict[str, str]] = []
    test_stones: list[dict[str, str]] = []

    for planet, info in gem_recs.items():
        rec = info.get("recommendation", "neutral")
        stone = info.get("gemstone", "Unknown")
        reasoning = info.get("reasoning", "").strip()
        entry = {"planet": planet, "stone": stone, "reasoning": reasoning}
        if rec == "wear":
            recommended_stones.append(entry)
        elif rec == "avoid":
            prohibited_stones.append(entry)
        elif rec == "test":
            test_stones.append(entry)

    # Format maraka entries with readable house strings
    maraka_raw = lagna_rules.get("maraka", [])
    maraka_formatted: list[dict[str, Any]] = []
    for m in maraka_raw:
        houses = m.get("houses", [])
        house_labels = {
            2: "2nd (maraka sthana)",
            7: "7th (maraka sthana)",
        }
        house_str = " + ".join(
            house_labels.get(h, f"{h}th") for h in houses
        )
        maraka_formatted.append({
            "planet": m.get("planet", ""),
            "houses": houses,
            "house_str": house_str,
            "reasoning": m.get("reasoning", "").strip(),
        })

    return {
        "sign_lord": lagna_rules.get("sign_lord", ""),
        "yogakaraka": lagna_rules.get("yogakaraka", {}),
        "functional_benefics": lagna_rules.get("functional_benefics", []),
        "functional_malefics": lagna_rules.get("functional_malefics", []),
        "maraka": maraka_formatted,
        "house_lords": lagna_rules.get("house_lords", {}),
        "gemstone_recommendations": gem_recs,
        "recommended_stones": recommended_stones,
        "prohibited_stones": prohibited_stones,
        "test_stones": test_stones,
    }


def build_gemstone_context() -> dict[str, Any]:
    """Load gemstone_logic.yaml context for prompt injection."""
    data = get_gemstone_data()
    return {
        "gemstone_data": data.get("gemstones", {}),
        "contraindications": data.get("contraindications", []),
        "decision_framework": data.get("decision_framework", {}),
        "planetary_friendships": data.get("planetary_friendships", {}),
    }


def build_scripture_context(chart: ChartData) -> list[str]:
    """Load relevant scripture citations for each planet in this chart."""
    citations: list[str] = []
    for planet_name, planet in chart.planets.items():
        refs = scripture_db.query_by_planet(planet_name, planet.house)
        for ref in refs[:2]:  # Top 2 per planet to control prompt size
            citations.append(scripture_db.get_citation(ref))
    return citations
