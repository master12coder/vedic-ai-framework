"""Pydantic models for gemstone weight results."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WeightFactor(BaseModel):
    """One factor contributing to the gemstone weight computation."""

    model_config = ConfigDict(frozen=True)
    name: str
    raw_value: str
    multiplier: float
    explanation: str


class GemstoneWeightResult(BaseModel):
    """Full gemstone weight recommendation for one stone."""

    model_config = ConfigDict(frozen=True)
    planet: str
    stone_name: str
    stone_name_hi: str
    status: str  # recommended / test_with_caution / prohibited
    base_ratti: float
    recommended_ratti: float
    factors: list[WeightFactor]
    website_comparisons: dict[str, float]
    pros_cons: dict[str, list[str]]
    free_alternatives: dict[str, str]
    prohibition_reason: str | None = None
