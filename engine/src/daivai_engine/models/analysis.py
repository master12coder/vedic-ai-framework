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

    v5.0: All Phase 1 modules wired in. 50+ fields.
    """

    model_config = ConfigDict(frozen=True)

    version: str = "5.0"

    # Core
    chart: ChartData

    # Dashas (all systems)
    mahadashas: list[DashaPeriod]
    current_md: DashaPeriod
    current_ad: DashaPeriod
    narayana_dasha: list[DashaPeriod]
    yogini_dasha: list[Any]  # YoginiDashaPeriod
    ashtottari_dasha: list[Any]  # AshtottariDashaPeriod
    chara_dasha: list[Any]  # CharaDashaPeriod (different model from DashaPeriod)
    kalachakra_dasha: Any | None  # KalachakraDashaResult (BPHS Ch.46)
    dasha_sandhi: list[Any]

    # Yogas & Doshas
    yogas: list[YogaResult]  # 80+ checks
    doshas: list[DoshaResult]  # 10 checks

    # Strength
    shadbala: list[ShadbalaResult]
    bhava_bala: list[Any]  # BhavaBalaResult — house strength
    ashtakavarga: AshtakavargaResult
    vimshopaka: list[VimshopakaBala]
    ishta_kashta: list[IshtaKashtaPhala]

    # Avasthas
    deeptadi_avasthas: list[DeeptadiAvastha]
    lajjitadi_avasthas: list[LajjitadiAvastha]

    # Special checks
    gandanta: list[GandantaResult]
    graha_yuddha: list[GrahaYuddha]
    gand_mool: Any | None

    # Divisional charts
    navamsha_positions: list[Any]  # D9 positions
    vargottam_planets: list[str]

    # Transit
    double_transit: list[DoubleTransit]
    double_transit_moon: list[DoubleTransit]
    sadesati: Any | None
    jupiter_transit: Any | None
    rahu_ketu_transit: Any | None

    # Jaimini
    jaimini: Any | None  # JaiminiResult — karakas + arudha + karakamsha
    upapada: UpapadaLagna
    argala: list[Any]

    # KP
    kp_positions: list[Any]  # KPPosition per planet

    # Bhava Chalit
    bhava_chalit: Any | None  # BhavaChalitResult
    house_shifts: list[Any]

    # Upagrahas
    upagrahas: list[Any]

    # Special lagnas
    special_lagnas: dict[str, Any]

    # Birth panchang
    birth_panchang: Any | None

    # Sudarshan
    sudarshan: Any | None

    # Saham points
    sahams: list[Any]

    # Longevity
    longevity: Any | None

    # Mangal dosha detailed
    mangal_dosha: Any | None

    # Varga analysis
    varga_analysis: dict[str, Any]

    # Lordship context
    lordship_context: dict

    # Verification
    verification_warnings: list[str]

    # Phase 1 advanced modules (March 2026)
    dispositor_tree: Any | None = None  # DispositorTree — chain/tree analysis
    badhaka: Any | None = None  # BadhakaResult — obstruction house/lord
    bhavat_bhavam: list[Any] = []  # BhavatBhavamResult per house
    chandra_kundali: Any | None = None  # ReferenceChartAnalysis from Moon
    surya_kundali: Any | None = None  # ReferenceChartAnalysis from Sun
    dasha_transit: Any | None = None  # DashaTransitAnalysis — #1 timing technique
    yoga_timings: Any | None = None  # AllYogaTimings — activation periods
    lal_kitab: Any | None = None  # LalKitabResult — parallel remedy system
    kota_chakra: Any | None = None  # KotaChakraResult — fortress diagram
    nisheka: Any | None = None  # NishekaResult — conception chart (BPHS Ch.4)
    eclipse_impacts: list[Any] = []  # EclipseNatalResult — upcoming eclipse natal impacts
