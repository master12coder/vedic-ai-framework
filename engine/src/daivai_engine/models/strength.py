"""Domain models for planetary strength (Shadbala) computation."""

from __future__ import annotations

from pydantic import BaseModel


class ShadbalaResult(BaseModel):
    """Six-fold planetary strength in shashtiyamsas.

    Each of the six components is measured in shashtiyamsas (60ths of a rupa).
    The total is compared against the planet-specific minimum to determine
    whether the planet is considered strong.
    """

    planet: str
    sthana_bala: float  # Positional (dignity, varga, house type)
    dig_bala: float  # Directional (house position)
    kala_bala: float  # Temporal (day/night, paksha, hora)
    cheshta_bala: float  # Motional (speed, retrogression)
    naisargika_bala: float  # Natural (fixed per planet)
    drik_bala: float  # Aspectual (aspects received)
    yuddha_bala: float = 0.0  # Planetary war adjustment (+60 winner, -60 loser)
    total: float  # Sum of all 6 + yuddha_bala
    required: float  # Minimum required for strength
    ratio: float  # total / required (>1 = strong)
    is_strong: bool  # ratio >= 1.0
    rank: int  # Rank among planets (1 = strongest)


class IshtaKashtaPhala(BaseModel):
    """Good/bad results derived from Shadbala.

    Ishta Phala = benefic potential, Kashta Phala = malefic potential.
    Net effect positive means planet gives more good than harm.
    Source: BPHS Chapter 27.
    """

    planet: str
    ishta_phala: float  # Benefic potential (0-60)
    kashta_phala: float  # Malefic potential (0-60)
    net_effect: float  # ishta - kashta
    classification: str  # strongly_benefic/mildly_benefic/neutral/mildly_malefic/strongly_malefic


class VimshopakaBala(BaseModel):
    """Strength of planet across divisional charts.

    Evaluates planet dignity in up to 16 vargas with weighted scoring.
    Source: BPHS Chapters 16-17.
    """

    planet: str
    shadvarga_score: float  # 6 main vargas (D1,D2,D3,D9,D12,D30) — max 10
    saptvarga_score: float  # 7 vargas (D1,D2,D3,D7,D9,D12,D30) — max 20
    dashavarga_score: float  # 10 vargas — max 20
    shodashavarga_score: float  # 16 vargas (most comprehensive) — max 20
    max_score: float  # Maximum possible (20.0)
    percentage: float  # shodashavarga_score/max * 100
    dignity_in_each: dict[str, str]  # {"D1": "own", "D9": "exalted", ...}


class PlanetStrength(BaseModel):
    """Backward-compatible simplified strength view.

    Preserves the original interface used by interpreter and formatter modules
    while delegating to the full Shadbala computation under the hood.
    """

    planet: str
    sthana_bala: float  # Positional strength (0-1)
    dig_bala: float  # Directional strength (0-1)
    kala_bala: float  # Temporal strength (0-1, simplified)
    total_relative: float  # Combined relative strength (0-1)
    rank: int  # Rank among all planets (1=strongest)
    is_strong: bool
