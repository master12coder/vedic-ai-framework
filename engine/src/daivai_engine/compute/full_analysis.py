"""Full chart analysis — compute ALL engine calculations in one call.

Single entry point that runs every engine computation and returns
a FullChartAnalysis model. Deterministic: same input = same output.

NOTE: lordship_context must be passed in from the products layer,
since engine/ cannot import products/ (CLAUDE.md boundary rule).
"""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.avasthas import (
    compute_deeptadi_avasthas,
    compute_lajjitadi_avasthas,
)
from daivai_engine.compute.dasha import (
    compute_mahadashas,
    find_current_dasha,
)
from daivai_engine.compute.dosha import detect_all_doshas
from daivai_engine.compute.double_transit import (
    check_double_transit,
    check_double_transit_from_moon,
)
from daivai_engine.compute.gandanta import check_gandanta
from daivai_engine.compute.graha_yuddha import detect_planetary_war
from daivai_engine.compute.ishta_kashta import compute_ishta_kashta
from daivai_engine.compute.strength import compute_shadbala
from daivai_engine.compute.upapada import compute_upapada_lagna
from daivai_engine.compute.verify import verify_chart_accuracy
from daivai_engine.compute.vimshopaka import compute_vimshopaka_bala
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import ChartData


def compute_full_analysis(
    chart: ChartData,
    lordship_context: dict[str, Any] | None = None,
) -> FullChartAnalysis:
    """Run ALL engine computations and return a single typed result.

    Args:
        chart: Computed birth chart.
        lordship_context: Pre-built lordship context from products layer.
            If None, an empty dict is used (caller should provide this).

    Returns:
        FullChartAnalysis containing every computation result.
    """
    if lordship_context is None:
        lordship_context = {}

    # Core computations
    mahadashas = compute_mahadashas(chart)
    md, ad, _pd = find_current_dasha(chart)
    yogas = detect_all_yogas(chart)
    doshas = detect_all_doshas(chart)
    shadbala = compute_shadbala(chart)
    avk = compute_ashtakavarga(chart)

    # New computations
    gandanta = check_gandanta(chart)
    yuddha = detect_planetary_war(chart)
    deeptadi = compute_deeptadi_avasthas(chart)
    lajjitadi = compute_lajjitadi_avasthas(chart)
    vimshopaka = compute_vimshopaka_bala(chart)
    ishta_kashta = compute_ishta_kashta(chart, shadbala)
    double_transit = check_double_transit(chart)
    double_transit_moon = check_double_transit_from_moon(chart)
    upapada = compute_upapada_lagna(chart)
    verification = verify_chart_accuracy(chart)

    return FullChartAnalysis(
        chart=chart,
        mahadashas=mahadashas,
        current_md=md,
        current_ad=ad,
        yogas=yogas,
        doshas=doshas,
        shadbala=shadbala,
        ashtakavarga=avk,
        gandanta=gandanta,
        graha_yuddha=yuddha,
        deeptadi_avasthas=deeptadi,
        lajjitadi_avasthas=lajjitadi,
        vimshopaka=vimshopaka,
        ishta_kashta=ishta_kashta,
        double_transit=double_transit,
        double_transit_moon=double_transit_moon,
        upapada=upapada,
        lordship_context=lordship_context,
        verification_warnings=verification,
    )
