"""Gem therapy computation — professional-grade Vedic gem therapy engine.

Computes complete gemstone recommendations including:
- Lordship-based stone selection per lagna
- Wearing protocol: finger, metal, day, nakshatra, mantra
- Weight formula per body weight
- Substitute (upratna) and quality specifications
- Pran Pratishtha (activation ritual) data
- Contraindication matrix (which gems must never be worn together)
- Auspicious wearing muhurta computation using Panchang

All computation stays in engine/ — zero AI, zero product imports.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.gem_therapy_core import compute_gem_recommendation
from daivai_engine.compute.gem_therapy_muhurta import compute_wearing_muhurta
from daivai_engine.knowledge.loader import load_gem_therapy_rules
from daivai_engine.models.gem_therapy import (
    ContraindicationPair,
    ContraindicationResult,
)


__all__ = [
    "check_gem_contraindications",
    "compute_gem_recommendation",
    "compute_wearing_muhurta",
]


def check_gem_contraindications(gems: list[str]) -> ContraindicationResult:
    """Check a list of gems (stone names or planet names) for contraindications.

    Args:
        gems: List of stone names (e.g., ["Emerald", "Yellow Sapphire"]) or
              planet names (e.g., ["Mercury", "Jupiter"]).

    Returns:
        ContraindicationResult with all conflicting pairs and safe combinations.
    """
    rules = load_gem_therapy_rules()
    stone_to_planet = rules.get("stone_to_planet", {})
    planet_to_stone = rules.get("planet_to_stone", {})
    pairs_data: list[dict[str, Any]] = rules.get("contraindication_pairs", [])

    # Normalize all inputs to stone names
    normalized: list[str] = []
    for gem in gems:
        if gem in planet_to_stone:
            normalized.append(planet_to_stone[gem])
        elif gem in stone_to_planet:
            normalized.append(gem)
        else:
            normalized.append(gem)

    conflicts: list[ContraindicationPair] = []
    safe_pairs: list[tuple[str, str]] = []

    for i in range(len(normalized)):
        for j in range(i + 1, len(normalized)):
            stone_a = normalized[i]
            stone_b = normalized[j]
            conflict = _find_conflict(
                stone_a, stone_b, pairs_data, stone_to_planet, planet_to_stone
            )
            if conflict:
                conflicts.append(conflict)
            else:
                safe_pairs.append((stone_a, stone_b))

    has_absolute = any(c.severity == "absolute" for c in conflicts)
    summary = _build_contraindication_summary(conflicts, normalized)

    return ContraindicationResult(
        gems_checked=normalized,
        conflicts=conflicts,
        safe_pairs=safe_pairs,
        has_absolute_conflict=has_absolute,
        summary=summary,
    )


def _find_conflict(
    stone_a: str,
    stone_b: str,
    pairs_data: list[dict[str, Any]],
    stone_to_planet: dict[str, str],
    planet_to_stone: dict[str, str],
) -> ContraindicationPair | None:
    """Check if two stones have a contraindication pair entry."""
    planet_a = stone_to_planet.get(stone_a, stone_a)
    planet_b = stone_to_planet.get(stone_b, stone_b)

    for pair in pairs_data:
        pair_planets: list[str] = pair.get("planets", [])
        if set(pair_planets) == {planet_a, planet_b}:
            return ContraindicationPair(
                planets=pair_planets,
                stones=pair.get("stones", [stone_a, stone_b]),
                severity=pair.get("severity", "moderate"),
                reason=pair.get("reason", "").strip(),
            )
    return None


def _build_contraindication_summary(conflicts: list[ContraindicationPair], gems: list[str]) -> str:
    """Build human-readable summary of contraindication check."""
    if not conflicts:
        return f"No contraindications found among: {', '.join(gems)}. Safe to wear together."
    absolutes = [c for c in conflicts if c.severity == "absolute"]
    if absolutes:
        stone_pairs = [f"{c.stones[0]} + {c.stones[1]}" for c in absolutes]
        return (
            f"CRITICAL: {len(absolutes)} absolute conflict(s) found — "
            f"{'; '.join(stone_pairs)}. These combinations must NEVER be worn together."
        )
    highs = [c for c in conflicts if c.severity == "high"]
    if highs:
        stone_pairs = [f"{c.stones[0]} + {c.stones[1]}" for c in highs]
        return f"High-severity conflict(s): {'; '.join(stone_pairs)}. Strongly advised against."
    stone_pairs = [f"{c.stones[0]} + {c.stones[1]}" for c in conflicts]
    return f"Moderate conflict(s) found: {'; '.join(stone_pairs)}. Consult astrologer before wearing together."
