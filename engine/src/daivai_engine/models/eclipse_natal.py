"""Domain models for eclipse-natal chart impact analysis."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EclipseData(BaseModel):
    """Represents a single solar or lunar eclipse event.

    Source: Surya Siddhanta — eclipses occur when New/Full Moons
    fall within ~18 degrees of the Rahu-Ketu axis.
    """

    model_config = ConfigDict(frozen=True)

    eclipse_type: str  # "solar" / "lunar"
    date: str  # DD/MM/YYYY
    julian_day: float
    longitude: float = Field(ge=0, lt=360)  # sidereal longitude of eclipse point
    sign_index: int = Field(ge=0, le=11)
    sign: str
    nakshatra: str


class NatalImpact(BaseModel):
    """Impact of an eclipse on a single natal point (planet or lagna).

    Source: BPHS Ch.27 — eclipse effects are strongest when
    the eclipse degree closely conjuncts natal points.
    """

    model_config = ConfigDict(frozen=True)

    natal_point: str  # planet name or "Lagna"
    natal_longitude: float = Field(ge=0, lt=360)
    orb: float  # degrees of separation from eclipse
    is_hit: bool  # within effective orb (5 degrees)
    severity: str  # "exact" (<1), "strong" (1-3), "moderate" (3-5), "none" (>5)
    house_affected: int = Field(ge=1, le=12)  # natal house of impacted point
    significations: list[str]  # what this point rules


class EclipseNatalResult(BaseModel):
    """Complete analysis of an eclipse's impact on a natal chart.

    Source: BPHS Ch.27, Surya Siddhanta — combines eclipse position
    with natal chart overlay to assess activation of houses and planets.
    """

    model_config = ConfigDict(frozen=True)

    eclipse: EclipseData
    impacts: list[NatalImpact]  # sorted by orb (tightest first)
    most_affected_planet: str | None  # tightest orb hit
    most_affected_house: int | None
    houses_activated: list[int]  # houses whose lords are hit
    is_significant: bool  # any impact within 3 degrees
    summary: str
