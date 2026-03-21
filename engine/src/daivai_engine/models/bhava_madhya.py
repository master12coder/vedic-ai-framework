"""Domain models for Sripati Paddhati Bhava Madhya and Sandhi analysis.

In Sripati Paddhati (11th century):
- ASC degree = Madhya (midpoint/center) of Bhava 1
- MC degree = Madhya of Bhava 10
- IC (MC+180°) = Madhya of Bhava 4
- DSC (ASC+180°) = Madhya of Bhava 7
- Intermediate Madhyas found by trisecting each quadrant arc
- Sandhi = midpoint between consecutive Madhyas = house boundary
- Planet in Sandhi = within SANDHI_THRESHOLD of any boundary

Source: Sripati Paddhati; BPHS Ch.27 Shadbala commentary.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BhavaMadhya(BaseModel):
    """Center and boundary data for a single Bhava in Sripati system.

    Each Bhava has:
    - A Madhya (center longitude) — the most powerful point of the house
    - A Sandhi (end boundary) — midpoint to the next Madhya, where house strength wanes
    """

    model_config = ConfigDict(frozen=True)

    house: int = Field(ge=1, le=12)
    madhya_longitude: float = Field(ge=0, lt=360)  # Center of this Bhava (sidereal)
    sandhi_longitude: float = Field(ge=0, lt=360)  # Boundary end: midpoint to next Madhya
    arc_span: float = Field(gt=0, lt=360)  # Total arc of this house in degrees


class PlanetSandhiStatus(BaseModel):
    """Planet's placement relative to Bhava Madhya and Sandhi in Sripati system.

    A planet near a Sandhi gives mixed results — it is pulled between two houses.
    A planet close to the Madhya is most fully expressive of that house's significations.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    bhava: int = Field(ge=1, le=12)  # Sripati house this planet falls in
    distance_to_madhya: float = Field(ge=0)  # Degrees from this Bhava's Madhya
    distance_to_sandhi: float = Field(ge=0)  # Degrees to nearest house boundary
    is_in_sandhi: bool  # True if within SANDHI_THRESHOLD (3°20') of a boundary
    prev_house: int = Field(ge=1, le=12)  # House on the prior-boundary side
    next_house: int = Field(ge=1, le=12)  # House on the next-boundary side


class SripatiBhavaMadhyaResult(BaseModel):
    """Complete Sripati Paddhati Bhava Madhya and Sandhi analysis.

    Contains the 12 Bhava Madhyas, their Sandhi boundaries, and per-planet
    assessment of whether each graha is in a Sandhi zone.
    """

    model_config = ConfigDict(frozen=True)

    bhavas: dict[int, BhavaMadhya]  # keyed by house number 1-12
    planet_status: dict[str, PlanetSandhiStatus]  # keyed by planet name
    method: str = "Sripati Paddhati"
