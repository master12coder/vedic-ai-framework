"""Domain models for dispositor tree computation.

A dispositor is the lord of the sign a planet occupies. Tracing each planet's
dispositor chain reveals the ultimate "ruler" of the chart — the final
dispositor — and any mutual reception pairs (parivartana).

Source: BPHS Ch.13, Phaladeepika Ch.2.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DispositorLink(BaseModel):
    """Single link in a dispositor chain.

    Attributes:
        planet: Name of the planet (e.g. "Mars").
        sign_index: Sign index (0-11) the planet occupies.
        dispositor: Lord of that sign — the next link in the chain.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    sign_index: int = Field(ge=0, le=11)
    dispositor: str


class PlanetDispositorChain(BaseModel):
    """Full dispositor chain for a single planet.

    The chain traces: planet -> its dispositor -> that dispositor's dispositor
    -> ... -> terminal (planet in own sign or mutual loop).

    Attributes:
        planet: Starting planet of this chain.
        chain: Ordered list from planet through each dispositor to terminus.
        final_dispositor: Planet where the chain terminates.
        chain_length: Number of links (len(chain) - 1).
        is_in_loop: True if the chain enters a mutual reception loop.
    """

    model_config = ConfigDict(frozen=True)

    planet: str
    chain: list[str]
    final_dispositor: str
    chain_length: int = Field(ge=0)
    is_in_loop: bool


class MutualReception(BaseModel):
    """Mutual reception (parivartana) between two planets.

    Planet A occupies a sign owned by planet B, and planet B occupies
    a sign owned by planet A.

    Attributes:
        planet_a: First planet in the exchange.
        planet_b: Second planet in the exchange.
        sign_a: Sign index that planet_a occupies (owned by planet_b).
        sign_b: Sign index that planet_b occupies (owned by planet_a).
    """

    model_config = ConfigDict(frozen=True)

    planet_a: str
    planet_b: str
    sign_a: int = Field(ge=0, le=11)
    sign_b: int = Field(ge=0, le=11)


class DispositorTree(BaseModel):
    """Complete dispositor analysis for all planets in a chart.

    Attributes:
        chains: Dispositor chain for each planet, keyed by planet name.
        final_dispositors: Unique list of terminal dispositor planets.
        mutual_receptions: All mutual reception pairs found.
        has_single_final_dispositor: True if all chains converge to one planet.
        summary: Human-readable summary of the dispositor structure.
    """

    model_config = ConfigDict(frozen=True)

    chains: dict[str, PlanetDispositorChain]
    final_dispositors: list[str]
    mutual_receptions: list[MutualReception]
    has_single_final_dispositor: bool
    summary: str
