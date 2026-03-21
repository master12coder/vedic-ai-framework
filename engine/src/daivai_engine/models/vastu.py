"""Domain models for Vastu Shastra analysis results.

All models use Pydantic v2 with frozen=True for immutability.
Scores are normalised to 0-100 (100 = strongest/most auspicious).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DirectionStrength(BaseModel):
    """Strength of a Vastu direction based on its ruling planet's chart position.

    Each of the 8 compass directions has a planetary ruler (Dik Bala).
    The planet's dignity, house placement, and other factors produce a
    0-100 strength score for that direction.
    """

    model_config = ConfigDict(frozen=True)

    direction: str  # e.g. "North", "South-East"
    direction_hi: str  # Hindi name e.g. "उत्तर"
    planet: str  # Ruling planet for this direction
    strength_score: float = Field(ge=0.0, le=100.0)
    dignity: str  # exalted / mooltrikona / own / neutral / debilitated
    house: int = Field(ge=1, le=12)  # Planet's house in natal chart
    is_favorable: bool  # True when strength_score >= 50
    description: str


class VastuZone(BaseModel):
    """A zone in the Vastu Purusha Mandala (8 directions + Brahmasthana center).

    Zone strength mirrors the ruling planet's natal chart power.
    Center (Brahmasthana) has no planet and defaults to 50.
    """

    model_config = ConfigDict(frozen=True)

    direction: str
    direction_hi: str
    planet: str  # "Brahma" for the Center zone
    element: str
    element_hi: str
    deity: str
    color: str
    significance: str
    zone_strength: float = Field(ge=0.0, le=100.0)


class RoomRecommendation(BaseModel):
    """Vastu-optimal room placement recommendation for a native.

    Combines the classical ideal direction for each room type with the
    strength of the ruling planet in the native's own chart.
    """

    model_config = ConfigDict(frozen=True)

    room: str  # e.g. "Kitchen", "Master Bedroom"
    ideal_direction: str
    ideal_direction_hi: str
    alternate_direction: str
    planet: str  # Planet that rules the ideal direction/room
    planet_strength: float = Field(ge=0.0, le=100.0)
    is_favorable: bool  # True when ruling planet is strong (score >= 50)
    reason: str


class AyadiField(BaseModel):
    """A single energy field in the Ayadi Shadvarga (32-field perimeter system).

    Fields are classified as Devta (positive), Manushya (neutral),
    or Asura (negative) based on the presiding deity.
    """

    model_config = ConfigDict(frozen=True)

    field_number: int = Field(ge=1, le=32)
    direction: str
    classification: str  # "Devta", "Manushya", or "Asura"
    deity: str
    quality: str


class DoorAnalysis(BaseModel):
    """Entry door recommendation based on Ayadi Shadvarga and lagna lord.

    The ideal main entrance aligns with a Devta-classified field that
    matches the native's lagna lord direction.
    """

    model_config = ConfigDict(frozen=True)

    recommended_direction: str
    recommended_direction_hi: str
    ayadi_field: AyadiField
    classification: str  # Field classification: Devta / Manushya / Asura
    lagna_alignment: str  # "Excellent", "Good", or "Neutral"
    recommendation: str  # Human-readable guidance string


class VastuDosha(BaseModel):
    """A detected Vastu Dosha from natal chart planetary placement.

    Currently checks for planets in the 4th house (home, property)
    that create specific architectural or energetic challenges.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_hi: str
    is_present: bool
    planet: str
    house: int = Field(ge=1, le=12)
    severity: str  # "mild", "moderate", "severe", or "none"
    description: str
    remedy_direction: str  # Direction to strengthen as remedy


class VastuResult(BaseModel):
    """Complete Vastu Shastra analysis result for a natal chart.

    Aggregates directional strengths, Mandala zones, room recommendations,
    entry door analysis, and dosha detections into a single result object.
    """

    model_config = ConfigDict(frozen=True)

    lagna: str  # Ascendant sign e.g. "Mithuna"
    lagna_lord: str  # Planet ruling the ascendant e.g. "Mercury"
    direction_strengths: list[DirectionStrength]  # 9 entries (9 planets)
    most_favorable_direction: str
    least_favorable_direction: str
    favorable_directions: dict[str, str]  # role → direction mapping
    mandala_zones: list[VastuZone]  # 9 zones (8 directions + Center)
    room_recommendations: list[RoomRecommendation]
    door_analysis: DoorAnalysis
    doshas: list[VastuDosha]
    active_doshas: list[str]  # Names of doshas with is_present=True
    summary: str
