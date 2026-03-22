"""Gochara (Transit Analysis) models — Pydantic v2.

Covers:
  - GocharaVedha: obstruction status for a transiting planet
  - MoorthyClass: Poorna/Madhya/Swalpa/Nishphala classification
  - GocharaPlanetResult: complete result for one planet's transit
  - GocharaAnalysis: full analysis for all 9 planets
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MoorthyClass(StrEnum):
    """Moorthy Nirnaya — transit quality from BAV bindu count.

    Source: Phaladeepika, Mantreswara tradition.
    """

    poorna = "poorna"  # 5-8 bindus — full benefit (Swarna/Gold)
    madhya = "madhya"  # 3-4 bindus — partial benefit (Rajata/Silver)
    swalpa = "swalpa"  # 1-2 bindus — minimal benefit (Tamra/Copper)
    nishphala = "nishphala"  # 0 bindus — fruitless (Loha/Iron)


class Favorability(StrEnum):
    """Gochara favorability classification."""

    very_favorable = "very_favorable"
    favorable = "favorable"
    neutral = "neutral"
    unfavorable = "unfavorable"
    very_unfavorable = "very_unfavorable"


class GocharaVedha(BaseModel):
    """Vedha (obstruction) status for a transiting planet.

    Vedha cancels beneficial transit effects when a natal planet
    occupies the vedha counterpart house of the favorable transit house.
    Malefic transits are never blocked by vedha.

    Source: Phaladeepika transit chapter.
    """

    model_config = ConfigDict(frozen=True)

    vedha_house: int = Field(ge=1, le=12, description="Vedha counterpart house")
    is_active: bool = Field(description="True if vedha is blocking the benefit")
    blocking_planet: str | None = Field(
        default=None, description="Natal planet occupying the vedha house"
    )


class GocharaPlanetResult(BaseModel):
    """Complete Gochara result for a single planet's transit.

    Combines gochara base score, BAV bindu count, Moorthy Nirnaya,
    vedha obstruction, and final adjusted score.
    """

    model_config = ConfigDict(frozen=True)

    planet: str = Field(description="Planet name (Sun, Moon, Mars, ...)")
    transit_sign_index: int = Field(ge=0, le=11, description="Transit sign (0=Mesha)")
    transit_sign: str = Field(description="Sanskrit sign name")
    house_from_moon: int = Field(ge=1, le=12, description="House from natal Moon")
    gochara_score: int = Field(ge=-2, le=2, description="Raw gochara score from Phaladeepika")
    favorability: Favorability = Field(description="Named favorability category")
    result_text: str = Field(description="Classical result description")
    special_name: str | None = Field(
        default=None,
        description="Named phenomenon (Sade Sati, Kantak Shani, etc.)",
    )
    vedha: GocharaVedha | None = Field(
        default=None, description="Vedha status (None if no vedha pair for this house)"
    )
    vedha_active: bool = Field(
        default=False, description="True if vedha is blocking this transit's benefit"
    )
    bav_bindus: int = Field(ge=0, le=8, description="BAV bindu count in transit sign (0-8)")
    moorthy: MoorthyClass = Field(description="Moorthy Nirnaya classification")
    final_score: int = Field(
        ge=-4,
        le=4,
        description="Adjusted score: gochara + BAV modifier, zeroed if vedha active",
    )


class GocharaAnalysis(BaseModel):
    """Full Gochara analysis for all 9 planets.

    Provides transit results from natal Moon sign with vedha, Moorthy
    Nirnaya, special phenomena, double transit, and overall rating.
    """

    model_config = ConfigDict(frozen=True)

    target_date: str = Field(description="Transit date in DD/MM/YYYY format")
    chart_name: str = Field(description="Native's name")
    moon_sign_index: int = Field(ge=0, le=11, description="Natal Moon sign index")
    moon_sign: str = Field(description="Natal Moon sign (Sanskrit)")
    planet_results: list[GocharaPlanetResult] = Field(
        description="Transit results for all 9 planets"
    )
    sadesati_active: bool = Field(description="True if Saturn is in 12th, 1st, or 2nd from Moon")
    sadesati_phase: str | None = Field(
        default=None,
        description="Sade Sati phase: Rising (12th), Peak (1st), Setting (2nd)",
    )
    sadesati_intensity: str | None = Field(
        default=None, description="Sade Sati intensity: mild/moderate/severe"
    )
    double_transit_houses: list[int] = Field(
        default_factory=list,
        description="Houses activated by both Jupiter and Saturn transit simultaneously",
    )
    overall_rating: int = Field(
        ge=-10,
        le=10,
        description="Sum of final scores, clamped to -10..+10",
    )
    summary: str = Field(description="Brief human-readable transit summary")
