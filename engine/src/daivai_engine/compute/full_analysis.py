"""Full chart analysis — compute ALL engine calculations in one call.

Single entry point that runs every engine computation and returns
a FullChartAnalysis model. Each module wrapped in safe_compute().

NOTE: lordship_context must be passed in from the products layer.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from daivai_engine.compute.argala import compute_argala
from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.avasthas import (
    compute_deeptadi_avasthas,
    compute_lajjitadi_avasthas,
)
from daivai_engine.compute.compatibility_advanced import compute_mangal_dosha_detailed
from daivai_engine.compute.dasha import compute_mahadashas, find_current_dasha
from daivai_engine.compute.dasha_advanced import compute_dasha_sandhi
from daivai_engine.compute.dosha import detect_all_doshas
from daivai_engine.compute.double_transit import (
    check_double_transit,
    check_double_transit_from_moon,
)
from daivai_engine.compute.gandanta import check_gandanta
from daivai_engine.compute.graha_yuddha import detect_planetary_war
from daivai_engine.compute.house_comparison import compare_whole_sign_vs_chalit
from daivai_engine.compute.ishta_kashta import compute_ishta_kashta
from daivai_engine.compute.longevity import compute_longevity
from daivai_engine.compute.namkaran import check_gand_mool
from daivai_engine.compute.narayana_dasha import compute_narayana_dasha
from daivai_engine.compute.saham import compute_sahams
from daivai_engine.compute.special_lagnas import compute_special_lagnas
from daivai_engine.compute.strength import compute_shadbala
from daivai_engine.compute.sudarshan import compute_sudarshan
from daivai_engine.compute.transit_advanced import (
    compute_jupiter_transit,
    compute_rahu_ketu_transit,
    compute_sadesati_detailed,
)
from daivai_engine.compute.upapada import compute_upapada_lagna
from daivai_engine.compute.varga_analysis import (
    analyze_d4_property,
    analyze_d7_children,
    analyze_d10_career,
    analyze_d24_education,
)
from daivai_engine.compute.verify import verify_chart_accuracy
from daivai_engine.compute.vimshopaka import compute_vimshopaka_bala
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import ChartData


logger = logging.getLogger(__name__)


def compute_full_analysis(
    chart: ChartData,
    lordship_context: dict[str, Any] | None = None,
) -> FullChartAnalysis:
    """Run ALL engine computations and return a single typed result.

    Each module is wrapped in safe_compute() — individual failures
    don't crash the pipeline.

    Args:
        chart: Computed birth chart.
        lordship_context: Pre-built lordship context from products layer.

    Returns:
        FullChartAnalysis v3.0 with all fields populated.
    """
    if lordship_context is None:
        lordship_context = {}

    # Core
    mahadashas = compute_mahadashas(chart)
    md, ad, _pd = find_current_dasha(chart)
    yogas = detect_all_yogas(chart)
    doshas = detect_all_doshas(chart)
    shadbala = compute_shadbala(chart)
    avk = compute_ashtakavarga(chart)

    # Strength
    vimshopaka = safe_compute(compute_vimshopaka_bala, chart)
    ishta_kashta = safe_compute(compute_ishta_kashta, chart, shadbala)

    # Avasthas
    deeptadi = safe_compute(compute_deeptadi_avasthas, chart)
    lajjitadi = safe_compute(compute_lajjitadi_avasthas, chart)

    # Special checks
    gandanta = safe_compute(check_gandanta, chart)
    yuddha = safe_compute(detect_planetary_war, chart)
    gand_mool = safe_compute(check_gand_mool, chart)

    # Transit
    dt_lagna = safe_compute(check_double_transit, chart)
    dt_moon = safe_compute(check_double_transit_from_moon, chart)
    sadesati = safe_compute(compute_sadesati_detailed, chart)
    jup_transit = safe_compute(compute_jupiter_transit, chart)
    rk_transit = safe_compute(compute_rahu_ketu_transit, chart)

    # Jaimini
    upapada = compute_upapada_lagna(chart)
    argala = safe_compute(compute_argala, chart)

    # Dashas
    narayana = safe_compute(compute_narayana_dasha, chart)
    sandhi = safe_compute(compute_dasha_sandhi, mahadashas)

    # Special lagnas
    sp_lagnas = safe_compute(compute_special_lagnas, chart)
    if not isinstance(sp_lagnas, dict):
        sp_lagnas = {}

    # Sudarshan
    sudarshan = safe_compute(compute_sudarshan, chart)

    # House comparison
    house_shifts = safe_compute(compare_whole_sign_vs_chalit, chart)

    # Saham points
    sahams = safe_compute(compute_sahams, chart)

    # Longevity
    longevity = safe_compute(compute_longevity, chart)

    # Mangal dosha detailed
    mangal = safe_compute(compute_mangal_dosha_detailed, chart)

    # Varga analysis
    varga = {}
    d7 = safe_compute(analyze_d7_children, chart)
    d4 = safe_compute(analyze_d4_property, chart)
    d24 = safe_compute(analyze_d24_education, chart)
    d10 = safe_compute(analyze_d10_career, chart)
    if d7:
        varga["D7"] = d7
    if d4:
        varga["D4"] = d4
    if d24:
        varga["D24"] = d24
    if d10:
        varga["D10"] = d10

    # Verification
    verification = verify_chart_accuracy(chart)

    return FullChartAnalysis(
        chart=chart,
        mahadashas=mahadashas,
        current_md=md,
        current_ad=ad,
        narayana_dasha=narayana,
        dasha_sandhi=sandhi,
        yogas=yogas,
        doshas=doshas,
        shadbala=shadbala,
        ashtakavarga=avk,
        vimshopaka=vimshopaka,
        ishta_kashta=ishta_kashta,
        deeptadi_avasthas=deeptadi,
        lajjitadi_avasthas=lajjitadi,
        gandanta=gandanta,
        graha_yuddha=yuddha,
        gand_mool=gand_mool,
        double_transit=dt_lagna,
        double_transit_moon=dt_moon,
        sadesati=sadesati,
        jupiter_transit=jup_transit,
        rahu_ketu_transit=rk_transit,
        upapada=upapada,
        argala=argala,
        special_lagnas=sp_lagnas,
        sudarshan=sudarshan,
        house_shifts=house_shifts,
        sahams=sahams,
        longevity=longevity,
        mangal_dosha=mangal,
        varga_analysis=varga,
        lordship_context=lordship_context,
        verification_warnings=verification,
    )


def safe_compute(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """Call a computation function. On crash, log error and return empty list."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning("Computation %s failed: %s", fn.__name__, e)
        return []
