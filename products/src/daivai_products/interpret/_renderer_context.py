"""Chart context builder for interpretation renderer.

Assembles the full template context dict from a ChartData object, including:
- Computed chart data (planets, yogas, doshas, strengths, dasha)
- Lordship rules for THIS lagna (benefics, malefics, maraka, gemstones)
- Gemstone logic with contraindications
- Scripture citations for planets in their houses
- Pandit Ji learned corrections
"""

from __future__ import annotations

import logging
from typing import Any

from daivai_engine.compute.dasha import compute_mahadashas, find_current_dasha
from daivai_engine.compute.divisional import get_vargottam_planets
from daivai_engine.compute.dosha import detect_all_doshas
from daivai_engine.compute.strength import compute_planet_strengths
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.models.chart import ChartData
from daivai_products.interpret.advanced_context import build_advanced_context
from daivai_products.interpret.advanced_context_extra import build_advanced_context_extra
from daivai_products.interpret.context import (
    build_gemstone_context,
    build_lordship_context,
    build_scripture_context,
)


logger = logging.getLogger(__name__)


def build_chart_context(
    chart: ChartData,
    full_analysis: Any | None = None,
) -> dict[str, Any]:
    """Build a context dictionary from chart data for prompt rendering.

    Includes:
    - All computed chart data (planets, yogas, doshas, strengths, dasha)
    - Lordship rules for THIS lagna (benefics, malefics, maraka, gemstones)
    - Gemstone logic with contraindications
    - Scripture citations for planets in their houses
    - Pandit Ji learned corrections
    - Phase 1 advanced modules (if full_analysis provided)

    Args:
        chart: Computed birth chart.
        full_analysis: Optional FullChartAnalysis with Phase 1 data.

    Returns:
        Dictionary ready for Jinja2 template rendering.
    """
    yogas = detect_all_yogas(chart)
    doshas = detect_all_doshas(chart)
    strengths = compute_planet_strengths(chart)
    vargottam = get_vargottam_planets(chart)
    mahadashas = compute_mahadashas(chart)

    try:
        md, ad, pd = find_current_dasha(chart)
        current_dasha = {
            "mahadasha": md.lord,
            "antardasha": ad.lord,
            "pratyantardasha": pd.lord,
            "md_start": md.start.strftime("%d/%m/%Y"),
            "md_end": md.end.strftime("%d/%m/%Y"),
            "ad_start": ad.start.strftime("%d/%m/%Y"),
            "ad_end": ad.end.strftime("%d/%m/%Y"),
        }
    except Exception:
        current_dasha = {
            "mahadasha": "Unknown",
            "antardasha": "Unknown",
            "pratyantardasha": "Unknown",
        }

    planet_summary = []
    for p in chart.planets.values():
        planet_summary.append(
            {
                "name": p.name,
                "sign": p.sign,
                "sign_en": p.sign_en,
                "house": p.house,
                "degree": f"{p.degree_in_sign:.1f}\u00b0",
                "nakshatra": p.nakshatra,
                "pada": p.pada,
                "dignity": p.dignity,
                "retrograde": p.is_retrograde,
                "combust": p.is_combust,
                "sign_lord": p.sign_lord,
            }
        )

    yoga_summary = [
        {
            "name": y.name,
            "name_hindi": y.name_hindi,
            "description": y.description,
            "effect": y.effect,
        }
        for y in yogas
        if y.is_present
    ]

    dosha_summary = [
        {
            "name": d.name,
            "name_hindi": d.name_hindi,
            "severity": d.severity,
            "description": d.description,
        }
        for d in doshas
        if d.is_present
    ]

    strength_summary = [
        {"planet": s.planet, "rank": s.rank, "strength": s.total_relative, "is_strong": s.is_strong}
        for s in strengths
    ]

    # ------------------------------------------------------------------
    # Knowledge context: lordship, gemstones, scripture, pandit rules
    # ------------------------------------------------------------------
    lordship_ctx = build_lordship_context(chart.lagna_sign)
    gemstone_ctx = build_gemstone_context()
    scripture_citations = build_scripture_context(chart)

    # Try to load Pandit corrections from the store
    pandit_teachings = ""
    try:
        from daivai_products.store.corrections import PanditCorrectionStore

        pandit_store = PanditCorrectionStore()
        pandit_teachings = pandit_store.get_prompt_additions(lagna=chart.lagna_sign)
    except Exception:
        pandit_teachings = ""

    # Determine if current Mahadasha lord is benefic for this lagna
    md_lord = current_dasha.get("mahadasha", "")
    benefic_names = [b.get("planet", "") for b in lordship_ctx.get("functional_benefics", [])]
    malefic_names = [m.get("planet", "") for m in lordship_ctx.get("functional_malefics", [])]
    maraka_names = [m.get("planet", "") for m in lordship_ctx.get("maraka", [])]
    is_md_lord_benefic = md_lord in benefic_names
    is_md_lord_maraka = md_lord in maraka_names

    # Lagnesh info
    lagnesh = lordship_ctx.get("sign_lord", "")
    lagnesh_stone = ""
    yogakaraka_info = lordship_ctx.get("yogakaraka", {})
    yogakaraka_planet = (
        yogakaraka_info.get("planet", "") if isinstance(yogakaraka_info, dict) else ""
    )
    yogakaraka_stone = ""

    gem_recs = lordship_ctx.get("gemstone_recommendations", {})
    if lagnesh and lagnesh in gem_recs:
        lagnesh_stone = gem_recs[lagnesh].get("gemstone", "")
    if yogakaraka_planet and yogakaraka_planet in gem_recs:
        yogakaraka_stone = gem_recs[yogakaraka_planet].get("gemstone", "")

    # Friend / enemy groups from gemstone_logic.yaml
    friends_map = gemstone_ctx.get("planetary_friendships", {}).get("friends", {})

    # Build friend group around lagnesh
    friend_group_planets: set[str] = set()
    if lagnesh:
        friend_group_planets.add(lagnesh)
        for friend in friends_map.get(lagnesh, []):
            if friend in benefic_names:
                friend_group_planets.add(friend)

    gemstone_data = gemstone_ctx.get("gemstone_data", {})
    friend_group_str = " + ".join(
        f"{p} ({gemstone_data.get(p, {}).get('primary', {}).get('name_en', '?')})"
        for p in sorted(friend_group_planets)
    )

    enemy_group_planets = set(malefic_names + maraka_names) - friend_group_planets
    enemy_group_str = " + ".join(
        f"{p} ({gemstone_data.get(p, {}).get('primary', {}).get('name_en', '?')})"
        for p in sorted(enemy_group_planets)
    )

    return {
        # --- Existing chart data ---
        "name": chart.name,
        "dob": chart.dob,
        "tob": chart.tob,
        "place": chart.place,
        "gender": chart.gender,
        "lagna": chart.lagna_sign,
        "lagna_en": chart.lagna_sign_en,
        "lagna_hi": chart.lagna_sign_hi,
        "lagna_degree": f"{chart.lagna_degree:.1f}\u00b0",
        "planets": planet_summary,
        "yogas": yoga_summary,
        "doshas": dosha_summary,
        "strengths": strength_summary,
        "vargottam_planets": vargottam,
        "current_dasha": current_dasha,
        "mahadashas": [
            {
                "lord": md.lord,
                "start": md.start.strftime("%d/%m/%Y"),
                "end": md.end.strftime("%d/%m/%Y"),
            }
            for md in mahadashas
        ],
        # --- Lordship context ---
        "lordship": lordship_ctx,
        "yogakaraka": yogakaraka_info,
        "yogakaraka_planet": yogakaraka_planet,
        "yogakaraka_stone": yogakaraka_stone,
        "functional_benefics": lordship_ctx.get("functional_benefics", []),
        "functional_malefics": lordship_ctx.get("functional_malefics", []),
        "maraka_planets": lordship_ctx.get("maraka", []),
        "house_lords": lordship_ctx.get("house_lords", {}),
        "recommended_stones": lordship_ctx.get("recommended_stones", []),
        "prohibited_stones": lordship_ctx.get("prohibited_stones", []),
        "test_stones": lordship_ctx.get("test_stones", []),
        "gemstone_recs": gem_recs,
        # --- Gemstone logic ---
        "contraindications": gemstone_ctx.get("contraindications", []),
        "friend_group": friend_group_str,
        "enemy_group": enemy_group_str,
        # --- Lagnesh / dasha benefic info ---
        "lagnesh": lagnesh,
        "lagnesh_stone": lagnesh_stone,
        "is_md_lord_benefic": is_md_lord_benefic,
        "is_md_lord_maraka": is_md_lord_maraka,
        # --- Scripture & Pandit Ji ---
        "scripture_citations": scripture_citations,
        "pandit_teachings": pandit_teachings,
        # --- Phase 1 advanced modules ---
        **(build_advanced_context(full_analysis) if full_analysis else {}),
        # --- Phase 2 + previously-dead fields ---
        **(build_advanced_context_extra(full_analysis) if full_analysis else {}),
    }
