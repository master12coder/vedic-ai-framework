"""Domain models for Argala (Intervention) and Virodha Argala (Obstruction).

Argala describes how planets in specific positions relative to a house or sign
'intervene' and support or harm the results of that house/sign.
Virodha Argala is the counter-force that can neutralize the intervention.

Source: BPHS Chapter 31 (Parashara), Jaimini Sutras 1.1.10-15.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ArgalaSource(BaseModel):
    """Argala from one specific position relative to a house or sign.

    Each primary argala position (2nd, 4th, 11th) has a corresponding
    obstruction position (12th, 10th, 3rd). The 5th (Putra) argala
    has the 9th as its obstruction.

    Obstruction is effective only when the number of obstructing planets
    is greater than or equal to the number of argala planets (BPHS Ch.31, v.9).

    Source: BPHS Chapter 31, v.1-9.
    """

    model_config = ConfigDict(frozen=True)

    argala_type: str  # "dhana", "sukha", "labha", "putra"
    argala_name: str  # e.g. "Dhana Argala"
    argala_name_hi: str  # Hindi name in Devanagari
    offset: int  # Position from target (1-indexed): 2, 4, 11, or 5
    planets: list[str]  # Planets providing argala
    obstruction_offset: int  # Obstruction position (1-indexed): 12, 10, 3, or 9
    obstructing_planets: list[str]  # Planets obstructing this argala
    is_obstructed: bool  # True if len(obstructors) >= len(argala planets) > 0
    is_effective: bool  # True if has planets AND not obstructed
    nature: str  # "shubha" (benefic), "ashubha" (malefic), "mishra" (mixed), "empty"


class ArgalaResult(BaseModel):
    """Complete Argala analysis for one house (Parashari house-based system).

    Analyzes all four argala types relative to the house (Dhana, Sukha,
    Labha, Putra) and their corresponding Virodha (obstructions).

    Used in Parashari chart reading to determine which houses receive
    planetary support and what nature that support is.

    Source: BPHS Chapter 31.
    """

    model_config = ConfigDict(frozen=True)

    house: int = Field(ge=1, le=12)  # Target house number (1-12)
    sign_index: int = Field(ge=0, le=11)  # Sign occupied by this house (0-11)
    argalas: list[ArgalaSource]  # All 4 argala type analyses
    net_argala_count: int = Field(ge=0)  # Number of unobstructed, effective argalas
    benefic_argala_count: int = Field(ge=0)  # Shubha (benefic) effective argalas
    malefic_argala_count: int = Field(ge=0)  # Ashubha (malefic) effective argalas
    is_supported: bool  # True if net_argala_count > 0


class SignArgalaResult(BaseModel):
    """Argala analysis for one sign (Jaimini sign-based system).

    In Jaimini astrology, Argala is computed sign-to-sign (rashi-to-rashi)
    rather than house-to-house. This makes it independent of the Lagna
    position and is used primarily in Chara Dasha and Padakrama analysis.

    Source: Jaimini Sutras 1.1.10-15, B.V. Raman 'Studies in Jaimini Astrology'.
    """

    model_config = ConfigDict(frozen=True)

    sign_index: int = Field(ge=0, le=11)  # Sign index (0-11)
    sign: str  # Sign name (Vedic, e.g. "Mesha")
    argalas: list[ArgalaSource]  # All 4 argala type analyses
    net_argala_count: int = Field(ge=0)  # Unobstructed effective argalas
    benefic_argala_count: int = Field(ge=0)  # Shubha argalas
    malefic_argala_count: int = Field(ge=0)  # Ashubha argalas
    is_supported: bool  # True if net_argala_count > 0
