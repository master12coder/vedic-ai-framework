"""Utilities for full_analysis.py — safe_compute wrapper and Phase 2 modules."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from daivai_engine.models.chart import ChartData


logger = logging.getLogger(__name__)


def safe_compute(fn: Callable, *args: Any, **kwargs: Any) -> Any:
    """Call a computation function. On crash, log and return empty list."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning("Computation %s failed: %s", fn.__name__, e)
        return []


def compute_phase2_modules(chart: ChartData) -> dict[str, Any]:
    """Compute Phase 2 engine modules — 14 previously orphaned calculations.

    Returns dict of field_name → result, ready to spread into FullChartAnalysis.
    """
    from daivai_engine.compute.avakhada import compute_avakhada
    from daivai_engine.compute.bhava_madhya import compute_sripati_bhava_madhya
    from daivai_engine.compute.bhrigu_bindu import compute_bhrigu_bindu
    from daivai_engine.compute.dasha_conditional import (
        compute_chaturaseeti_dasha,
        compute_dwadashottari_dasha,
        compute_dwisaptati_dasha,
        compute_panchottari_dasha,
        compute_shashtihayani_dasha,
        compute_shatabdika_dasha,
        compute_shatrimsha_dasha,
    )
    from daivai_engine.compute.drekkana_analysis import compute_drekkana_analysis
    from daivai_engine.compute.gochara import compute_gochara
    from daivai_engine.compute.hora_analysis import analyze_hora
    from daivai_engine.compute.medical import analyze_health
    from daivai_engine.compute.mrityu_bhaga import check_mrityu_bhaga
    from daivai_engine.compute.pushkara import check_pushkara
    from daivai_engine.compute.sav_transit import compute_sav_pinda
    from daivai_engine.compute.shashtyamsha_analysis import analyze_d60_chart
    from daivai_engine.compute.transit import compute_transits
    from daivai_engine.compute.varga_deep_analysis import (
        analyze_d7_deep,
        analyze_d9_deep,
        analyze_d10_deep,
        analyze_d12_deep,
    )

    # Core Phase 2 modules
    result: dict[str, Any] = {
        "avakhada": safe_compute(compute_avakhada, chart),
        "bhava_madhya": safe_compute(compute_sripati_bhava_madhya, chart),
        "bhrigu_bindu": safe_compute(compute_bhrigu_bindu, chart),
        "drekkana": safe_compute(compute_drekkana_analysis, chart),
        "gochara": safe_compute(compute_gochara, chart),
        "hora": safe_compute(analyze_hora, chart),
        "medical": safe_compute(analyze_health, chart),
        "mrityu_bhaga": safe_compute(check_mrityu_bhaga, chart),
        "pushkara": safe_compute(check_pushkara, chart),
        "sav_pinda": safe_compute(compute_sav_pinda, chart),
        "d60_analysis": safe_compute(analyze_d60_chart, chart),
        "current_transits": safe_compute(compute_transits, chart),
    }

    # Deep varga analysis
    varga_deep: dict[str, Any] = {}
    for key, fn in [
        ("D9", analyze_d9_deep),
        ("D10", analyze_d10_deep),
        ("D7", analyze_d7_deep),
        ("D12", analyze_d12_deep),
    ]:
        v = safe_compute(fn, chart)
        if v:
            varga_deep[key] = v
    result["varga_deep"] = varga_deep

    # Conditional dashas (7 systems — store as dict)
    cond: dict[str, Any] = {}
    for name, cfn in [
        ("dwisaptati", compute_dwisaptati_dasha),
        ("shatabdika", compute_shatabdika_dasha),
        ("chaturaseeti", compute_chaturaseeti_dasha),
        ("dwadashottari", compute_dwadashottari_dasha),
        ("panchottari", compute_panchottari_dasha),
        ("shashtihayani", compute_shashtihayani_dasha),
        ("shatrimsha", compute_shatrimsha_dasha),
    ]:
        periods = safe_compute(cfn, chart)
        if periods and not isinstance(periods, list):
            periods = []
        if periods:
            cond[name] = periods
    result["conditional_dashas"] = cond

    return result


def compute_phase1_advanced(chart: ChartData, panchang: Any, moon_nak: int) -> dict[str, Any]:
    """Compute Phase 1 advanced modules — dispositor, badhaka, reference charts, etc."""
    from daivai_engine.compute.badhaka import compute_badhaka
    from daivai_engine.compute.bhavat_bhavam import compute_all_bhavat_bhavam
    from daivai_engine.compute.dasha_transit import compute_dasha_transit
    from daivai_engine.compute.datetime_utils import now_ist, to_jd
    from daivai_engine.compute.dispositor import compute_dispositor_tree
    from daivai_engine.compute.eclipse_natal import compute_upcoming_eclipse_impacts
    from daivai_engine.compute.kota_chakra import compute_kota_chakra
    from daivai_engine.compute.lal_kitab import compute_lal_kitab
    from daivai_engine.compute.nisheka import compute_nisheka
    from daivai_engine.compute.reference_chart import (
        compute_chandra_kundali,
        compute_surya_kundali,
    )
    from daivai_engine.compute.yoga_timing import compute_all_yoga_timings

    result: dict[str, Any] = {
        "dispositor_tree": safe_compute(compute_dispositor_tree, chart),
        "badhaka": safe_compute(compute_badhaka, chart),
        "bhavat_bhavam": safe_compute(compute_all_bhavat_bhavam, chart),
        "chandra_kundali": safe_compute(compute_chandra_kundali, chart),
        "surya_kundali": safe_compute(compute_surya_kundali, chart),
        "dasha_transit": safe_compute(compute_dasha_transit, chart),
        "yoga_timings": safe_compute(compute_all_yoga_timings, chart),
        "lal_kitab": safe_compute(compute_lal_kitab, chart),
        "kota_chakra": safe_compute(compute_kota_chakra, moon_nak),
        "nisheka": safe_compute(compute_nisheka, chart),
    }

    # Eclipse impacts
    eclipse_jd = to_jd(now_ist())
    result["eclipse_impacts"] = safe_compute(compute_upcoming_eclipse_impacts, chart, eclipse_jd, 1)

    # Pancha Pakshi birth bird
    pp_bird = ""
    if panchang and hasattr(panchang, "paksha"):
        from daivai_engine.compute.pancha_pakshi import get_birth_bird

        pp_bird_result = safe_compute(get_birth_bird, moon_nak, panchang.paksha)
        if pp_bird_result and hasattr(pp_bird_result, "value"):
            pp_bird = pp_bird_result.value
        elif isinstance(pp_bird_result, str):
            pp_bird = pp_bird_result
    result["pancha_pakshi_bird"] = pp_bird

    return result
