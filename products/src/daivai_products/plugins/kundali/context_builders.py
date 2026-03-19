"""Helper builders for HTML kundali context — grids, bars, rows.

Extracted from html_context.py to keep files under 300 lines.
All functions are pure: data in, dicts out, no side effects.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from daivai_engine.constants import SIGNS_HI
from daivai_engine.models.chart import ChartData
from daivai_products.plugins.kundali.theme import (
    MPL_GOLD,
    MPL_GREEN,
    MPL_RED,
    PLANET_HI,
    planet_color_hex,
)


def build_dasha_bars(
    mahadashas: list[Any],
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
) -> list[dict[str, Any]]:
    """Build dasha timeline bar data with percentages."""
    if not mahadashas:
        return []

    total_start = mahadashas[0].start
    total_end = mahadashas[-1].end
    total_span = (total_end - total_start).total_seconds() or 1
    now = datetime.now(tz=total_start.tzinfo)

    bars: list[dict[str, Any]] = []
    for md in mahadashas:
        span = (md.end - md.start).total_seconds()
        pct = (span / total_span) * 100
        is_current = md.start <= now <= md.end
        color = planet_color_hex(md.lord, benefics, malefics, yogakaraka)
        hi = PLANET_HI.get(md.lord, md.lord[:2])
        bars.append(
            {
                "lord": md.lord,
                "lord_hi": hi,
                "start": md.start.strftime("%Y"),
                "end": md.end.strftime("%Y"),
                "pct": round(pct, 1),
                "color": color,
                "is_current": is_current,
            }
        )
    return bars


def build_ad_bars(
    antardashas: list[Any],
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
    current_ad: Any,
) -> list[dict[str, Any]]:
    """Build antardasha bars for current mahadasha."""
    if not antardashas:
        return []

    total_start = antardashas[0].start
    total_end = antardashas[-1].end
    total_span = (total_end - total_start).total_seconds() or 1

    bars: list[dict[str, Any]] = []
    for ad in antardashas:
        span = (ad.end - ad.start).total_seconds()
        pct = (span / total_span) * 100
        is_current = ad.lord == current_ad.lord
        color = planet_color_hex(ad.lord, benefics, malefics, yogakaraka)
        hi = PLANET_HI.get(ad.lord, ad.lord[:2])
        bars.append(
            {
                "lord": ad.lord,
                "lord_hi": hi,
                "start": ad.start.strftime("%b %Y"),
                "end": ad.end.strftime("%b %Y"),
                "pct": round(pct, 1),
                "color": color,
                "is_current": is_current,
            }
        )
    return bars


def build_shadbala_data(
    shadbala: list[Any],
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
) -> list[dict[str, Any]]:
    """Build shadbala display data with bar widths and colors."""
    if not shadbala:
        return []

    max_ratio = max(s.ratio for s in shadbala) if shadbala else 1.0
    data: list[dict[str, Any]] = []
    for s in shadbala:
        bar_pct = min((s.ratio / max(max_ratio, 1.0)) * 100, 100)
        bar_color = MPL_GREEN if s.ratio >= 1.0 else MPL_RED
        pcolor = planet_color_hex(s.planet, benefics, malefics, yogakaraka)
        hi = PLANET_HI.get(s.planet, s.planet[:2])
        data.append(
            {
                "planet": s.planet,
                "planet_hi": hi,
                "ratio": round(s.ratio, 2),
                "total": round(s.total, 1),
                "required": round(s.required, 1),
                "is_strong": s.is_strong,
                "bar_pct": round(bar_pct, 1),
                "bar_color": bar_color,
                "planet_color": pcolor,
                "rank": s.rank,
            }
        )
    return data


def build_avk_grid(avk: Any) -> dict[str, Any]:
    """Build ashtakavarga grid data with cell colors."""
    planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    rows: list[dict[str, Any]] = []

    for planet in planets:
        bindus = avk.bhinna.get(planet, [0] * 12)
        cells = []
        for b in bindus:
            if b >= 5:
                color = MPL_GREEN
            elif b >= 3:
                color = MPL_GOLD
            else:
                color = MPL_RED
            cells.append({"value": b, "color": color})
        hi = PLANET_HI.get(planet, planet[:2])
        rows.append({"planet": planet, "planet_hi": hi, "cells": cells})

    # SAV row
    sav_cells = []
    for b in avk.sarva:
        if b >= 30:
            color = MPL_GREEN
        elif b >= 25:
            color = MPL_GOLD
        else:
            color = MPL_RED
        sav_cells.append({"value": b, "color": color})
    rows.append({"planet": "SAV", "planet_hi": "सर्व", "cells": sav_cells})

    return {"rows": rows, "total": avk.total, "signs_hi": SIGNS_HI}


def build_planet_rows(
    chart: ChartData,
    shadbala: list[Any],
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
) -> list[dict[str, Any]]:
    """Build planet table row data."""
    sb_map = {s.planet: s for s in shadbala}
    rows: list[dict[str, Any]] = []

    for name, p in chart.planets.items():
        hi = PLANET_HI.get(name, name[:2])
        color = planet_color_hex(name, benefics, malefics, yogakaraka)

        # Functional role tag
        if name == yogakaraka:
            role = "योगकारक"
            role_class = "yoga"
        elif name in benefics:
            role = "शुभ"
            role_class = "shubh"
        elif name in malefics:
            role = "अशुभ"
            role_class = "ashubh"
        else:
            role = "—"
            role_class = "neutral"

        # Motion symbol
        if p.is_retrograde:
            motion = "↩ वक्री"
        elif p.is_combust:
            motion = "☀ अस्त"
        else:
            motion = "→"

        sb = sb_map.get(name)
        ratio = round(sb.ratio, 2) if sb else None

        rows.append(
            {
                "name": name,
                "name_hi": hi,
                "color": color,
                "sign_hi": p.sign_hi,
                "sign_en": p.sign_en,
                "degree": round(p.degree_in_sign, 1),
                "nakshatra": p.nakshatra,
                "pada": p.pada,
                "house": p.house,
                "motion": motion,
                "dignity": p.dignity,
                "avastha": p.avastha,
                "role": role,
                "role_class": role_class,
                "ratio": ratio,
            }
        )

    return rows


def find_golden(
    mahadashas: list[Any],
    benefics: set[str],
    yogakaraka: str,
) -> dict[str, Any] | None:
    """Find best upcoming golden period."""
    if not mahadashas:
        return None

    now = datetime.now(tz=mahadashas[0].start.tzinfo)
    cutoff = now.replace(year=now.year + 20)
    best_score = 0
    best_md = None

    for md in mahadashas:
        if md.end < now:
            continue
        if md.start > cutoff:
            break
        score = 0
        if md.lord == yogakaraka:
            score = 3
        elif md.lord in benefics:
            score = 2
        if score > best_score:
            best_score = score
            best_md = md

    if best_md is None:
        return None

    hi = PLANET_HI.get(best_md.lord, best_md.lord[:2])
    return {
        "lord": best_md.lord,
        "lord_hi": hi,
        "start": best_md.start.strftime("%b %Y"),
        "end": best_md.end.strftime("%b %Y"),
        "is_yogakaraka": best_md.lord == yogakaraka,
    }
