"""Full chart analysis model — ALL computations in one typed container.

This is THE data contract. Everything downstream (web, PDF, AI, Pandit view)
reads from this. Nothing computes on the fly.
"""

from __future__ import annotations

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
    """Complete pre-computed analysis — single source of truth for all layers.

    Every field is deterministic: same input chart = same output, always.
    """

    model_config = ConfigDict(frozen=True)

    chart: ChartData
    mahadashas: list[DashaPeriod]
    current_md: DashaPeriod
    current_ad: DashaPeriod
    yogas: list[YogaResult]
    doshas: list[DoshaResult]
    shadbala: list[ShadbalaResult]
    ashtakavarga: AshtakavargaResult
    gandanta: list[GandantaResult]
    graha_yuddha: list[GrahaYuddha]
    deeptadi_avasthas: list[DeeptadiAvastha]
    lajjitadi_avasthas: list[LajjitadiAvastha]
    vimshopaka: list[VimshopakaBala]
    ishta_kashta: list[IshtaKashtaPhala]
    double_transit: list[DoubleTransit]
    upapada: UpapadaLagna
    lordship_context: dict  # Functional benefic/malefic per lagna
