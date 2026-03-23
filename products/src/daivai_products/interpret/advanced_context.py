"""Advanced context builder — converts Phase 1 engine output to LLM-ready text.

Extracts dasha_transit, yoga_timings, lal_kitab, badhaka, dispositor,
bhavat_bhavam, eclipse_impacts, kota_chakra, and nisheka from
FullChartAnalysis into structured dicts for prompt rendering.
"""

from __future__ import annotations

from typing import Any


def build_advanced_context(analysis: Any) -> dict[str, Any]:
    """Extract Phase 1 engine fields into template-ready context.

    Args:
        analysis: FullChartAnalysis (typed as Any to avoid circular import).

    Returns:
        Dict with keys for each Phase 1 module, ready for Jinja2 templates.
    """
    ctx: dict[str, Any] = {}

    # Dasha-Transit integration
    if dt := getattr(analysis, "dasha_transit", None):
        ctx["dasha_transit"] = _format_dasha_transit(dt)

    # Yoga activation timing
    if yt := getattr(analysis, "yoga_timings", None):
        ctx["yoga_timings"] = _format_yoga_timings(yt)

    # Lal Kitab
    if lk := getattr(analysis, "lal_kitab", None):
        ctx["lal_kitab"] = _format_lal_kitab(lk)

    # Badhaka
    if bad := getattr(analysis, "badhaka", None):
        ctx["badhaka"] = _format_badhaka(bad)

    # Dispositor tree
    if disp := getattr(analysis, "dispositor_tree", None):
        ctx["dispositor"] = _format_dispositor(disp)

    # Bhavat Bhavam
    if bb := getattr(analysis, "bhavat_bhavam", None):
        ctx["bhavat_bhavam"] = _format_bhavat_bhavam(bb)

    # Chandra / Surya Kundali
    if ck := getattr(analysis, "chandra_kundali", None):
        ctx["chandra_kundali"] = _format_reference_chart(ck, "Moon")
    if sk := getattr(analysis, "surya_kundali", None):
        ctx["surya_kundali"] = _format_reference_chart(sk, "Sun")

    # Kota Chakra
    if kc := getattr(analysis, "kota_chakra", None):
        ctx["kota_chakra"] = _format_kota_chakra(kc)

    # Nisheka
    if nish := getattr(analysis, "nisheka", None):
        ctx["nisheka"] = _format_nisheka(nish)

    # Eclipse impacts
    if ei := getattr(analysis, "eclipse_impacts", None):
        ctx["eclipse_impacts"] = _format_eclipse_impacts(ei)

    return ctx


def _format_dasha_transit(dt: Any) -> dict[str, Any]:
    """Format DashaTransitAnalysis for templates."""
    return {
        "summary": getattr(dt, "summary", ""),
        "overall_favorability": getattr(dt, "overall_favorability", ""),
        "md_lord": getattr(dt, "md_lord", None),
        "ad_lord": getattr(dt, "ad_lord", None),
        "md_ad_relationship": getattr(dt, "md_ad_relationship", ""),
        "active_houses": getattr(dt, "active_houses", []),
        "event_domains": getattr(dt, "event_domains", []),
    }


def _format_yoga_timings(yt: Any) -> dict[str, Any]:
    """Format AllYogaTimings for templates."""
    yogas = getattr(yt, "yogas", [])
    return {
        "summary": getattr(yt, "summary", ""),
        "currently_active": getattr(yt, "currently_active_yogas", []),
        "upcoming": getattr(yt, "upcoming_activations", [])[:5],
        "most_significant": _safe_yoga_name(getattr(yt, "most_significant", None)),
        "total_yogas_analyzed": len(yogas),
    }


def _safe_yoga_name(yoga: Any) -> str:
    if yoga is None:
        return ""
    return getattr(yoga, "yoga_name", "")


def _format_lal_kitab(lk: Any) -> dict[str, Any]:
    """Format LalKitabResult for templates."""
    assessments = getattr(lk, "assessments", [])
    rins = getattr(lk, "rins", [])
    remedies = getattr(lk, "remedies", [])
    return {
        "summary": getattr(lk, "summary", ""),
        "strongest_planet": getattr(lk, "strongest_planet", ""),
        "weakest_planet": getattr(lk, "weakest_planet", ""),
        "dormant_planets": getattr(lk, "dormant_planets", []),
        "rins": [{"name": r.rin_type, "severity": r.severity} for r in rins] if rins else [],
        "remedies": [
            {"planet": r.planet, "house": r.house, "remedy": r.remedy_text} for r in remedies[:10]
        ]
        if remedies
        else [],
        "assessment_count": len(assessments),
    }


def _format_badhaka(bad: Any) -> dict[str, Any]:
    """Format BadhakaResult for templates."""
    return {
        "badhaka_house": getattr(bad, "badhaka_house", 0),
        "badhaka_lord": getattr(bad, "badhaka_lord", ""),
        "badhaka_lord_house": getattr(bad, "badhaka_lord_house", 0),
        "severity": getattr(bad, "severity", ""),
        "rahu_ketu_association": getattr(bad, "rahu_ketu_association", False),
        "obstruction_domains": getattr(bad, "obstruction_domains", []),
        "summary": getattr(bad, "summary", ""),
    }


def _format_dispositor(disp: Any) -> dict[str, Any]:
    """Format DispositorTree for templates."""
    chains = getattr(disp, "chains", [])
    receptions = getattr(disp, "mutual_receptions", [])
    return {
        "final_dispositor": getattr(disp, "final_dispositor", None),
        "has_final_dispositor": getattr(disp, "has_final_dispositor", False),
        "mutual_receptions": [f"{r.planet_a}-{r.planet_b}" for r in receptions]
        if receptions
        else [],
        "chain_count": len(chains),
        "summary": getattr(disp, "summary", ""),
    }


def _format_bhavat_bhavam(bb_list: Any) -> list[dict[str, Any]]:
    """Format BhavatBhavamResult list for templates."""
    if not bb_list or not isinstance(bb_list, list):
        return []
    results = []
    for bb in bb_list[:12]:
        results.append(
            {
                "house": getattr(bb, "primary_house", 0),
                "derived_house": getattr(bb, "derived_house", 0),
                "primary_lord": getattr(bb, "primary_lord", ""),
                "derived_lord": getattr(bb, "derived_lord", ""),
                "relationship": getattr(bb, "lord_relationship", ""),
            }
        )
    return results


def _format_reference_chart(rc: Any, ref_planet: str) -> dict[str, Any]:
    """Format ReferenceChartAnalysis for templates."""
    return {
        "reference_planet": ref_planet,
        "kendras": getattr(rc, "kendras", []),
        "trikonas": getattr(rc, "trikonas", []),
        "dusthanas": getattr(rc, "dusthanas", []),
        "summary": getattr(rc, "summary", ""),
    }


def _format_kota_chakra(kc: Any) -> dict[str, Any]:
    """Format KotaChakraResult for templates."""
    return {
        "kota_swami": getattr(kc, "kota_swami_nakshatra", ""),
        "overall_strength": getattr(kc, "overall_strength", ""),
        "threatening_planets": getattr(kc, "threatening_planets", []),
        "protective_planets": getattr(kc, "protective_planets", []),
    }


def _format_nisheka(nish: Any) -> dict[str, Any]:
    """Format NishekaResult for templates."""
    return {
        "conception_date": getattr(nish, "conception_date", ""),
        "nisheka_lagna_sign": getattr(nish, "nisheka_lagna_sign_name", ""),
        "nisheka_moon_sign": getattr(nish, "nisheka_moon_sign_name", ""),
        "verification_passed": getattr(nish, "verification_passed", False),
        "summary": getattr(nish, "summary", ""),
    }


def _format_eclipse_impacts(impacts: Any) -> list[dict[str, Any]]:
    """Format eclipse natal impacts for templates."""
    if not impacts or not isinstance(impacts, list):
        return []
    results = []
    for ei in impacts[:5]:
        eclipse = getattr(ei, "eclipse", None)
        results.append(
            {
                "type": getattr(eclipse, "eclipse_type", "") if eclipse else "",
                "date": getattr(eclipse, "date", "") if eclipse else "",
                "most_affected": getattr(ei, "most_affected_planet", ""),
                "is_significant": getattr(ei, "is_significant", False),
                "summary": getattr(ei, "summary", ""),
            }
        )
    return results
