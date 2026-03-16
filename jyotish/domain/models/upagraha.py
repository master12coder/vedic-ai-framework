"""Upagraha (shadow planet) data models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UpagrahaPosition:
    """Position of an Upagraha (shadow planet)."""
    name: str
    name_hi: str
    longitude: float
    sign_index: int
    sign: str
    degree_in_sign: float
    house: int
    source_planet: str  # Which planet generates this upagraha
