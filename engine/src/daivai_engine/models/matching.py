"""Domain models for Ashtakoot (36 Guna) marriage matching."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RajjuResult(BaseModel):
    """Rajju (backbone) Dosha result for marriage compatibility.

    Rajju maps Moon nakshatras to body parts. If both partners share
    the same Rajju (body part), certain inauspicious effects are indicated.
    """

    model_config = ConfigDict(frozen=True)

    has_dosha: bool
    nakshatra1: str
    nakshatra2: str
    body_part: str | None  # Paada / Kati / Nabhi / Kantha / Shira (or None if no dosha)
    severity: str  # none / mild / moderate / severe
    description: str


class KootaScore(BaseModel):
    """Represents the score for a single koota (compatibility factor) in Ashtakoot matching.

    Each koota has a name, maximum possible points, obtained points, and a
    description of how the score was determined.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_hindi: str
    max_points: float = Field(ge=0)
    obtained: float = Field(ge=0)
    description: str


class MatchingResult(BaseModel):
    """Represents the complete Ashtakoot (36 Guna) matching result between two persons.

    Contains the Moon sign and nakshatra indices for both persons, the list of
    individual koota scores, the aggregate totals, percentage, and a human-readable
    recommendation.
    """

    model_config = ConfigDict(frozen=True)

    person1_nakshatra_index: int = Field(ge=0, le=26)
    person1_moon_sign: int = Field(ge=0, le=11)
    person2_nakshatra_index: int = Field(ge=0, le=26)
    person2_moon_sign: int = Field(ge=0, le=11)
    kootas: list[KootaScore]
    total_obtained: float = Field(ge=0)
    total_max: float = Field(ge=0)
    percentage: float = Field(ge=0, le=100)
    recommendation: str
