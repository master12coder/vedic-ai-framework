"""Domain models for D60 Shashtyamsha analysis."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ShashtyamshaDeity(BaseModel):
    """One of the 60 Shashtyamsha deities per BPHS Ch.6.

    Each deity presides over a 0.5° segment of a zodiac sign and determines
    whether a planet placed there receives auspicious or inauspicious support
    from past-life karma.
    """

    model_config = ConfigDict(frozen=True)

    number: int = Field(ge=1, le=60)  # 1-60
    name: str
    nature: str  # Saumya (benefic) / Krura (malefic) / Mishra (mixed)
    element: str  # Fire / Water / Air / Earth / Akasha
    signification: str


class ShashtyamshaPosition(BaseModel):
    """A planet's complete Shashtyamsha (D60) position with deity info.

    Encodes the planet's D1 sign, the D60 sign it occupies, the 0.5°
    division within the D1 sign, and the presiding deity with its nature.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    longitude: float = Field(ge=0.0, lt=360.0)
    d1_sign_index: int = Field(ge=0, le=11)
    d1_sign: str
    d60_sign_index: int = Field(ge=0, le=11)
    d60_sign: str
    d60_lord: str  # Lord of the D60 sign
    part: int = Field(ge=0, le=59)  # 0-based position within D1 sign (each = 0.5°)
    deity: ShashtyamshaDeity
    is_vargottam: bool  # True when D1 sign == D60 sign


class D60Analysis(BaseModel):
    """Full D60 Shashtyamsha analysis for all planets in a chart.

    The D60 is called the 'most telling chart' by Parashara because it reveals
    the deepest layer of past-life karma that shapes a planet's expression.
    """

    model_config = ConfigDict(frozen=True)

    planets: list[ShashtyamshaPosition]
    benefic_planets: list[str]  # Planets in Saumya (benefic) Shashtyamsha
    malefic_planets: list[str]  # Planets in Krura (malefic) Shashtyamsha
    mixed_planets: list[str]  # Planets in Mishra (mixed) Shashtyamsha
    vargottam_planets: list[str]  # Planets with identical D1 and D60 signs
    key_findings: list[str]  # Notable observations


class D1D60Comparison(BaseModel):
    """D1 vs D60 agreement for a single planet.

    Per BPHS: 'If D1 and D60 agree, the result is certain.'
    Agreement means both charts show the planet as benefic or both malefic.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    d1_assessment: str  # benefic / malefic / neutral
    d60_assessment: str  # Saumya / Krura / Mishra (deity nature)
    agreement: bool  # True when both show same polarity
    certainty: str  # certain / uncertain
    interpretation: str


class D1D60ComparisonResult(BaseModel):
    """Cross-chart validation result for all planets per BPHS rule.

    Planets where D1 and D60 agree (both benefic or both malefic) produce
    results with high certainty. Disagreement creates uncertainty.
    """

    model_config = ConfigDict(frozen=True)

    comparisons: list[D1D60Comparison]
    certain_benefics: list[str]  # D1 benefic + D60 Saumya
    certain_malefics: list[str]  # D1 malefic + D60 Krura
    conflicting: list[str]  # D1 and D60 disagree
    summary: str
