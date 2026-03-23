"""Domain models for Dasha-Transit integration analysis.

Combines running Vimshottari dasha lords with their current transit
positions, Ashtakavarga strength, and double transit activation.
This is the #1 predictive timing technique in Vedic astrology.

Source: BPHS Ch.25, Phaladeepika Ch.26.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DashaLordTransit(BaseModel):
    """Transit analysis for a single dasha lord.

    Captures both the natal promise (house placement, dignity) and the
    current transit delivery (transit position, BAV strength, dignity).

    Source: BPHS Ch.25 — dasha lords deliver results based on natal +
    transit position simultaneously.
    """

    model_config = ConfigDict(frozen=True)

    lord: str  # Planet name e.g. "Jupiter"
    dasha_level: str  # "MD" / "AD" / "PD"

    # Natal position
    natal_house: int = Field(ge=1, le=12)
    natal_sign_index: int = Field(ge=0, le=11)
    natal_dignity: str

    # Transit position
    transit_sign_index: int = Field(ge=0, le=11)
    transit_house_from_lagna: int = Field(ge=1, le=12)
    transit_house_from_moon: int = Field(ge=1, le=12)
    transit_house_from_natal: int = Field(ge=1, le=12)
    transit_dignity: str  # exalted / own / debilitated / neutral
    is_retrograde_transit: bool

    # BAV strength
    bav_bindus: int = Field(ge=0, le=8)
    bav_strength: str  # "strong" (5+), "moderate" (3-4), "weak" (0-2)

    # Houses owned by this lord
    houses_owned: list[int]

    # Composite scoring
    favorability: str  # "favorable" / "neutral" / "unfavorable"
    score: int = Field(ge=0, le=100)


class DoubleTransitOnDashaHouses(BaseModel):
    """Double transit (Jupiter + Saturn) activation of a dasha lord's house.

    When both Jupiter and Saturn aspect (by transit) a house owned by a
    running dasha lord, events signified by that house become highly probable.

    Source: K.N. Rao method — widely used in North Indian tradition.
    """

    model_config = ConfigDict(frozen=True)

    house: int = Field(ge=1, le=12)
    house_signification: str
    jupiter_activates: bool
    saturn_activates: bool
    both_activate: bool  # True = event likely in this house's domain


class DashaTransitAnalysis(BaseModel):
    """Complete dasha-transit integration for the current period.

    Combines:
      1. Each dasha lord's transit position and BAV strength
      2. Double transit activation on houses owned by dasha lords
      3. MD-AD inter-relationship (friends / enemies / neutral)
      4. Composite prediction indicators and event domains

    This is the PRIMARY timing tool for answering "WHEN will X happen?"

    Source: BPHS Ch.25, Phaladeepika Ch.26.
    """

    model_config = ConfigDict(frozen=True)

    analysis_date: str

    # Current dasha lords with transit analysis
    md_lord: DashaLordTransit
    ad_lord: DashaLordTransit
    pd_lord: DashaLordTransit | None = None

    # Double transit on houses owned by dasha lords
    double_transit_activation: list[DoubleTransitOnDashaHouses]

    # MD-AD relationship
    md_ad_relationship: str  # "friends" / "neutral" / "enemies"
    md_ad_mutual_aspect: bool  # MD and AD lords aspect each other in transit

    # Composite prediction indicators
    overall_favorability: str  # highly_favorable / favorable / mixed / challenging / difficult
    active_houses: list[int]  # houses activated by BOTH dasha + transit
    event_domains: list[str]  # likely life areas: ["career", "marriage", ...]

    summary: str
