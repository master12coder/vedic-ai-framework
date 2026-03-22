"""Pydantic models and sign-strength tables for varga deep analysis."""

from __future__ import annotations

from pydantic import BaseModel


__all__ = [
    "_EXALT_SIGNS",
    "_OWN_SIGNS",
    "CrossVargaResult",
    "VargaDeepResult",
]


class VargaDeepResult(BaseModel):
    """Deep analysis result for a single divisional chart."""

    varga: str  # D9, D10, D7, D12
    varga_name: str
    varga_lagna_sign: str
    varga_lagna_sign_index: int  # 0-11
    key_house_sign: str  # Most relevant house sign (7th for D9, 10th for D10, etc.)
    key_house_index: int  # House number (1-12)
    key_planets: list[str]  # Planets in the key house
    vargottama_planets: list[str]
    key_findings: list[str]
    strength: str  # strong / moderate / weak


class CrossVargaResult(BaseModel):
    """Cross-varga strength confirmation for a single planet across D1+D9+D60."""

    planet: str
    d1_sign: str
    d9_sign: str
    d60_sign: str
    in_d1_own_or_exalt: bool
    in_d9_own_or_exalt: bool
    in_d60_own_or_exalt: bool
    certainty: str  # certain / probable / possible / weak


# Own signs per planet (sign indices 0-11)
_OWN_SIGNS: dict[str, list[int]] = {
    "Sun": [4],
    "Moon": [3],
    "Mars": [0, 7],
    "Mercury": [2, 5],
    "Jupiter": [8, 11],
    "Venus": [1, 6],
    "Saturn": [9, 10],
    "Rahu": [],
    "Ketu": [],
}

# Exaltation sign index per planet
_EXALT_SIGNS: dict[str, int] = {
    "Sun": 0,  # Aries
    "Moon": 1,  # Taurus
    "Mars": 9,  # Capricorn
    "Mercury": 5,  # Virgo
    "Jupiter": 3,  # Cancer
    "Venus": 11,  # Pisces
    "Saturn": 6,  # Libra
    "Rahu": 2,  # Gemini
    "Ketu": 8,  # Sagittarius
}
