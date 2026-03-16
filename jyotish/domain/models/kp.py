"""KP (Krishnamurti Paddhati) data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KPPosition:
    """KP sub-lord position for a planet or cusp."""
    name: str                 # Planet name or cusp name
    longitude: float          # Sidereal longitude
    sign_lord: str            # Lord of the sign
    nakshatra_lord: str       # Star lord (nakshatra lord)
    sub_lord: str             # Sub lord
    sub_sub_lord: str         # Sub-sub lord
    nakshatra: str            # Nakshatra name
