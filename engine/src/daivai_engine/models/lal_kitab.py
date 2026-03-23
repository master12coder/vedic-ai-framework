"""Domain models for Lal Kitab analysis.

Lal Kitab is a distinct astrological system by Pandit Roop Chand Joshi
(5 volumes, 1939-1952). It uses planet-in-house positions (ignoring signs)
with unique remedy rules, debt (Rin) analysis, and Pakka Ghar assessment.

Source: Lal Kitab (1939-1952).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LalKitabPlanetAssessment(BaseModel):
    """Assessment of a single planet's strength in the Lal Kitab system.

    Strength is determined by Pakka Ghar placement, friendships, and
    Rahu/Ketu affliction (dormancy).
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    house: int = Field(ge=1, le=12)
    pakka_ghar: int = Field(ge=1, le=12)
    is_in_pakka_ghar: bool
    strength: str  # "very_strong" / "strong" / "moderate" / "weak" / "dormant"
    is_dormant: bool
    friends_in_chart: list[str]
    enemies_in_chart: list[str]
    assessment: str


class LalKitabRin(BaseModel):
    """Represents a Lal Kitab debt (Rin) detected in the chart.

    Three types: Pitra Rin (ancestral), Matri Rin (mother's), Stri Rin (wife's).
    """

    model_config = ConfigDict(frozen=True)

    rin_type: str  # "pitra" / "matri" / "stri"
    rin_name_hi: str  # "पितृ ऋण" / "मातृ ऋण" / "स्त्री ऋण"
    is_present: bool
    causing_planet: str
    causing_house: int = Field(ge=1, le=12)
    description: str
    severity: str  # "mild" / "moderate" / "severe"


class LalKitabRemedy(BaseModel):
    """A matched remedy from the Lal Kitab remedies YAML."""

    model_config = ConfigDict(frozen=True)

    planet: str
    house: int = Field(ge=1, le=12)
    remedy_text: str
    remedy_text_hi: str | None = None
    category: str  # "daan" / "behavioral" / "ritual" / "object"


class LalKitabResult(BaseModel):
    """Complete Lal Kitab analysis result for a birth chart.

    Includes planet-by-planet assessment, detected debts (Rins),
    matched remedies, and overall summary.
    """

    model_config = ConfigDict(frozen=True)

    planet_assessments: list[LalKitabPlanetAssessment]
    rins: list[LalKitabRin]
    applicable_remedies: list[LalKitabRemedy]
    dormant_planets: list[str]
    strongest_planet: str
    weakest_planet: str
    summary: str
