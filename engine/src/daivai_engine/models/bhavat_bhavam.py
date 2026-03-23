"""Domain models for Bhavat Bhavam (house from house) analysis.

The Bhavat Bhavam principle states that the Nth house from the Nth house
acts as a secondary indicator for the Nth house's matters. This provides
a deeper layer of house analysis beyond the primary house signification.

Source: BPHS Ch.5, Phaladeepika Ch.1.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HousePerspective(BaseModel):
    """Snapshot of a single house's key attributes.

    Attributes:
        house_number: House number (1-12).
        sign_index: Sign index of this house (0-11).
        sign: English sign name.
        lord: Planet that lords this sign.
        lord_house: House number where the lord is placed.
        lord_dignity: Dignity of the lord in its natal position.
        planets_in_house: List of planet names occupying this house.
    """

    model_config = ConfigDict(frozen=True)

    house_number: int = Field(ge=1, le=12)
    sign_index: int = Field(ge=0, le=11)
    sign: str
    lord: str
    lord_house: int = Field(ge=1, le=12)
    lord_dignity: str
    planets_in_house: list[str]


class BhavatBhavamResult(BaseModel):
    """Bhavat Bhavam analysis for a single query house.

    Attributes:
        query_house: The house being analyzed (1-12).
        query_label: Human-readable label (e.g. "Marriage" for 7th).
        primary: The query house perspective.
        derived: The Nth-from-Nth derived house perspective.
        karaka_perspective: House perspective from the natural karaka's position.
        natural_karaka: Natural significator planet for this house.
        karaka_house: Natal house where the karaka sits.
        karaka_dignity: Dignity of the natural karaka.
        reinforcing: True if primary and derived lords are natural friends or same.
        conflicting: True if primary and derived lords are natural enemies.
        summary: Human-readable summary of the analysis.
    """

    model_config = ConfigDict(frozen=True)

    query_house: int = Field(ge=1, le=12)
    query_label: str
    primary: HousePerspective
    derived: HousePerspective
    karaka_perspective: HousePerspective | None
    natural_karaka: str
    karaka_house: int = Field(ge=1, le=12)
    karaka_dignity: str
    reinforcing: bool
    conflicting: bool
    summary: str
