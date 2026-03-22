"""Domain models for Namakarana (Hindu Naming Ceremony) computation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NakshtraAkshar(BaseModel):
    """A nakshatra-pada's recommended starting syllables for naming.

    Each of the 27 nakshatras has 4 padas (quarters), giving 108 aksharas
    in total. The child's name traditionally begins with the syllable of
    their birth nakshatra-pada.
    """

    model_config = ConfigDict(frozen=True)

    nakshatra: str
    nakshatra_index: int = Field(ge=0, le=26)
    pada: int = Field(ge=1, le=4)
    syllable: str  # Primary recommended syllable (e.g. "Va")
    syllable_devanagari: str  # Devanagari form (e.g. "वा")
    alternate_syllables: list[str]  # Regional/textual variants
    rashi: str  # Rashi (sign) where this nakshatra falls
    nakshatra_lord: str  # Ruling planet of the nakshatra


class RashiLetters(BaseModel):
    """All naming letters associated with a Rashi (Moon sign).

    Derived from the starting syllables of all padas falling in that rashi.
    """

    model_config = ConfigDict(frozen=True)

    rashi: str
    rashi_index: int = Field(ge=0, le=11)
    letters: list[str]  # All syllables for this rashi
    primary_letters: list[str]  # Most commonly used letters


class NameScore(BaseModel):
    """Comprehensive scoring of a name against a birth chart.

    Evaluates nakshatra syllable match, rashi compatibility, numerology,
    and sound vibration (Nada) quality.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    nakshatra_syllable_match: bool  # Does name start with birth nakshatra syllable?
    matching_syllable: str | None  # Which syllable matched (or None)
    nakshatra_score: float = Field(ge=0, le=10)  # 10 = perfect match
    rashi_score: float = Field(ge=0, le=10)  # 10 = name starts with rashi letter
    numerology_name_number: int = Field(ge=1, le=9)  # Chaldean name number
    numerology_life_number: int = Field(ge=1, le=9)  # Life path number from DOB
    numerology_score: float = Field(ge=0, le=10)  # Compatibility of the two numbers
    planet_of_sound: str  # Planet ruling the name's starting sound
    planet_is_benefic_for_lagna: bool  # Whether that planet benefits the lagna
    sound_score: float = Field(ge=0, le=10)  # Sound vibration quality
    total_score: float = Field(ge=0, le=10)  # Weighted aggregate score
    recommendation: str  # Highly Recommended / Recommended / Acceptable / Avoid


class NameSuggestion(BaseModel):
    """A traditional Sanskrit name suggested for the birth chart.

    Scored against the chart and ranked by total_score.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    gender: str  # M / F / N (neutral/unisex)
    meaning: str
    deity: str  # Associated deity or divine figure
    starting_syllable: str
    score: NameScore
    is_nakshatra_match: bool  # Starts with exact birth-nakshatra syllable


class NamakaranaMuhurta(BaseModel):
    """An auspicious date/time candidate for the naming ceremony.

    Evaluated on Panchang quality: nakshatra, tithi, vara, and paksha.
    """

    model_config = ConfigDict(frozen=True)

    date: str  # DD/MM/YYYY
    day: str  # Monday, Tuesday …
    nakshatra: str
    tithi: str
    paksha: str  # Shukla / Krishna
    vara: str  # Weekday name in Sanskrit
    score: float  # Can be negative for highly inauspicious dates
    reasons: list[str]  # Human-readable scoring factors
    rahu_kaal: str  # Time window to avoid (from panchang)
    is_recommended: bool  # score >= threshold


class NamakaranaResult(BaseModel):
    """Complete Namakarana computation result for a birth chart.

    Contains the prescribed syllables, scored name suggestions, and
    auspicious Muhurta dates for the naming ceremony.
    """

    model_config = ConfigDict(frozen=True)

    birth_nakshatra: str
    birth_nakshatra_index: int = Field(ge=0, le=26)
    birth_pada: int = Field(ge=1, le=4)
    birth_rashi: str
    birth_rashi_index: int = Field(ge=0, le=11)

    # Primary naming guidance
    nakshatra_akshar: NakshtraAkshar  # The prescribed syllable for this birth
    rashi_letters: RashiLetters  # All compatible letters from rashi

    # Name suggestions ranked by score
    name_suggestions: list[NameSuggestion]

    # Auspicious timing for the ceremony
    muhurta_candidates: list[NamakaranaMuhurta]
