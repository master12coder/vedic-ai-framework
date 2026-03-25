"""Domain models for cross-chart (synastry) planetary interactions."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlanetOverlay(BaseModel):
    """One planet from chart_a near a position in chart_b.

    Records the degree orb, interaction type (conjunction, opposition, trine),
    and the qualitative effect of this cross-chart contact.
    """

    model_config = ConfigDict(frozen=True)

    person_a_name: str
    person_b_name: str
    planet_a: str
    planet_b: str  # planet name, or "Lagna" for axis contacts
    sign: str  # Sign where the interaction occurs
    orb_degrees: float = Field(ge=0)
    interaction_type: str  # "conjunction", "opposition", "trine", "square", "sextile"
    effect: str  # "supportive", "challenging", "karmic", "neutral"
    description: str


class CrossChartResult(BaseModel):
    """Complete cross-chart analysis between two people.

    Organises overlays by category: generic planet-on-planet overlays,
    contacts to the other person's Moon (emotional influence), axis contacts
    (Lagnesh-on-Moon, 7th-lord-on-Lagna), and karmic links (Saturn/Rahu
    contacts that indicate deep karmic bonds).
    """

    model_config = ConfigDict(frozen=True)

    person_a: str
    person_b: str
    overlays: list[PlanetOverlay] = Field(default_factory=list)
    moon_contacts: list[PlanetOverlay] = Field(default_factory=list)
    axis_contacts: list[PlanetOverlay] = Field(default_factory=list)
    karmic_links: list[PlanetOverlay] = Field(default_factory=list)
    bond_strength: float = Field(ge=0, le=100)  # Composite score
    summary: str
