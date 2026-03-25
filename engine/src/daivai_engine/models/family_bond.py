"""Domain models for family bond analysis: wealth flow, gemstone synergy, dasha sync."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from daivai_engine.models.functional_nature import FunctionalNature, ShadowPlanetNature


class WealthFlowProfile(BaseModel):
    """Financial archetype classification for one person.

    Based on 2nd lord (stored wealth), 10th lord (career/karma income),
    and 11th lord (gains) house placements and dignities.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    archetype: str  # "earner", "accumulator", "distributor", "mixed"
    second_lord: str
    second_lord_house: int = Field(ge=1, le=12)
    tenth_lord: str
    tenth_lord_house: int = Field(ge=1, le=12)
    eleventh_lord: str
    eleventh_lord_house: int = Field(ge=1, le=12)
    wealth_score: float = Field(ge=0, le=100)
    description: str


class ConjunctionPenalty(BaseModel):
    """Gemstone weight penalty from planet conjuncting malefic influences.

    When a recommended planet (e.g., Lagnesh) conjuncts Rahu, 6L, 8L, or 12L,
    the gemstone weight should be reduced — the stone amplifies ALL conjunct
    energies, not just the target planet. Source: BV Raman, How to Judge a
    Horoscope Vol.II.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    has_penalty: bool
    penalty_factor: float = Field(ge=0, le=1)  # 1.0 = no penalty
    conjunct_with: list[str] = Field(default_factory=list)
    reasoning: str


class FamilyMemberGemProfile(BaseModel):
    """Gemstone profile for one family member including shadow planet analysis."""

    model_config = ConfigDict(frozen=True)

    name: str
    lagna_sign: str
    recommended: list[str] = Field(default_factory=list)  # Stone names
    prohibited: list[str] = Field(default_factory=list)
    test_with_caution: list[str] = Field(default_factory=list)
    rahu_gem: ShadowPlanetNature | None = None
    ketu_gem: ShadowPlanetNature | None = None
    conjunction_penalties: list[ConjunctionPenalty] = Field(default_factory=list)


class GemSynergyPair(BaseModel):
    """A cross-member gemstone relationship.

    Karmic complementarity: one person's prohibited stone is another's
    recommended stone — "जो एक के लिए विष, दूसरे के लिए अमृत".
    """

    model_config = ConfigDict(frozen=True)

    person_a: str
    person_b: str
    stone: str
    planet: str
    relationship: str  # "karmic_complement", "shared_recommend", "conflict"
    description: str


class FamilyGemSynergyResult(BaseModel):
    """Cross-family gemstone analysis aggregating all members."""

    model_config = ConfigDict(frozen=True)

    members: list[FamilyMemberGemProfile] = Field(default_factory=list)
    synergy_pairs: list[GemSynergyPair] = Field(default_factory=list)
    family_safe_stones: list[str] = Field(default_factory=list)
    summary: str


class DashaSyncEntry(BaseModel):
    """Dasha state for one person at a point in time."""

    model_config = ConfigDict(frozen=True)

    name: str
    current_md_lord: str
    current_ad_lord: str | None = None
    md_nature: FunctionalNature
    md_start: datetime
    md_end: datetime


class DashaSyncResult(BaseModel):
    """Synchronized dasha view for a family."""

    model_config = ConfigDict(frozen=True)

    entries: list[DashaSyncEntry] = Field(default_factory=list)
    favorable_windows: list[str] = Field(default_factory=list)
    challenging_windows: list[str] = Field(default_factory=list)
    summary: str
