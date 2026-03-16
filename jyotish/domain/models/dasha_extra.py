"""Additional dasha system data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class YoginiDashaPeriod:
    """A Yogini Dasha period."""
    yogini_name: str       # Mangala, Pingala, Dhanya, etc.
    planet: str            # Associated planet
    years: int             # Duration in years
    start: datetime
    end: datetime


@dataclass
class AshtottariDashaPeriod:
    """An Ashtottari Dasha period."""
    planet: str
    years: int
    start: datetime
    end: datetime


@dataclass
class CharaDashaPeriod:
    """A Chara (Jaimini) sign-based dasha period."""
    sign: str
    sign_index: int
    years: float
    start: datetime
    end: datetime
