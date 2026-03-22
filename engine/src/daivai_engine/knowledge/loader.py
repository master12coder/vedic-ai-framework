"""YAML knowledge loading with caching."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)

_KNOWLEDGE_DIR = Path(__file__).parent
_cache: dict[str, dict[str, Any]] = {}


def _load_yaml(filename: str) -> dict[str, Any]:
    """Load a YAML file from the knowledge directory with caching."""
    if filename in _cache:
        return _cache[filename]

    filepath = _KNOWLEDGE_DIR / filename
    if not filepath.exists():
        logger.warning("Knowledge file not found: %s", filepath)
        return {}

    with open(filepath) as f:
        data = yaml.safe_load(f) or {}

    _cache[filename] = data
    return data


def load_lordship_rules() -> dict[str, Any]:
    """Load per-lagna lordship rules."""
    return _load_yaml("lordship_rules.yaml")


def load_gemstone_logic() -> dict[str, Any]:
    """Load gemstone contraindication rules."""
    return _load_yaml("gemstone_logic.yaml")


def load_yoga_definitions() -> dict[str, Any]:
    """Load yoga definitions."""
    return _load_yaml("yoga_definitions.yaml")


def load_remedy_rules() -> dict[str, Any]:
    """Load remedy rules."""
    return _load_yaml("remedy_rules.yaml")


def load_weekly_routine() -> dict[str, Any]:
    """Load weekly routine mapping."""
    return _load_yaml("weekly_routine.yaml")


def load_vastu_rules() -> dict[str, Any]:
    """Load Vastu Shastra directional mappings, mandala zones, and dosha rules."""
    return _load_yaml("vastu_rules.yaml")


def load_namakarana_rules() -> dict[str, Any]:
    """Load Namakarana (naming ceremony) rules — 108 aksharas + muhurta rules."""
    return _load_yaml("namakarana_rules.yaml")


def reload() -> None:
    """Clear cache and force reload."""
    global _cache
    _cache = {}
