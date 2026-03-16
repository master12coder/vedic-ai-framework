"""Domain models for planetary strength (Shadbala) computation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ShadbalaResult:
    """Six-fold planetary strength in shashtiyamsas.

    Each of the six components is measured in shashtiyamsas (60ths of a rupa).
    The total is compared against the planet-specific minimum to determine
    whether the planet is considered strong.
    """

    planet: str
    sthana_bala: float      # Positional (dignity, varga, house type)
    dig_bala: float         # Directional (house position)
    kala_bala: float        # Temporal (day/night, paksha, hora)
    cheshta_bala: float     # Motional (speed, retrogression)
    naisargika_bala: float  # Natural (fixed per planet)
    drik_bala: float        # Aspectual (aspects received)
    total: float            # Sum of all 6
    required: float         # Minimum required for strength
    ratio: float            # total / required (>1 = strong)
    is_strong: bool         # ratio >= 1.0
    rank: int               # Rank among planets (1 = strongest)


@dataclass
class PlanetStrength:
    """Backward-compatible simplified strength view.

    Preserves the original interface used by interpreter and formatter modules
    while delegating to the full Shadbala computation under the hood.
    """

    planet: str
    sthana_bala: float     # Positional strength (0-1)
    dig_bala: float        # Directional strength (0-1)
    kala_bala: float       # Temporal strength (0-1, simplified)
    total_relative: float  # Combined relative strength (0-1)
    rank: int              # Rank among all planets (1=strongest)
    is_strong: bool
