"""Domain models for planetary avastha (state/condition) systems."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DeeptadiAvastha(BaseModel):
    """9-state planetary condition from BPHS Ch.45.

    Based on dignity, combustion, and planetary war status.
    Each state has a strength multiplier affecting the planet's results.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    avastha: str  # deepta/swastha/mudita/shanta/deena/vikala/dukhita/kala/kopa
    avastha_hi: str
    description: str
    strength_multiplier: float  # 0.0 to 1.5


class LajjitadiAvastha(BaseModel):
    """6-state planetary dignity from BPHS Ch.45.

    Based on house position, conjunctions, and aspects received.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    avastha: str  # lajjita/garvita/kshudhita/trushita/mudita/kshobhita
    avastha_hi: str
    description: str
    is_positive: bool
