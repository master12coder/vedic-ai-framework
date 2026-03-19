"""Full chart analysis model — ALL computations in one typed container.

This is THE data contract. Everything downstream (web, PDF, AI, Pandit view)
reads from this. Nothing computes on the fly.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from daivai_engine.models.ashtakavarga import AshtakavargaResult
from daivai_engine.models.avastha import DeeptadiAvastha, LajjitadiAvastha
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.dosha import DoshaResult
from daivai_engine.models.special import (
    DoubleTransit,
    GandantaResult,
    GrahaYuddha,
    UpapadaLagna,
)
from daivai_engine.models.strength import (
    IshtaKashtaPhala,
    ShadbalaResult,
    VimshopakaBala,
)
from daivai_engine.models.yoga import YogaResult


class FullChartAnalysis(BaseModel):
    """Complete pre-computed analysis — single source of truth.

    Every field is deterministic: same input chart = same output, always.
    """

    model_config = ConfigDict(frozen=True)

    version: str = "3.0"

    # Core chart
    chart: ChartData

    # Dashas
    mahadashas: list[DashaPeriod]
    current_md: DashaPeriod
    current_ad: DashaPeriod
    narayana_dasha: list[DashaPeriod]
    dasha_sandhi: list[Any]  # DashaSandhi

    # Yogas & Doshas
    yogas: list[YogaResult]
    doshas: list[DoshaResult]

    # Strength
    shadbala: list[ShadbalaResult]
    ashtakavarga: AshtakavargaResult
    vimshopaka: list[VimshopakaBala]
    ishta_kashta: list[IshtaKashtaPhala]

    # Avasthas
    deeptadi_avasthas: list[DeeptadiAvastha]
    lajjitadi_avasthas: list[LajjitadiAvastha]

    # Special checks
    gandanta: list[GandantaResult]
    graha_yuddha: list[GrahaYuddha]
    gand_mool: Any | None  # GandMoolResult

    # Transit
    double_transit: list[DoubleTransit]
    double_transit_moon: list[DoubleTransit]
    sadesati: Any | None  # SadesatiDetail
    jupiter_transit: Any | None  # JupiterTransitResult
    rahu_ketu_transit: Any | None  # RahuKetuTransitResult

    # Jaimini
    upapada: UpapadaLagna
    argala: list[Any]

    # Special lagnas
    special_lagnas: dict[str, Any]

    # Sudarshan
    sudarshan: Any | None

    # House comparison
    house_shifts: list[Any]

    # Saham points
    sahams: list[Any]

    # Longevity (internal use only)
    longevity: Any | None  # LongevityResult

    # Mangal dosha detailed
    mangal_dosha: Any | None  # MangalDoshaDetail

    # Varga analysis
    varga_analysis: dict[str, Any]  # D7, D4, D24, D10

    # Lordship context
    lordship_context: dict

    # Verification
    verification_warnings: list[str]
