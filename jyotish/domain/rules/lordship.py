"""Lordship rules — load from YAML and provide query functions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

import logging

logger = logging.getLogger(__name__)

_lordship_data: dict[str, Any] | None = None
_YAML_PATH = Path(__file__).parent.parent.parent / "knowledge" / "lordship_rules.yaml"


def _load() -> dict[str, Any]:
    """Load and cache lordship rules from YAML."""
    global _lordship_data
    if _lordship_data is not None:
        return _lordship_data
    if _YAML_PATH.exists():
        with open(_YAML_PATH) as f:
            _lordship_data = yaml.safe_load(f) or {}
    else:
        logger.warning("lordship_rules.yaml not found at %s", _YAML_PATH)
        _lordship_data = {}
    return _lordship_data


def get_yogakaraka(lagna: str) -> str | None:
    """Get yogakaraka planet for a lagna.

    Args:
        lagna: Lagna name (e.g., 'Mithuna', 'Mesha')

    Returns:
        Planet name or None if not found.
    """
    data = _load()
    lagna_data = data.get(lagna.lower(), data.get(lagna, {}))
    if isinstance(lagna_data, dict):
        yk = lagna_data.get("yogakaraka", {})
        if isinstance(yk, dict):
            return yk.get("planet")
        return yk
    return None


def get_functional_benefics(lagna: str) -> list[str]:
    """Get functional benefic planets for a lagna."""
    data = _load()
    lagna_data = data.get(lagna.lower(), data.get(lagna, {}))
    if isinstance(lagna_data, dict):
        benefics = lagna_data.get("functional_benefics", [])
        if isinstance(benefics, list):
            return [b.get("planet", b) if isinstance(b, dict) else b for b in benefics]
    return []


def get_functional_malefics(lagna: str) -> list[str]:
    """Get functional malefic planets for a lagna."""
    data = _load()
    lagna_data = data.get(lagna.lower(), data.get(lagna, {}))
    if isinstance(lagna_data, dict):
        malefics = lagna_data.get("functional_malefics", [])
        if isinstance(malefics, list):
            return [m.get("planet", m) if isinstance(m, dict) else m for m in malefics]
    return []


def get_maraka_planets(lagna: str) -> list[dict[str, Any]]:
    """Get maraka planets for a lagna with house numbers and reasoning."""
    data = _load()
    lagna_data = data.get(lagna.lower(), data.get(lagna, {}))
    if isinstance(lagna_data, dict):
        return lagna_data.get("maraka", [])
    return []


def get_gemstone_recommendation(lagna: str, planet: str) -> dict[str, str] | None:
    """Get gemstone recommendation for a planet given a lagna.

    Returns:
        Dict with 'recommendation' (wear/avoid/test/neutral) and 'reasoning'.
    """
    data = _load()
    lagna_data = data.get(lagna.lower(), data.get(lagna, {}))
    if isinstance(lagna_data, dict):
        gems = lagna_data.get("gemstone_recommendations", {})
        return gems.get(planet)
    return None
