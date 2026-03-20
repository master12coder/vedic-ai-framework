"""Domain models for Pushkara Navamsha and Pushkara Bhaga computation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PushkaraResult(BaseModel):
    """Pushkara status for a single planet.

    Pushkara Navamsha and Pushkara Bhaga are auspicious positions that
    strengthen a planet's ability to give benefic results (Phaladeepika).

    Attributes:
        planet: Planet name.
        sign_index: Sign index 0-11.
        sign: Vedic sign name.
        sign_en: English sign name.
        degree_in_sign: Planet's actual degree within the sign (0-30).
        is_pushkara_navamsha: True if planet is in a Pushkara Navamsha range.
        is_pushkara_bhaga: True if planet is within 1° of the Pushkara Bhaga.
        pushkara_bhaga_degree: The Pushkara Bhaga degree for this sign.
        pushkara_bhaga_distance: Distance from Pushkara Bhaga degree.
        pushkara_type: "bhaga" | "navamsha" | "both" | "none".
        strength_modifier: Descriptive effect on planet strength.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    degree_in_sign: float = Field(ge=0, lt=30)
    is_pushkara_navamsha: bool
    is_pushkara_bhaga: bool
    pushkara_bhaga_degree: int = Field(ge=0, le=30)
    pushkara_bhaga_distance: float = Field(ge=0)
    pushkara_type: str  # "bhaga" | "navamsha" | "both" | "none"
    strength_modifier: str  # human-readable effect description
