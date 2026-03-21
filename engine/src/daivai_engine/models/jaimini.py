"""Domain models for Jaimini astrology system."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CharaKaraka(BaseModel):
    """Represents a Chara (movable) Karaka in the Jaimini system.

    Chara Karakas are determined by planetary degrees within their signs,
    unlike fixed Parashari karakas. The planet with the highest degree
    becomes Atmakaraka (soul significator).
    """

    model_config = ConfigDict(frozen=True)

    karaka: str  # AK, AmK, BK, MK, PK, GK, DK
    karaka_full: str  # Atmakaraka, Amatyakaraka, etc.
    karaka_hi: str  # Hindi name in Devanagari
    planet: str  # Planet name
    degree_in_sign: float = Field(ge=0, lt=30)  # Degree within the sign (0-30)


class ArudhaPada(BaseModel):
    """Represents an Arudha Pada (A1-A12) for a house.

    The Arudha Pada is the image or projection of a house, calculated
    by counting from the house to its lord, then the same distance
    from the lord.
    """

    model_config = ConfigDict(frozen=True)

    house: int = Field(ge=1, le=12)  # 1-12
    name: str  # A1, A2... A12
    sign_index: int = Field(ge=0, le=11)  # 0-11
    sign: str  # Sign name (Vedic)


class JaiminiRajYoga(BaseModel):
    """A Raj (kingly) Yoga detected in the Jaimini system.

    Jaimini Raj Yogas differ from Parashari — they are based on sign aspects,
    Chara Karakas, and Arudha Lagna rather than house lords.

    Source: Jaimini Upadesha Sutras, B.V. Raman Studies in Jaimini Astrology.
    """

    model_config = ConfigDict(frozen=True)

    name: str  # e.g. "AK-AmK Conjunction"
    name_hi: str  # Hindi name
    is_present: bool
    description: str
    planets_involved: list[str]
    strength: str  # strong / moderate / weak


class JaiminiResult(BaseModel):
    """Complete Jaimini analysis result for a chart.

    Aggregates Chara Karakas, Arudha Padas, Karakamsha, and Raj Yogas
    into a single result object.
    """

    model_config = ConfigDict(frozen=True)

    chara_karakas: list[CharaKaraka]
    arudha_padas: list[ArudhaPada]
    karakamsha_sign_index: int = Field(ge=0, le=11)  # 0-11
    karakamsha_sign: str  # Sign name (Vedic)
    atmakaraka: str  # Planet name of Atmakaraka
    darakaraka: str  # Planet name of Darakaraka
    raj_yogas: list[JaiminiRajYoga] = Field(default_factory=list)
