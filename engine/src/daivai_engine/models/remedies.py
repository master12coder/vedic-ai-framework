"""Domain models for Vedic remedy recommendations — mantras, yantras, daan."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MantraRecommendation(BaseModel):
    """A single mantra recommendation for a native.

    Encapsulates the full details needed to begin a mantra sadhana:
    the mantra text, beej syllable, japa counts, timing guidance,
    deity, and mala to use.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    planet_hi: str
    beej: str
    beej_mantra: str
    beej_mantra_en: str
    moola_mantra: str
    gayatri: str
    japa_daily: int = Field(ge=1)
    japa_total: int = Field(ge=1)
    best_day: str
    best_time: str
    facing_direction: str
    mala: str
    deity: str
    reason: str  # why this planet's mantra is recommended for this chart


class NakshatraMantra(BaseModel):
    """Nakshatra deity mantra for a specific nakshatra.

    Used when the natal Moon, lagna, or a chart factor falls in a specific
    nakshatra and its presiding deity's blessings are sought.
    """

    model_config = ConfigDict(frozen=True)

    nakshatra_number: int = Field(ge=1, le=27)
    nakshatra_en: str
    nakshatra_hi: str
    deity: str
    deity_hi: str
    mantra: str
    mantra_en: str
    extended_mantra: str
    japa_count: int = Field(ge=1)
    deity_domain: str


class YantraRecommendation(BaseModel):
    """A single yantra recommendation for a native.

    Contains the magic square grid, material, installation instructions,
    and the reason it is recommended for this chart.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    planet_hi: str
    vedic_number: int = Field(ge=1, le=9)
    grid: list[list[int]]  # 3x3 magic square
    magic_sum: int = Field(ge=1)
    center_number: int = Field(ge=1)
    material_primary: str
    installation_day: str
    installation_time: str
    energizing_mantra: str
    purpose: list[str]
    reason: str  # why this yantra is prescribed for this chart


class RemedyPlan(BaseModel):
    """Complete remedy plan derived from chart analysis.

    Aggregates all recommended mantras, yantras, and the natal Moon
    nakshatra mantra into a single actionable plan for the native.
    Priority order: lagna lord first, then afflicted planets, then dasha lord.
    """

    model_config = ConfigDict(frozen=False)

    native_name: str
    lagna_sign: str
    lagna_lord: str
    dasha_lord: str | None = None

    primary_mantras: list[MantraRecommendation] = Field(default_factory=list)
    nakshatra_mantra: NakshatraMantra | None = None
    primary_yantras: list[YantraRecommendation] = Field(default_factory=list)

    afflicted_planets: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
