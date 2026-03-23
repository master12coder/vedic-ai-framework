"""Domain models for reference-lagna chart analysis (Chandra/Surya Kundali)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ReferenceHouse(BaseModel):
    """A single house in the reference chart (from Moon or Sun as lagna).

    Source: BPHS — Chandra Kundali is analysed alongside Rasi chart
    for confirming Rasi-chart indications and judging mental disposition.
    """

    model_config = ConfigDict(frozen=True)

    house_number: int = Field(ge=1, le=12)  # 1-12 from reference
    sign_index: int = Field(ge=0, le=11)
    sign: str
    lord: str
    lord_ref_house: int = Field(ge=1, le=12)  # house of the lord from reference
    planets: list[str]  # planets occupying this house from reference


class ReferencePlanetPosition(BaseModel):
    """A planet's position re-mapped from the reference planet's perspective.

    Source: Phaladeepika Ch.2 — house positions from Moon are used to
    assess mental tendencies, emotional strength, and popular support.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    ref_house: int = Field(ge=1, le=12)
    sign_index: int = Field(ge=0, le=11)
    sign: str
    dignity: str
    is_ref_kendra: bool  # in 1/4/7/10 from reference
    is_ref_trikona: bool  # in 1/5/9 from reference
    is_ref_dusthana: bool  # in 6/8/12 from reference


class ReferenceChartAnalysis(BaseModel):
    """Complete analysis of a chart from an alternate lagna (Moon or Sun).

    Source: BPHS (throughout), Uttarakalamrita, Phaladeepika —
    Chandra Kundali and Surya Kundali are standard supplementary charts
    used to confirm or nuance findings from the Rasi chart.
    """

    model_config = ConfigDict(frozen=True)

    reference_planet: str  # "Moon" or "Sun"
    reference_sign_index: int = Field(ge=0, le=11)
    reference_sign: str

    houses: list[ReferenceHouse]  # 12 houses from reference
    planet_positions: dict[str, ReferencePlanetPosition]

    # Key derived insights
    ref_lagna_lord: str  # lord of Moon/Sun sign
    ref_lagna_lord_house: int = Field(ge=1, le=12)
    yogakaraka_from_ref: str | None  # planet owning both kendra + trikona from ref

    # Strength indicators
    planets_in_kendras: list[str]  # 1,4,7,10 from reference
    planets_in_trikonas: list[str]  # 1,5,9 from reference
    planets_in_dusthanas: list[str]  # 6,8,12 from reference

    summary: str
