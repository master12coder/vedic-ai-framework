"""Domain model for Bhrigu Bindu computation result."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BhriguBinduResult(BaseModel):
    """Bhrigu Bindu — the midpoint of Rahu and Moon.

    Bhrigu Bindu is a highly sensitive point in the chart. When a transit
    planet crosses this point, major life events are triggered. The house
    where it falls indicates the area of life most activated by transits.

    Formula: BB = (Rahu_longitude + Moon_longitude) / 2 (mod 360)

    Attributes:
        longitude: Absolute sidereal longitude of Bhrigu Bindu (0-360).
        sign_index: Sign index 0-11 (Aries=0 … Pisces=11).
        sign: Vedic sign name (e.g. "Kanya").
        sign_en: English sign name (e.g. "Virgo").
        degree_in_sign: Degree within the sign (0-30).
        house: Whole-sign house from Lagna (1-12).
        nakshatra_index: Nakshatra index 0-26.
        nakshatra: Nakshatra name (e.g. "Chitra").
        nakshatra_lord: Vimshottari dasha lord of that nakshatra.
        sign_lord: Lord of the sign where Bhrigu Bindu falls.
        rahu_longitude: Input Rahu longitude used in computation.
        moon_longitude: Input Moon longitude used in computation.
    """

    model_config = ConfigDict(frozen=True)

    longitude: float = Field(ge=0, lt=360)
    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    degree_in_sign: float = Field(ge=0, lt=30)
    house: int = Field(ge=1, le=12)
    nakshatra_index: int = Field(ge=0, le=26)
    nakshatra: str
    nakshatra_lord: str
    sign_lord: str
    rahu_longitude: float = Field(ge=0, lt=360)
    moon_longitude: float = Field(ge=0, lt=360)
