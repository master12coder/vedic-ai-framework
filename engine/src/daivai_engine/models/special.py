"""Domain models for special chart features — gandanta, graha yuddha, upapada."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GandantaResult(BaseModel):
    """Water-fire sign junction check.

    Gandanta = last 3 deg 20 min of water sign to first 3 deg 20 min of fire sign.
    Moon or Lagna in gandanta has significant implications.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    is_gandanta: bool
    gandanta_type: str | None = None  # nakshatra_gandanta / rashi_gandanta
    junction: str | None = None  # e.g. "Jyeshtha-Moola"
    degree: float | None = None
    severity: str | None = None  # mild / severe
    remedial_note: str | None = None


class GrahaYuddha(BaseModel):
    """Planetary war — two planets within 1 degree.

    Only Mars, Mercury, Jupiter, Venus, Saturn participate.
    Winner = planet with higher longitude (in same sign context).
    Loser's significations and owned houses get damaged.
    """

    model_config = ConfigDict(frozen=True)

    planet1: str
    planet2: str
    separation_degrees: float
    winner: str
    loser: str
    is_exact: bool  # Within 0 deg 10 min
    affected_houses: list[int]  # Houses owned by the loser


class UpapadaLagna(BaseModel):
    """Jaimini marriage indicator — Arudha of the 12th house.

    The sign arrived at by counting the distance of the 12th lord
    from the 12th house, then counting that same distance from the lord.
    """

    model_config = ConfigDict(frozen=True)

    sign_index: int
    sign_hi: str
    sign_en: str
    lord: str
    lord_house: int  # House where upapada lord sits
    planets_in_upapada: list[str]
    marriage_indication: str  # favorable / delayed / challenging


class DoubleTransit(BaseModel):
    """Jupiter + Saturn must both aspect a house for major event.

    The primary timing technique used by professional astrologers.
    """

    model_config = ConfigDict(frozen=True)

    house: int
    house_name_hi: str
    jupiter_aspects: bool
    saturn_aspects: bool
    is_active: bool  # Both True = double transit active
    event_potential: str


class VedhaPoint(BaseModel):
    """Obstruction point that blocks transit benefit."""

    model_config = ConfigDict(frozen=True)

    benefic_house: int
    vedha_house: int
    is_blocked: bool
    blocking_planet: str | None = None


class MoorthyNirnaya(BaseModel):
    """Transit quality classification from SAV bindus."""

    model_config = ConfigDict(frozen=True)

    planet: str
    transit_sign: int
    bindus: int
    classification: str  # swarna / rajata / tamra / loha
    classification_hi: str  # स्वर्ण / रजत / ताम्र / लोह
