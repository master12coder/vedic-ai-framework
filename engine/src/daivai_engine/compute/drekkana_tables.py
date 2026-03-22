"""Drekkana (D3) tables, models, and constants for sibling analysis."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


# Nature classification for each of the 36 Drekkanas
# Indexed as (sign_index, part): 0=first 10°, 1=second 10°, 2=third 10°
# Nature: "human" / "quadruped" / "serpent" / "mixed"
# Source: BPHS Ch.27 v1-36 (Drekkana forms), Saravali commentary
_DREKKANA_NATURE: dict[tuple[int, int], str] = {
    # Mesha (0)
    (0, 0): "human",  # 1st: male with weapon (Agni)
    (0, 1): "serpent",  # 2nd: serpentine Naga form
    (0, 2): "human",  # 3rd: woman on throne
    # Vrishabha (1)
    (1, 0): "human",  # 1st: farmer/cultivator
    (1, 1): "serpent",  # 2nd: serpent form
    (1, 2): "quadruped",  # 3rd: bull form
    # Mithuna (2)
    (2, 0): "human",  # 1st: couple (man+woman)
    (2, 1): "human",  # 2nd: woman playing veena
    (2, 2): "serpent",  # 3rd: serpent/Naga (commonly cited)
    # Karka (3)
    (3, 0): "serpent",  # 1st: serpent/crab (water sign Sarpa)
    (3, 1): "human",  # 2nd: woman with flowers
    (3, 2): "human",  # 3rd: horse rider
    # Simha (4)
    (4, 0): "quadruped",  # 1st: lion
    (4, 1): "human",  # 2nd: man in forest
    (4, 2): "quadruped",  # 3rd: elephant
    # Kanya (5)
    (5, 0): "human",  # 1st: woman
    (5, 1): "human",  # 2nd: man with bow
    (5, 2): "human",  # 3rd: man with scales
    # Tula (6)
    (6, 0): "human",  # 1st: merchant with scales
    (6, 1): "human",  # 2nd: vulture / eagle form
    (6, 2): "human",  # 3rd: man with armor
    # Vrischika (7)
    (7, 0): "serpent",  # 1st: serpent (water sign Sarpa)
    (7, 1): "serpent",  # 2nd: scorpion/serpent form
    (7, 2): "human",  # 3rd: woman with lotus
    # Dhanu (8)
    (8, 0): "human",  # 1st: archer on horseback
    (8, 1): "quadruped",  # 2nd: horse form
    (8, 2): "human",  # 3rd: man with gold ornaments
    # Makara (9)
    (9, 0): "mixed",  # 1st: half animal / Makara (sea creature)
    (9, 1): "human",  # 2nd: woman adorned
    (9, 2): "quadruped",  # 3rd: goat form
    # Kumbha (10)
    (10, 0): "human",  # 1st: man with pot
    (10, 1): "human",  # 2nd: woman
    (10, 2): "human",  # 3rd: man with chains (karma)
    # Meena (11)
    (11, 0): "serpent",  # 1st: serpent/fish (water sign Sarpa)
    (11, 1): "human",  # 2nd: man swimming
    (11, 2): "mixed",  # 3rd: fish form
}

# Drekkana classical names (partial — most notable ones)
# From Parashara's 36-Drekkana descriptions
_DREKKANA_NAMES: dict[tuple[int, int], str] = {
    (0, 0): "Agni Drekkana",
    (0, 1): "Naga Drekkana",
    (0, 2): "Yaksha Drekkana",
    (1, 0): "Bhumi Drekkana",
    (1, 1): "Sarpa Drekkana",
    (1, 2): "Vrisha Drekkana",
    (2, 0): "Mithuna Drekkana",
    (2, 1): "Vana Drekkana",
    (2, 2): "Naga Drekkana",
    (3, 0): "Sarpa Drekkana",
    (3, 1): "Jala Drekkana",
    (3, 2): "Vaja Drekkana",
    (4, 0): "Simha Drekkana",
    (4, 1): "Aranya Drekkana",
    (4, 2): "Gaja Drekkana",
    (5, 0): "Kanya Drekkana",
    (5, 1): "Dhanu Drekkana",
    (5, 2): "Tula Drekkana",
    (6, 0): "Vanija Drekkana",
    (6, 1): "Shyena Drekkana",
    (6, 2): "Kavachi Drekkana",
    (7, 0): "Sarpa Drekkana",
    (7, 1): "Vrishchika Drekkana",
    (7, 2): "Padma Drekkana",
    (8, 0): "Chakra Drekkana",
    (8, 1): "Turaga Drekkana",
    (8, 2): "Swarna Drekkana",
    (9, 0): "Makara Drekkana",
    (9, 1): "Nari Drekkana",
    (9, 2): "Chaga Drekkana",
    (10, 0): "Kumbha Drekkana",
    (10, 1): "Jala Drekkana",
    (10, 2): "Bandha Drekkana",
    (11, 0): "Sarpa Drekkana",
    (11, 1): "Jala Drekkana",
    (11, 2): "Matsya Drekkana",
}

# Sibling indication per Drekkana nature
_NATURE_SIBLING_INDICATION: dict[str, str] = {
    "human": "Strong human qualities in sibling; intellectual or artistic nature.",
    "quadruped": "Sibling may be sturdy, hardworking, connected to land/animals.",
    "serpent": "Complex sibling relationship; secrecy or hidden aspects; possible estrangement.",
    "mixed": "Mixed relationship; sibling has dual nature or unconventional path.",
}


class DrekkanaPosition(BaseModel):
    """A planet's Drekkana (D3) position with classical attributes."""

    model_config = ConfigDict(frozen=True)

    planet: str
    natal_sign_index: int = Field(ge=0, le=11)
    natal_sign: str
    natal_degree: float
    drekkana_part: int = Field(ge=0, le=2)  # 0=first 10°, 1=second 10°, 2=third 10°
    d3_sign_index: int = Field(ge=0, le=11)
    d3_sign: str
    d3_sign_en: str
    d3_lord: str  # Lord of the D3 sign
    drekkana_name: str  # Classical name
    nature: str  # human/quadruped/serpent/mixed
    is_sarpa_drekkana: bool
    sibling_indication: str


class SiblingAnalysis(BaseModel):
    """3rd-house and D3-based sibling analysis."""

    model_config = ConfigDict(frozen=True)

    third_house_lord: str  # Lord of 3rd house in natal chart
    third_house_lord_d3_sign: str  # Where 3rd lord is in D3
    third_house_occupants: list[str]  # Planets in 3rd house (natal)
    d3_third_house_occupants: list[str]  # Planets in 3rd in D3
    sibling_count_indication: str  # Based on 3rd house indicators
    sibling_nature: str  # From drekkana analysis
    has_sarpa_drekkana: bool  # Any planet in 3rd in Sarpa Drekkana
    strength: str  # strong/moderate/weak (for sibling matters)


class DrekkanaAnalysisResult(BaseModel):
    """Complete D3 Drekkana analysis for all planets."""

    model_config = ConfigDict(frozen=True)

    all_positions: list[DrekkanaPosition]
    sibling_analysis: SiblingAnalysis
    sarpa_drekkana_planets: list[str]  # Planets in Sarpa Drekkanas
