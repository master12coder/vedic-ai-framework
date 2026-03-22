"""Domain models for Namakarana — Vedic Naming Ceremony computation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GandMoolResult(BaseModel):
    """Gand Mool nakshatra check for a newborn's birth chart.

    Gand Mool nakshatras (Ashwini, Ashlesha, Magha, Jyeshtha, Moola, Revati)
    are junction points at rasi-sandhi. A child born with Moon here traditionally
    requires a Gand Mool Shanti Puja to mitigate the effects.
    """

    model_config = ConfigDict(frozen=True)

    is_gand_mool: bool
    nakshatra: str
    pada: int = Field(ge=1, le=4)
    severity: str  # none / mild / moderate / severe
    description: str
    recommended_shanti: str


class NameNumerology(BaseModel):
    """Chaldean name numerology result for a given name string."""

    model_config = ConfigDict(frozen=True)

    name: str
    name_number: int = Field(ge=1, le=9)  # Single digit (1-9)
    raw_sum: int = Field(ge=0)
    interpretation: str


class NameScore(BaseModel):
    """Composite auspiciousness score for a candidate name.

    Evaluates three dimensions against the birth chart:
    - nakshatra_match: starts with Moon's nakshatra-pada syllable (0-40 pts)
    - rashi_score: starts with a Moon-sign letter (0-30 pts)
    - numerology_score: name number compatible with birth number (0-30 pts)

    Total ≥ 60 is recommended for the Namakarana ceremony.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    total_score: float = Field(ge=0.0, le=100.0)
    nakshatra_match: float = Field(ge=0.0, le=40.0)
    rashi_score: float = Field(ge=0.0, le=30.0)
    numerology_score: float = Field(ge=0.0, le=30.0)
    name_number: int = Field(ge=1, le=9)
    is_recommended: bool
    breakdown: dict[str, str]


class NameSuggestion(BaseModel):
    """Complete naming guidance for the Namakarana ceremony.

    Contains all astrological context needed to select an auspicious name:
    nakshatra-pada syllables, rashi letters, birth numerology, and
    compatible name numbers to target.
    """

    model_config = ConfigDict(frozen=True)

    nakshatra: str
    pada: int = Field(ge=1, le=4)
    nakshatra_letters: list[str]  # Exact pada syllables (primary auspicious)
    rashi: str
    rashi_letters: list[str]  # All 9 rashi-pada letters (secondary)
    rashi_lord: str
    birth_number: int = Field(ge=1, le=9)
    compatible_name_numbers: list[int]
    primary_letters: list[str]  # Nakshatra-pada letters (most auspicious)
    all_letters: list[str]  # Nakshatra + unique rashi letters combined
    guidance: str


class NamakaranaResult(BaseModel):
    """Complete Namakarana ceremony computation result.

    Combines Gand Mool dosha check and name suggestion into a single
    structured result for the naming ceremony.
    """

    model_config = ConfigDict(frozen=True)

    gand_mool: GandMoolResult
    suggestion: NameSuggestion
