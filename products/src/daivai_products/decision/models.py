"""Pydantic v2 models for Decision Engine outputs.

Every model here is frozen (immutable) and fully typed. These models are the
data contract between the Decision Engine (Layer 3) and the AI Interpretation
layer (Layer 4). Nothing downstream should parse raw dicts — always use these.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# ── Cross-Chart Validation ──────────────────────────────────────────────────


class CrossChartCheck(BaseModel):
    """Result of comparing a single planet across D1 (Rashi) and D9 (Navamsha).

    Captures whether the planet's dignity/placement in the two charts are
    consistent, contradictory, or show special patterns like Neech Bhanga.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    d1_sign: str
    d1_dignity: str  # exalted / debilitated / own / mooltrikona / neutral
    d9_sign: str
    d9_dignity: str  # exalted / debilitated / own / mooltrikona / neutral
    is_vargottam: bool
    is_consistent: bool
    pattern: str  # "strong_confirmed" | "neech_bhanga_potential" | "d1_weakened" | "vargottam_strong" | "neutral" | "mixed"
    explanation: str


class CrossChartValidation(BaseModel):
    """Aggregated cross-chart validation report for the entire chart.

    Contains per-planet checks plus an overall consistency score (0.0-1.0).
    """

    model_config = ConfigDict(frozen=True)

    checks: list[CrossChartCheck]
    consistency_score: float = Field(ge=0.0, le=1.0)
    vargottam_count: int = Field(ge=0)
    strong_confirmations: int = Field(ge=0)
    weakened_count: int = Field(ge=0)
    neech_bhanga_count: int = Field(ge=0)
    summary: str


# ── Confidence Scoring ──────────────────────────────────────────────────────


class SectionConfidence(BaseModel):
    """Confidence assessment for a single life-area section.

    Score is 0-100 with boosters, penalties, and textual caveats explaining
    why confidence is higher or lower for this area.
    """

    model_config = ConfigDict(frozen=True)

    section: str  # career / marriage / health / wealth / education / spiritual / children / longevity / timing
    score: int = Field(ge=0, le=100)
    boosters: list[str]  # Human-readable reasons score went up
    penalties: list[str]  # Human-readable reasons score went down
    caveats: list[str]  # Textual warnings (not score-affecting)
    key_planets: list[str]  # Planets most relevant to this section


class ConfidenceReport(BaseModel):
    """Full confidence report across all life-area sections.

    Includes per-section scores, an overall weighted average, and
    birth-time quality assessment.
    """

    model_config = ConfigDict(frozen=True)

    sections: list[SectionConfidence]
    overall_score: int = Field(ge=0, le=100)
    birth_time_quality: str  # "exact" | "approximate" | "unknown"
    birth_time_caveats: list[str]


# ── Chart Selection (used by chart_selector) ────────────────────────────────


class ChartSelection(BaseModel):
    """Which divisional charts are relevant for a given query type."""

    model_config = ConfigDict(frozen=True)

    query_type: str
    primary_chart: str  # e.g. "D1", "D9", "D10"
    supporting_charts: list[str]
    reason: str


# ── House Highlighting (used by house_highlighter) ──────────────────────────


class HouseHighlight(BaseModel):
    """Houses and karakas relevant for a query type."""

    model_config = ConfigDict(frozen=True)

    query_type: str
    primary_houses: list[int]
    supporting_houses: list[int]
    karaka_planets: list[str]
    reason: str


# ── Gemstone Weight (used by gemstone_weight) ────────────────────────────────


class GemstoneWeight(BaseModel):
    """Computed gemstone carat recommendation with full factor breakdown.

    10-factor scoring: body weight, avastha, BAV, dignity, combustion,
    retrograde, dasha, lordship, stone density, purpose multiplier.
    Status is derived from lordship_rules.yaml -- never hardcoded.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    stone: str  # English name (e.g. "Emerald (Panna)")
    stone_hindi: str  # Hindi name (e.g. "Panna")
    status: str  # "RECOMMENDED" | "TEST_WITH_CAUTION" | "PROHIBITED"
    base_ratti: float = Field(ge=0.0)
    recommended_ratti: float = Field(ge=0.0)
    factor_breakdown: dict[str, float]  # factor_name -> multiplier
    reasoning: str
    free_alternatives: list[str]  # Mantra, color therapy, daan alternatives


class GemstoneReport(BaseModel):
    """Complete gemstone analysis for a chart with safety enforcement."""

    model_config = ConfigDict(frozen=True)

    lagna: str
    lagna_lord: str
    weights: list[GemstoneWeight]
    prohibited_stones: list[str]  # Stone names that must NEVER be recommended
    safety_warnings: list[str]
