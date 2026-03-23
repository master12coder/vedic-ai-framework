"""Domain models for Kota Chakra (fortress diagram) analysis.

Kota Chakra arranges 28 nakshatras (27 standard + Abhijit) in 4 concentric
rings around the natal Moon's nakshatra (Kota Swami). Used in Tajaka (annual
chart) transit analysis to assess fortress integrity.

Source: Tajaka Neelakanthi.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KotaNakshatra(BaseModel):
    """A nakshatra placed in one of the four Kota Chakra rings."""

    model_config = ConfigDict(frozen=True)

    nakshatra_index: int = Field(ge=0, le=27)
    nakshatra_name: str
    ring: str  # "stambha" / "madhya" / "prakaara" / "bahya"
    is_dvara: bool
    position_from_swami: int = Field(ge=0, le=27)


class KotaPlanetPosition(BaseModel):
    """A planet's position within the Kota Chakra fortress."""

    model_config = ConfigDict(frozen=True)

    planet: str
    nakshatra_name: str
    ring: str  # "stambha" / "madhya" / "prakaara" / "bahya"
    is_at_dvara: bool
    is_benefic: bool
    effect: str  # "protective" / "threatening" / "neutral"


class KotaChakraResult(BaseModel):
    """Complete Kota Chakra analysis result.

    Contains the fortress layout, transit planet positions, and an overall
    assessment of the fort's integrity.
    """

    model_config = ConfigDict(frozen=True)

    kota_swami_nakshatra: str
    kota_swami_index: int

    ring_layout: dict[str, list[KotaNakshatra]]

    transit_positions: list[KotaPlanetPosition]

    stambha_threatened: bool
    dvara_breached: bool
    overall_strength: str  # "fortified" / "stable" / "vulnerable" / "breached"

    summary: str
