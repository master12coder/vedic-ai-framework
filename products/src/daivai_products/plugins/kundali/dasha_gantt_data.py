"""Dasha Gantt data helpers — color mapping, label constants, AD sub-row drawing."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from daivai_engine.models.dasha import DashaPeriod
from daivai_products.plugins.kundali.theme import (
    MPL_INDIGO,
    PLANET_HI,
    get_font_path,
)


# Full Hindi planet names for bar labels
PLANET_NAME_HI: dict[str, str] = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मंगल",
    "Mercury": "बुध",
    "Jupiter": "गुरु",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
}


def get_font_props() -> fm.FontProperties | None:
    """Load Devanagari font for matplotlib labels."""
    fpath = get_font_path()
    if fpath and fpath.exists():
        return fm.FontProperties(fname=str(fpath))
    return None


def planet_color(
    planet: str,
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
    maraka: set[str],
) -> str:
    """Return the bar color based on functional classification."""
    from daivai_products.plugins.kundali.theme import (
        MPL_GOLD,
        MPL_GRAY,
        MPL_GREEN,
        MPL_RED,
    )

    if planet == yogakaraka:
        return MPL_GOLD
    if planet in benefics:
        return MPL_GREEN
    if planet in malefics or planet in maraka:
        return MPL_RED
    return MPL_GRAY


def extract_sets(lordship_ctx: dict[str, Any]) -> tuple[set[str], set[str], str, set[str]]:
    """Extract functional classification sets from lordship context."""
    benefics = {e["planet"] for e in lordship_ctx.get("functional_benefics", [])}
    malefics = {e["planet"] for e in lordship_ctx.get("functional_malefics", [])}
    yk = lordship_ctx.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""
    maraka = {m["planet"] for m in lordship_ctx.get("maraka", [])}
    return benefics, malefics, yogakaraka, maraka


def date_label(dt: datetime) -> str:
    """Short date string for bar labels."""
    return dt.strftime("%Y")


def draw_ad_row(
    ax: plt.Axes,
    antardashas: list[DashaPeriod],
    current_ad: DashaPeriod,
    timeline_start: datetime,
    row_y: float,
    row_h: float,
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
    maraka: set[str],
    font_props: fm.FontProperties | None,
) -> None:
    """Draw Antardasha sub-bars within the expanded current MD row."""
    for ad in antardashas:
        x_start = (ad.start - timeline_start).total_seconds() / 86400.0
        width = (ad.end - ad.start).total_seconds() / 86400.0
        color = planet_color(ad.lord, benefics, malefics, yogakaraka, maraka)
        is_current = ad.lord == current_ad.lord and ad.start == current_ad.start

        bar = FancyBboxPatch(
            (x_start, row_y),
            width,
            row_h,
            boxstyle="round,pad=0.01",
            facecolor=color,
            edgecolor=MPL_INDIGO,
            linewidth=1.5 if is_current else 0.5,
            alpha=1.0 if is_current else 0.6,
        )
        ax.add_patch(bar)

        hi_abbr = PLANET_HI.get(ad.lord, ad.lord[:2])
        label_kw: dict[str, Any] = {
            "ha": "center",
            "va": "center",
            "fontsize": 6,
            "color": "white",
            "fontweight": "bold" if is_current else "normal",
        }
        if font_props:
            label_kw["fontproperties"] = font_props

        cx = x_start + width / 2
        ax.text(cx, row_y + row_h / 2, hi_abbr, **label_kw)
