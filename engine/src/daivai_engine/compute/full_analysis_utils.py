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
