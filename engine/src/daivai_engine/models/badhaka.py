"""Domain models for Badhaka Sthana (house of obstruction) computation.

The Badhaka house and its lord (Badhakesh) indicate the primary source of
obstruction in a native's life. The specific house depends on the modality
(movable / fixed / dual) of the Lagna sign.

Source: BPHS Ch.44-45, Jaimini Sutras.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BadhakaResult(BaseModel):
    """Complete Badhaka analysis for a birth chart.

    Attributes:
        lagna_sign_index: Lagna sign index (0=Aries .. 11=Pisces).
        lagna_modality: Modality of the lagna — "movable", "fixed", or "dual".
        badhaka_house: The obstructing house number (7, 9, or 11).
        badhaka_sign_index: Sign index of the Badhaka house.
        badhaka_sign: English name of the Badhaka sign.
        badhakesh: Planet that lords the Badhaka sign.
        badhakesh_house: Natal house where the Badhakesh is placed.
        badhakesh_sign_index: Sign index where Badhakesh sits.
        badhakesh_dignity: Dignity of the Badhakesh in its natal position.
        badhakesh_retrograde: True if the Badhakesh is retrograde.
        rahu_conjunct_badhakesh: Rahu in the same house as Badhakesh.
        ketu_conjunct_badhakesh: Ketu in the same house as Badhakesh.
        rahu_in_badhaka_house: Rahu placed in the Badhaka house.
        ketu_in_badhaka_house: Ketu placed in the Badhaka house.
        planets_in_badhaka_house: Planets occupying the Badhaka house.
        badhakesh_aspects_lagna: True if Badhakesh aspects the lagna house.
        obstruction_severity: "mild", "moderate", or "severe".
        obstruction_domains: Life domains affected (e.g. ["career", "marriage"]).
        summary: Human-readable summary of the obstruction pattern.
    """

    model_config = ConfigDict(frozen=True)

    lagna_sign_index: int = Field(ge=0, le=11)
    lagna_modality: str
    badhaka_house: int
    badhaka_sign_index: int = Field(ge=0, le=11)
    badhaka_sign: str
    badhakesh: str
    badhakesh_house: int = Field(ge=1, le=12)
    badhakesh_sign_index: int = Field(ge=0, le=11)
    badhakesh_dignity: str
    badhakesh_retrograde: bool
    rahu_conjunct_badhakesh: bool
    ketu_conjunct_badhakesh: bool
    rahu_in_badhaka_house: bool
    ketu_in_badhaka_house: bool
    planets_in_badhaka_house: list[str]
    badhakesh_aspects_lagna: bool
    obstruction_severity: str
    obstruction_domains: list[str]
    summary: str
