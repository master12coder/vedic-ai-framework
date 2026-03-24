"""Template context builder for HTML kundali rendering.

Computes all engine data, generates SVGs, prepares dasha timeline
percentages, shadbala ratios, and ashtakavarga cell colors.
Used by both the standalone HTML template and the web route.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.dasha import (
    compute_antardashas,
    compute_mahadashas,
    find_current_dasha,
)
from daivai_engine.compute.divisional import compute_navamsha
from daivai_engine.compute.strength import compute_shadbala
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.constants import SIGNS_HI
from daivai_engine.models.chart import ChartData
from daivai_products.interpret.context import build_lordship_context
from daivai_products.plugins.kundali.context_builders import (
    build_ad_bars,
    build_avk_grid,
    build_dasha_bars,
    build_planet_rows,
    build_shadbala_data,
    find_golden,
)
from daivai_products.plugins.kundali.svg_chart import (
    render_d1_svg,
    render_divisional_svg,
)
from daivai_products.plugins.kundali.theme import PLANET_HI


def build_kundali_context(
    chart: ChartData,
    fmt: str = "detailed",
    gemstone_results: list[Any] | None = None,
    full_analysis: Any | None = None,
) -> dict[str, Any]:
    """Build complete template context for the HTML kundali.

    Args:
        chart: Computed birth chart.
        fmt: Report format ('summary', 'detailed', 'pandit').
        gemstone_results: Pre-computed gemstone weight results.
        full_analysis: Optional FullChartAnalysis — avoids recomputing engine modules.

    Returns:
        Dictionary with all template variables.
    """
    ctx = build_lordship_context(chart.lagna_sign)
    benefics = {e["planet"] for e in ctx.get("functional_benefics", [])}
    malefics = {e["planet"] for e in ctx.get("functional_malefics", [])}
    yk = ctx.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""

    fa = full_analysis  # shorthand

    # Dasha — use pre-computed if available
    mahadashas = fa.mahadashas if fa else compute_mahadashas(chart)
    if fa:
        md, ad = fa.current_md, fa.current_ad
    else:
        md, ad, _pd = find_current_dasha(chart)
    antardashas = compute_antardashas(md)

    # Yogas
    yogas = (
        [y for y in fa.yogas if y.is_present]
        if fa
        else [y for y in detect_all_yogas(chart) if y.is_present]
    )

    # Shadbala
    shadbala = fa.shadbala if fa else compute_shadbala(chart)

    # Ashtakavarga
    avk = fa.ashtakavarga if fa else compute_ashtakavarga(chart)

    # SVGs
    d1_svg = render_d1_svg(chart, ctx)
    navamsha = fa.navamsha_positions if fa else compute_navamsha(chart)
    d9_svg = render_divisional_svg(chart, navamsha, "D9 नवमांश", ctx)

    # Delegate to context_builders
    dasha_bars = build_dasha_bars(mahadashas, benefics, malefics, yogakaraka)
    ad_bars = build_ad_bars(antardashas, benefics, malefics, yogakaraka, ad)
    shadbala_data = build_shadbala_data(shadbala, benefics, malefics, yogakaraka)
    avk_grid = build_avk_grid(avk)
    planet_rows = build_planet_rows(chart, shadbala, benefics, malefics, yogakaraka)
    golden = find_golden(mahadashas, benefics, yogakaraka)

    # Gemstones
    recommended_stones = ctx.get("recommended_stones", [])
    prohibited_stones = ctx.get("prohibited_stones", [])

    return {
        "chart": chart,
        "lordship_ctx": ctx,
        "benefics": benefics,
        "malefics": malefics,
        "yogakaraka": yogakaraka,
        "md": md,
        "ad": ad,
        "mahadashas": mahadashas,
        "antardashas": antardashas,
        "yogas": yogas,
        "shadbala": shadbala,
        "avk": avk,
        "d1_svg": d1_svg,
        "d9_svg": d9_svg,
        "dasha_bars": dasha_bars,
        "ad_bars": ad_bars,
        "shadbala_data": shadbala_data,
        "avk_grid": avk_grid,
        "planet_rows": planet_rows,
        "golden": golden,
        "recommended_stones": recommended_stones,
        "prohibited_stones": prohibited_stones,
        "gemstone_results": gemstone_results or [],
        "fmt": fmt,
        "signs_hi": SIGNS_HI,
        "planet_hi": PLANET_HI,
    }
