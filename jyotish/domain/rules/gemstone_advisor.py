"""Gemstone recommendation engine with contraindication logic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

import logging

logger = logging.getLogger(__name__)

_gemstone_data: dict[str, Any] | None = None
_YAML_PATH = Path(__file__).parent.parent.parent / "knowledge" / "gemstone_logic.yaml"


def reset_gemstone_cache() -> None:
    """Clear cached gemstone data."""
    global _gemstone_data
    _gemstone_data = None


@dataclass
class GemstoneRecommendation:
    """A gemstone recommendation with full details."""
    planet: str
    stone_name: str
    stone_name_hi: str
    recommendation: str  # wear, avoid, test, neutral
    reasoning: str
    finger: str
    hand: str
    metal: str
    day: str
    mantra: str
    contraindications: list[str]


def _load() -> dict[str, Any]:
    """Load and cache gemstone data from YAML."""
    global _gemstone_data
    if _gemstone_data is not None:
        return _gemstone_data
    if _YAML_PATH.exists():
        with open(_YAML_PATH) as f:
            _gemstone_data = yaml.safe_load(f) or {}
    else:
        logger.warning("gemstone_logic.yaml not found at %s", _YAML_PATH)
        _gemstone_data = {}
    return _gemstone_data


def get_gemstone_info(planet: str) -> dict[str, Any]:
    """Get gemstone info for a planet."""
    data = _load()
    return data.get("gemstones", {}).get(planet, {})


def get_contraindications() -> list[str]:
    """Get all gemstone contraindication rules."""
    data = _load()
    return data.get("contraindications", [])


def check_compatibility(stone1_planet: str, stone2_planet: str) -> bool:
    """Check if two gemstones can be worn together.

    Returns:
        True if compatible, False if contraindicated.
    """
    data = _load()
    enemies = data.get("planetary_friendships", {}).get("enemies", {})
    planet1_enemies = enemies.get(stone1_planet, [])
    planet2_enemies = enemies.get(stone2_planet, [])
    return stone2_planet not in planet1_enemies and stone1_planet not in planet2_enemies


def recommend_gemstone(
    planet: str,
    is_functional_benefic: bool,
    is_yogakaraka: bool = False,
    is_maraka: bool = False,
    dignity: str = "neutral",
) -> GemstoneRecommendation:
    """Generate a gemstone recommendation based on chart context.

    Args:
        planet: Planet name
        is_functional_benefic: Is this planet a functional benefic for the lagna
        is_yogakaraka: Is this the yogakaraka planet
        is_maraka: Is this a maraka planet
        dignity: Planet's dignity (exalted/own/mooltrikona/neutral/debilitated)
    """
    info = get_gemstone_info(planet)
    primary = info.get("primary", {})

    if is_yogakaraka:
        rec = "wear"
        reasoning = f"{planet} is yogakaraka — always safe to strengthen"
    elif is_maraka and dignity == "debilitated":
        rec = "avoid"
        reasoning = f"{planet} is maraka and debilitated — wearing may activate death-inflicting house"
    elif is_functional_benefic:
        rec = "wear"
        reasoning = f"{planet} is a functional benefic — strengthening is beneficial"
    elif dignity == "debilitated":
        rec = "test"
        reasoning = f"{planet} is debilitated — trial for 3 days before committing"
    elif is_maraka:
        rec = "avoid"
        reasoning = f"{planet} is a maraka planet — avoid strengthening"
    else:
        rec = "neutral"
        reasoning = f"{planet} has mixed lordship — consult for specific chart analysis"

    return GemstoneRecommendation(
        planet=planet,
        stone_name=primary.get("name_en", "Unknown"),
        stone_name_hi=primary.get("name_hi", ""),
        recommendation=rec,
        reasoning=reasoning,
        finger=info.get("finger", ""),
        hand=info.get("hand", "Right"),
        metal=info.get("metal", ""),
        day=info.get("day", ""),
        mantra=info.get("mantra", ""),
        contraindications=get_contraindications(),
    )
