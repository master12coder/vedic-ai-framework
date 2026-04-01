"""Prediction accuracy models — AccuracyMetrics, CredibilityScore."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CredibilityLevel = Literal["novice", "developing", "reliable", "expert", "master"]


class AccuracyMetrics(BaseModel):
    """Aggregated prediction accuracy statistics."""

    model_config = ConfigDict(frozen=True)

    total_predictions: int = 0
    verified_correct: int = 0
    verified_incorrect: int = 0
    pending: int = 0
    accuracy_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    by_category: dict[str, float] = {}  # e.g. {"career": 0.85, "marriage": 0.70}


class CredibilityScore(BaseModel):
    """Overall credibility assessment based on prediction track record."""

    model_config = ConfigDict(frozen=True)

    score: int = Field(default=0, ge=0, le=100)
    level: CredibilityLevel = "novice"
    factors: list[str] = []
