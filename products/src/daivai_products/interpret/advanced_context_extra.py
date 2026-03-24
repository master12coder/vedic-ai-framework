"""Extra context builder — activates dead FullChartAnalysis fields + Phase 2.

Converts previously-orphaned engine fields into LLM-ready template context.
Companion to advanced_context.py (Phase 1 fields).
"""

from __future__ import annotations

from typing import Any


def build_advanced_context_extra(analysis: Any) -> dict[str, Any]:
    """Extract Phase 2 + previously-dead fields into template-ready context."""
    ctx: dict[str, Any] = {}

    # Birth panchang (tithi, yoga, karana — fundamental)
    if bp := getattr(analysis, "birth_panchang", None):
        ctx["birth_panchang"] = _format_panchang(bp)

    # Sade Sati
    if ss := getattr(analysis, "sadesati", None):
        ctx["sadesati"] = _format_sadesati(ss)

    # Double transit (Jupiter + Saturn)
    dt = getattr(analysis, "double_transit", None)
    dtm = getattr(analysis, "double_transit_moon", None)
    if dt or dtm:
        ctx["double_transit_info"] = _format_double_transit(dt, dtm)

    # Jaimini
    if jm := getattr(analysis, "jaimini", None):
        ctx["jaimini"] = _format_jaimini(jm)

    # Special lagnas
    if sl := getattr(analysis, "special_lagnas", None):
        ctx["special_lagnas_info"] = _format_special_lagnas(sl)

    # Mangal dosha detailed
    if md := getattr(analysis, "mangal_dosha", None):
        ctx["mangal_dosha_detail"] = _format_mangal_dosha(md)

    # Gandanta
    if gd := getattr(analysis, "gandanta", None):
        ctx["gandanta_info"] = _format_gandanta(gd)

    # Graha Yuddha
    if gy := getattr(analysis, "graha_yuddha", None):
        ctx["graha_yuddha_info"] = _format_graha_yuddha(gy)

    # Varga analysis (D4/D7/D10/D24)
    if va := getattr(analysis, "varga_analysis", None):
        ctx["varga_basic"] = _format_varga_basic(va)

    # Longevity
    if lon := getattr(analysis, "longevity", None):
        ctx["longevity_info"] = _format_longevity(lon)

    # Phase 2 modules
    if av := getattr(analysis, "avakhada", None):
        ctx["avakhada"] = _format_avakhada(av)

    if bb := getattr(analysis, "bhrigu_bindu", None):
        ctx["bhrigu_bindu"] = _format_bhrigu_bindu(bb)

    if gc := getattr(analysis, "gochara", None):
        ctx["gochara_info"] = _format_gochara(gc)

    if med := getattr(analysis, "medical", None):
        ctx["medical_info"] = _format_medical(med)

    if mb := getattr(analysis, "mrityu_bhaga", None):
        ctx["mrityu_bhaga_info"] = _format_mrityu_bhaga(mb)

    if pk := getattr(analysis, "pushkara", None):
        ctx["pushkara_info"] = _format_pushkara(pk)

    if hr := getattr(analysis, "hora", None):
        ctx["hora_info"] = _format_hora(hr)

    if ct := getattr(analysis, "current_transits", None):
        ctx["transit_info"] = _format_transits(ct)

    if d60 := getattr(analysis, "d60_analysis", None):
        ctx["d60_info"] = _format_d60(d60)

    return ctx


# ── Formatters ────────────────────────────────────────────────────────────


def _format_panchang(bp: Any) -> dict[str, Any]:
    return {
        "tithi": getattr(bp, "tithi", ""),
        "yoga": getattr(bp, "yoga", ""),
        "karana": getattr(bp, "karana", ""),
        "nakshatra": getattr(bp, "nakshatra", ""),
        "vara": getattr(bp, "vara", ""),
    }


def _format_sadesati(ss: Any) -> dict[str, Any]:
    return {
        "is_active": getattr(ss, "is_active", False),
        "phase": getattr(ss, "phase", ""),
        "intensity": getattr(ss, "intensity", ""),
        "start_date": str(getattr(ss, "start_date", "")),
        "end_date": str(getattr(ss, "end_date", "")),
    }


def _format_double_transit(dt: Any, dtm: Any) -> dict[str, Any]:
    houses_lagna = [getattr(d, "house", 0) for d in (dt or [])]
    houses_moon = [getattr(d, "house", 0) for d in (dtm or [])]
    return {"active_houses_from_lagna": houses_lagna, "active_houses_from_moon": houses_moon}


def _format_jaimini(jm: Any) -> dict[str, Any]:
    karakas = getattr(jm, "karakas", {})
    if hasattr(karakas, "items"):
        karaka_list = [{"karaka": k, "planet": v} for k, v in karakas.items()]
    elif isinstance(karakas, list):
        karaka_list = [
            {"karaka": getattr(k, "karaka_name", ""), "planet": getattr(k, "planet", "")}
            for k in karakas
        ]
    else:
        karaka_list = []
    return {"karakas": karaka_list, "karakamsha": getattr(jm, "karakamsha_sign", "")}


def _format_special_lagnas(sl: dict) -> list[dict[str, Any]]:
    if not isinstance(sl, dict):
        return []
    return [
        {"name": k, "sign": v.get("sign", "") if isinstance(v, dict) else str(v)}
        for k, v in sl.items()
    ]


def _format_mangal_dosha(md: Any) -> dict[str, Any]:
    return {
        "is_present": getattr(md, "is_present", False),
        "severity": getattr(md, "severity", ""),
        "from_lagna": getattr(md, "from_lagna", False),
        "from_moon": getattr(md, "from_moon", False),
        "from_venus": getattr(md, "from_venus", False),
        "cancellations": getattr(md, "cancellations", []),
    }


def _format_gandanta(gd: Any) -> list[dict[str, Any]]:
    if not gd or not isinstance(gd, list):
        return []
    return [
        {"planet": getattr(g, "planet", ""), "type": getattr(g, "gandanta_type", "")}
        for g in gd
        if getattr(g, "is_gandanta", False)
    ]


def _format_graha_yuddha(gy: Any) -> list[dict[str, Any]]:
    if not gy or not isinstance(gy, list):
        return []
    return [
        {
            "winner": getattr(g, "winner", ""),
            "loser": getattr(g, "loser", ""),
            "degree_diff": getattr(g, "degree_diff", 0),
        }
        for g in gy
    ]


def _format_varga_basic(va: dict) -> dict[str, Any]:
    if not isinstance(va, dict):
        return {}
    result = {}
    for key, val in va.items():
        result[key] = (
            getattr(val, "summary", str(val)[:200]) if hasattr(val, "summary") else str(val)[:200]
        )
    return result


def _format_longevity(lon: Any) -> dict[str, Any]:
    return {
        "category": getattr(lon, "category", ""),
        "amshayu": getattr(lon, "amshayu_years", 0),
        "pindayu": getattr(lon, "pindayu_years", 0),
    }


def _format_avakhada(av: Any) -> dict[str, Any]:
    return {
        "birth_nakshatra": getattr(av, "birth_nakshatra", ""),
        "varna": getattr(av, "varna", ""),
        "yoni": getattr(av, "yoni", ""),
        "gana": getattr(av, "gana", ""),
        "nadi": getattr(av, "nadi", ""),
        "tattwa": getattr(av, "tattwa", ""),
    }


def _format_bhrigu_bindu(bb: Any) -> dict[str, Any]:
    return {
        "longitude": getattr(bb, "longitude", 0),
        "sign": getattr(bb, "sign_name", ""),
        "nakshatra": getattr(bb, "nakshatra", ""),
        "house": getattr(bb, "house", 0),
        "activation_ages": getattr(bb, "activation_ages", []),
    }


def _format_gochara(gc: Any) -> list[dict[str, Any]]:
    planets = getattr(gc, "planets", [])
    if not isinstance(planets, list):
        return []
    return [
        {
            "planet": getattr(p, "planet", ""),
            "transit_sign": getattr(p, "transit_sign", ""),
            "house_from_moon": getattr(p, "house_from_moon", 0),
            "effect": getattr(p, "effect", ""),
            "is_favorable": getattr(p, "is_favorable", None),
        }
        for p in planets[:9]
    ]


def _format_medical(med: Any) -> dict[str, Any]:
    vulns = getattr(med, "vulnerabilities", [])
    dosha_bal = getattr(med, "tridosha", None)
    return {
        "vulnerable_areas": [
            {"body_part": getattr(v, "body_part", ""), "planet": getattr(v, "planet", "")}
            for v in (vulns[:5] if isinstance(vulns, list) else [])
        ],
        "tridosha": getattr(dosha_bal, "dominant", "") if dosha_bal else "",
    }


def _format_mrityu_bhaga(mb: Any) -> list[dict[str, Any]]:
    if not mb or not isinstance(mb, list):
        return []
    return [
        {"planet": getattr(m, "planet", ""), "is_afflicted": getattr(m, "is_afflicted", False)}
        for m in mb
        if getattr(m, "is_afflicted", False)
    ]


def _format_pushkara(pk: Any) -> list[dict[str, Any]]:
    if not pk or not isinstance(pk, list):
        return []
    return [
        {"planet": getattr(p, "planet", ""), "type": getattr(p, "pushkara_type", "")}
        for p in pk
        if getattr(p, "is_pushkara", False)
    ]


def _format_hora(hr: Any) -> dict[str, Any]:
    planets = getattr(hr, "planets", [])
    return {
        "wealth_indicator": getattr(hr, "wealth_summary", ""),
        "sun_hora_planets": [
            getattr(p, "planet", "") for p in planets if getattr(p, "hora_lord", "") == "Sun"
        ],
        "moon_hora_planets": [
            getattr(p, "planet", "") for p in planets if getattr(p, "hora_lord", "") == "Moon"
        ],
    }


def _format_transits(ct: Any) -> list[dict[str, Any]]:
    planets = getattr(ct, "planets", [])
    if not isinstance(planets, list):
        return []
    return [
        {
            "planet": getattr(p, "planet", ""),
            "sign": getattr(p, "sign", ""),
            "is_retrograde": getattr(p, "is_retrograde", False),
        }
        for p in planets
    ]


def _format_d60(d60: Any) -> dict[str, Any]:
    return {
        "summary": getattr(d60, "summary", ""),
        "benefic_count": getattr(d60, "benefic_d60_count", 0),
        "malefic_count": getattr(d60, "malefic_d60_count", 0),
    }
