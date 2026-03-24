"""Domain models for birth chart data."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlanetData(BaseModel):
    """Represents a single planet's position and attributes in a Vedic birth chart.

    Contains the sidereal longitude, sign, nakshatra, house placement, dignity,
    avastha, retrograde/combust status, and other key attributes for one graha.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_hi: str
    longitude: float = Field(ge=0, lt=360)  # Sidereal longitude (0-360)
    sign_index: int = Field(ge=0, le=11)  # 0-11
    sign: str  # Vedic sign name
    sign_en: str  # Western sign name
    sign_hi: str  # Hindi sign name
    degree_in_sign: float = Field(ge=0, lt=30)  # 0-30
    nakshatra_index: int = Field(ge=0, le=26)  # 0-26
    nakshatra: str  # Nakshatra name
    nakshatra_lord: str  # Dasha lord of nakshatra
    pada: int = Field(ge=1, le=4)  # 1-4
    house: int = Field(ge=1, le=12)  # 1-12 from lagna
    is_retrograde: bool
    speed: float  # deg/day
    is_stationary: bool = False  # |speed| below threshold — extremely powerful (paused graha)
    dignity: str  # exalted/debilitated/own/mooltrikona/neutral
    avastha: str  # Bala/Kumara/Yuva/Vriddha/Mruta
    is_combust: bool
    is_cazimi: bool = False  # Within 17' of Sun — extremely powerful, not weakened
    sign_lord: str  # Lord of the sign planet is in


class ChartData(BaseModel):
    """Represents a complete Vedic birth chart (Kundali).

    Holds the native's birth details, location, computed ayanamsha, lagna (ascendant)
    information, and a dictionary of all planetary positions keyed by planet name.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    dob: str
    tob: str
    place: str
    gender: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone_name: str
    julian_day: float
    ayanamsha: float
    lagna_longitude: float = Field(ge=0, lt=360)
    lagna_sign_index: int = Field(ge=0, le=11)
    lagna_sign: str
    lagna_sign_en: str
    lagna_sign_hi: str
    lagna_degree: float = Field(ge=0, lt=30)
    planets: dict[str, PlanetData] = Field(default_factory=dict)
