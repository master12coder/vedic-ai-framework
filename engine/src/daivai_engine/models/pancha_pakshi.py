"""Pancha Pakshi Shastra models — Tamil 5-bird timing system.

Five birds (Vulture, Owl, Crow, Cock, Peacock) govern time segments
based on birth nakshatra, birth paksha, and current daily Yama sequences.
Each day/night is split into 5 equal Yama periods; each Yama into 5 sub-periods.

Source: Classical Tamil Siddha tradition, Prasnamarga.
Cross-verified: DrikPanchang, Astro-Vision Pancha Pakshi module.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Bird(StrEnum):
    """The five birds of Pancha Pakshi Shastra.

    Each person has a birth bird determined by Moon's nakshatra and birth paksha.
    """

    VULTURE = "Vulture"  # Gidha / Valluru - Nakshatras 1-5 in Shukla
    OWL = "Owl"  # Uluka / Aandhai  - Nakshatras 6-11 in Shukla
    CROW = "Crow"  # Kaka  / Kaakam  - Nakshatras 12-16 in Shukla
    COCK = "Cock"  # Kukkuta / Kozhi - Nakshatras 17-22 in Shukla
    PEACOCK = "Peacock"  # Mayura / Mayil - Nakshatras 23-27 in Shukla


class Activity(StrEnum):
    """The five activities each bird performs within a Yama period.

    Activities cycle through the 5 Yama positions: Rule, Eat, Walk, Sleep, Die.
    The birth bird's activity at any moment determines auspiciousness.
    """

    RULE = "Rule"  # Rajya / Arasu  - full strength (1.0), most auspicious
    EAT = "Eat"  # Bhojana / Oon - 3/4 strength (0.75)
    WALK = "Walk"  # Chara / Nadai - 1/2 strength (0.50)
    SLEEP = "Sleep"  # Nidra / Thuyil - 1/4 strength (0.25)
    DIE = "Die"  # Marana / Saavu - no strength (0.0), avoid action


# Normalized strength per activity -- widely used in software implementations.
# Classical ratio: Rule=full, Eat=1/3, Walk=1/6, Sleep=1/12, Die=1/24.
# Normalized to 0.0-1.0 scale (4 grades): Rule=1.0, Eat=0.75, Walk=0.5, Sleep=0.25, Die=0.0.
ACTIVITY_STRENGTH: dict[Activity, float] = {
    Activity.RULE: 1.0,
    Activity.EAT: 0.75,
    Activity.WALK: 0.5,
    Activity.SLEEP: 0.25,
    Activity.DIE: 0.0,
}


class PanchaPakshiPeriod(BaseModel):
    """One Yama period — 1/5 of the daylight or nighttime duration (~2.4 hours).

    Five Yamas divide each half-day, each governed by one bird performing one activity.
    """

    model_config = ConfigDict(frozen=True)

    yama_index: int = Field(ge=1, le=5, description="1-based Yama number (1=first)")
    bird: Bird
    activity: Activity
    strength: float = Field(ge=0.0, le=1.0, description="Normalized activity strength")
    start_time: datetime
    end_time: datetime
    is_daytime: bool


class PanchaPakshiSubPeriod(BaseModel):
    """Sub-period within a Yama — 1/25 of daylight or nighttime duration (~28 min).

    Each Yama is subdivided into 5 sub-periods, one per bird, rotating from the
    Yama's main bird through the sequence. Sub-activities mirror the main cycle.
    """

    model_config = ConfigDict(frozen=True)

    sub_index: int = Field(ge=1, le=5, description="1-based sub-period number")
    bird: Bird
    activity: Activity
    strength: float = Field(ge=0.0, le=1.0)
    start_time: datetime
    end_time: datetime


class PanchaPakshiResult(BaseModel):
    """Complete Pancha Pakshi state at a specific moment for a given birth chart.

    Answers: which bird rules now, what is it doing, and crucially — what is
    MY birth bird doing right now (determines personal auspiciousness)?
    """

    model_config = ConfigDict(frozen=True)

    # Birth identification
    birth_bird: Bird
    birth_nakshatra: str
    birth_nakshatra_index: int = Field(ge=0, le=26)
    birth_paksha: str  # "Shukla" or "Krishna"

    # Query context
    query_dt: datetime
    is_daytime: bool
    current_paksha: str  # "Shukla" or "Krishna" at query time

    # Current main Yama period (~2.4 hours)
    current_bird: Bird
    current_activity: Activity
    current_strength: float = Field(ge=0.0, le=1.0)
    period_start: datetime
    period_end: datetime
    yama_index: int = Field(ge=1, le=5)

    # Current sub-period within the Yama (~28 minutes)
    sub_bird: Bird
    sub_activity: Activity
    sub_strength: float = Field(ge=0.0, le=1.0)
    sub_period_start: datetime
    sub_period_end: datetime
    sub_index: int = Field(ge=1, le=5)

    # Birth bird's activity in this Yama — the key auspiciousness indicator.
    # Each Yama sub-sequence contains every bird exactly once; the birth bird
    # occupies a fixed sub-position determined by its place in the main sequence.
    birth_bird_activity: Activity
    birth_bird_strength: float = Field(ge=0.0, le=1.0)


class PanchaPakshiDay(BaseModel):
    """Complete Pancha Pakshi breakdown for a full day (sunrise → next sunrise).

    Provides all 10 Yama periods (5 day + 5 night) to plan activities
    around the birth bird's most auspicious windows.
    """

    model_config = ConfigDict(frozen=True)

    date: str  # YYYY-MM-DD
    sunrise: datetime
    sunset: datetime
    paksha: str  # "Shukla" or "Krishna"
    birth_bird: Bird
    day_periods: list[PanchaPakshiPeriod]  # 5 Yamas from sunrise to sunset
    night_periods: list[PanchaPakshiPeriod]  # 5 Yamas from sunset to next sunrise
