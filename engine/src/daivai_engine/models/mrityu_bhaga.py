"""Domain models for Mrityu Bhaga (death degree) computation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MrityuBhagaResult(BaseModel):
    """Result of a Mrityu Bhaga check for a single planet or Lagna.

    Mrityu Bhaga is the "death degree" in each sign — a specific degree
    where a planet is at extreme weakness (BPHS, Jataka Parijata).

    Attributes:
        body: Planet name or "Lagna".
        sign_index: Sign index 0-11 (Aries=0 … Pisces=11).
        sign: Vedic sign name (e.g. "Kanya").
        sign_en: English sign name (e.g. "Virgo").
        mrityu_degree: The tabulated Mrityu Bhaga degree for this body/sign.
        actual_degree: Planet's actual degree within the sign (0-30).
        distance: Absolute angular distance from Mrityu Bhaga degree.
        severity: "severe" (≤1°), "moderate" (≤3°), or "clear" (>3°).
    """

    model_config = ConfigDict(frozen=True)

    body: str
    sign_index: int = Field(ge=0, le=11)
    sign: str
    sign_en: str
    mrityu_degree: int = Field(ge=0, le=30)
    actual_degree: float = Field(ge=0, lt=30)
    distance: float = Field(ge=0)
    severity: str  # "severe" | "moderate" | "clear"
