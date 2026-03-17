"""Domain models for Jaimini astrology system."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CharaKaraka:
    """Represents a Chara (movable) Karaka in the Jaimini system.

    Chara Karakas are determined by planetary degrees within their signs,
    unlike fixed Parashari karakas. The planet with the highest degree
    becomes Atmakaraka (soul significator).
    """

    karaka: str  # AK, AmK, BK, MK, PK, GK, DK
    karaka_full: str  # Atmakaraka, Amatyakaraka, etc.
    karaka_hi: str  # Hindi name in Devanagari
    planet: str  # Planet name
    degree_in_sign: float  # Degree within the sign (0-30)


@dataclass
class ArudhaPada:
    """Represents an Arudha Pada (A1-A12) for a house.

    The Arudha Pada is the image or projection of a house, calculated
    by counting from the house to its lord, then the same distance
    from the lord.
    """

    house: int  # 1-12
    name: str  # A1, A2... A12
    sign_index: int  # 0-11
    sign: str  # Sign name (Vedic)


@dataclass
class JaiminiResult:
    """Complete Jaimini analysis result for a chart.

    Aggregates Chara Karakas, Arudha Padas, and Karakamsha
    into a single result object.
    """

    chara_karakas: list[CharaKaraka]
    arudha_padas: list[ArudhaPada]
    karakamsha_sign_index: int  # 0-11
    karakamsha_sign: str  # Sign name (Vedic)
    atmakaraka: str  # Planet name of Atmakaraka
    darakaraka: str  # Planet name of Darakaraka
