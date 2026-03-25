"""Domain models for functional nature classification of planets per lagna."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FunctionalNature(BaseModel):
    """Functional classification of a planet for a specific lagna.

    Per BPHS lordship principles: Kendra/Trikona lords gain beneficence,
    Dusthana lords are malefic, Maraka lords (2nd/7th) inflict death-like
    events, and Yogakaraka planets own both a kendra and a trikona.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    lagna_sign: str
    classification: str  # "benefic", "malefic", "yogakaraka", "maraka", "neutral"
    houses_owned: list[int]
    reasoning: str
    is_maraka: bool = False
    is_yogakaraka: bool = False


class ShadowPlanetNature(BaseModel):
    """Rahu/Ketu functional nature resolved via sign lord (rashyadhipati).

    BPHS principle: "छाया ग्रह जिस राशि में हो, उस राशि के स्वामी का फल देता है"
    Shadow planets give results of the lord of the sign they occupy.

    For gemstone safety: if sign lord is a functional benefic for the lagna,
    Gomed (Rahu) or Lehsunia (Ketu) is safe to wear. If sign lord is a
    functional malefic or maraka, the stone carries risk.
    """

    model_config = ConfigDict(frozen=True)

    shadow_planet: str  # "Rahu" or "Ketu"
    sign_index: int  # 0-11 sign Rahu/Ketu occupies
    sign_name: str  # e.g., "Dhanu"
    sign_lord: str  # Classical lord of the sign (e.g., "Jupiter")
    sign_lord_nature: FunctionalNature
    gemstone_safety: str  # "safe", "unsafe", "test_with_caution"
    gemstone_name: str  # "Hessonite (Gomed)" or "Cat's Eye (Lehsunia)"
    reasoning: str
