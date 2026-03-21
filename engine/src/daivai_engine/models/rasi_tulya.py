"""Models for Rasi Tulya Navamsha (RTN) analysis."""

from __future__ import annotations

from pydantic import BaseModel


class RTNPlanet(BaseModel):
    """RTN data for a single planet.

    Records the D1 and D9 sign, the sign distance between them,
    the classified relationship, Pushkara status, and timing note.
    """

    planet: str
    d1_sign_index: int  # 0-11
    d9_sign_index: int  # 0-11
    d1_sign: str
    d9_sign: str
    sign_distance: int  # 0-11 (forward distance from D1 to D9)
    relationship: str  # vargottama / kendra / trikona / dusthana / neutral
    is_pushkara_navamsha: bool
    pushkara_type: str  # none / navamsha / bhaga / both
    timing_note: str


class RTNResult(BaseModel):
    """Rasi Tulya Navamsha analysis for all planets in a chart."""

    planets: list[RTNPlanet]
    vargottama_planets: list[str]  # D1 sign == D9 sign
    pushkara_planets: list[str]  # Any Pushkara type != "none"
    summary: str
