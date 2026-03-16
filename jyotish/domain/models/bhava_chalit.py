"""Domain models for Bhava Chalit chart computation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BhavaPlanet:
    """Planet's Bhava Chalit position.

    Compares the planet's whole-sign (Rashi) house placement with its
    Placidus-based Bhava Chalit house placement, flagging any shift.
    """

    name: str
    rashi_house: int       # House in Rashi chart (whole sign)
    bhava_house: int       # House in Bhava Chalit
    has_bhava_shift: bool  # True if rashi_house != bhava_house
    cusp_longitude: float  # Nearest cusp longitude (sidereal)


@dataclass
class BhavaChalitResult:
    """Bhava Chalit house positions.

    Contains the 12 sidereal house cusp longitudes and per-planet
    Bhava Chalit placements derived from Placidus cusps.
    """

    cusps: list[float]                  # 12 house cusp longitudes (sidereal)
    planets: dict[str, BhavaPlanet]     # keyed by planet name
