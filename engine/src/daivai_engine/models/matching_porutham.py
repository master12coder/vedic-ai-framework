"""Domain models for South Indian 10-Porutham marriage matching."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PouruthamItem(BaseModel):
    """Result of a single Porutham compatibility check.

    Each porutham is either agreed (compatible) or disagreed (incompatible).
    Eliminatory poruthams (Rajju, Vedha) block the match regardless of total score.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    name_tamil: str
    agrees: bool
    is_eliminatory: bool
    description: str
    exception_note: str = ""


class PouruthamResult(BaseModel):
    """Complete South Indian 10-Porutham marriage compatibility result.

    Contains all 10 poruthams with pass/fail status, eliminatory dosha flags,
    and an overall recommendation. Rajju and Vedha are eliminatory — their
    presence marks the match as not recommended regardless of agreed_count.

    Minimum 6 of 10 poruthams must agree for a recommended match.
    """

    model_config = ConfigDict(frozen=True)

    boy_nakshatra_index: int = Field(ge=0, le=26)
    girl_nakshatra_index: int = Field(ge=0, le=26)
    boy_moon_sign: int = Field(ge=0, le=11)
    girl_moon_sign: int = Field(ge=0, le=11)
    poruthams: list[PouruthamItem]
    agreed_count: int = Field(ge=0)
    total_count: int = Field(default=10)
    has_rajju_dosha: bool
    has_vedha_dosha: bool
    rajju_body_part: str | None  # Paada/Kati/Nabhi/Kantha/Shira (None if no dosha)
    rajju_severity: str  # none / mild / moderate / severe
    is_recommended: bool
    recommendation: str
