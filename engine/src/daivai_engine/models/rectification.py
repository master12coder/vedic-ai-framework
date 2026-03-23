"""Domain models for birth time rectification.

Supports three rectification methods:
1. KP Ruling Planets — match current ruling planets to natal chart
2. Event-Based Verification — check dasha alignment with life events
3. Tattwa-Based — narrow lagna by reported birth element

Source: BPHS Ch.4, KP system.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RulingPlanets(BaseModel):
    """The five KP ruling planets at a given moment.

    Derived from Moon's nakshatra lord, Moon's sign lord, lagna's nakshatra
    lord, lagna's sign lord, and the day lord.
    """

    model_config = ConfigDict(frozen=True)

    moon_nak_lord: str
    moon_sign_lord: str
    lagna_nak_lord: str
    lagna_sign_lord: str
    day_lord: str
    unique_rulers: list[str]


class LifeEvent(BaseModel):
    """A known life event used for event-based rectification."""

    model_config = ConfigDict(frozen=True)

    event_type: str  # "marriage" / "first_child" / "career_start" / "parent_death"
    date: str  # DD/MM/YYYY
    description: str | None = None


class EventVerification(BaseModel):
    """Verification result for a single life event against dasha periods."""

    model_config = ConfigDict(frozen=True)

    event: LifeEvent
    dasha_lord_at_event: str
    antardasha_lord_at_event: str
    expected_lords: list[str]
    matches: bool
    confidence: str  # "high" / "medium" / "low"


class RectificationCandidate(BaseModel):
    """A candidate birth time with its rectification score."""

    model_config = ConfigDict(frozen=True)

    birth_time: str  # HH:MM
    lagna_sign_index: int = Field(ge=0, le=11)
    lagna_sign: str
    lagna_degree: float
    ruling_planet_matches: int = Field(ge=0, le=5)
    event_matches: int = Field(ge=0)
    total_score: float
    method: str  # "ruling_planets" / "event_based" / "tattwa" / "combined"


class RectificationResult(BaseModel):
    """Complete birth time rectification result.

    Contains the original birth data, ruling planet analysis, event
    verifications, ranked candidates, and overall confidence.
    """

    model_config = ConfigDict(frozen=True)

    original_birth_time: str
    original_lagna: str

    ruling_planets_now: RulingPlanets | None = None
    event_verifications: list[EventVerification] = Field(default_factory=list)

    candidates: list[RectificationCandidate]
    best_candidate: RectificationCandidate | None = None

    confidence: str  # "high" / "medium" / "low"
    summary: str
