"""Domain models for planetary avastha (state/condition) systems."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ShayanadiAvastha(BaseModel):
    """12-state positional avastha from BPHS Ch.45.

    Based on the planet's degree position within its sign (odd vs even sign
    determines the sequence direction). Each 2.5° zone = one of 12 states.

    Positive states (give good results): Prakasha, Gamana, Sabha, Aagama, Bhojana,
    Nrityalipsya, Kautuka.
    Negative states (give poor results): Shayana, Upavesha, Netrapani, Agama, Nidra.

    Source: BPHS Chapter 45 v21-35.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    avastha: str  # one of the 12 states
    avastha_hi: str
    zone: int  # 1-12 (position within the sign)
    is_positive: bool
    result_summary: str  # Classical result from BPHS
    strength_fraction: float  # 0.0 to 1.0 (used in strength calculations)


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
