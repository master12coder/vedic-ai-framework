"""Dasha Gantt chart renderer — horizontal timeline of Vimshottari Mahadashas.

Renders 9 color-coded MD bars (birth to 120y) with current MD expanded to show ADs.
"""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib


matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from jyotish_engine.models.chart import ChartData
from jyotish_engine.models.dasha import DashaPeriod
from jyotish_products.plugins.kundali.theme import (
    MPL_CREAM,
    MPL_GOLD,
    MPL_GRAY,
    MPL_GREEN,
    MPL_INDIGO,
    MPL_RED,
    MPL_SAFFRON,
    PLANET_HI,
    get_font_path,
)


# Full Hindi planet names for bar labels
_PLANET_NAME_HI: dict[str, str] = {
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


def _get_font_props() -> fm.FontProperties | None:
    """Load Devanagari font for matplotlib labels."""
    fpath = get_font_path()
    if fpath and fpath.exists():
        return fm.FontProperties(fname=str(fpath))
    return None


def _planet_color(
    planet: str,
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
    maraka: set[str],
) -> str:
    """Return the bar color based on functional classification."""
    if planet == yogakaraka:
        return MPL_GOLD
    if planet in benefics:
        return MPL_GREEN
    if planet in malefics or planet in maraka:
        return MPL_RED
    return MPL_GRAY


def _extract_sets(lordship_ctx: dict[str, Any]) -> tuple[set[str], set[str], str, set[str]]:
    """Extract functional classification sets from lordship context."""
    benefics = {e["planet"] for e in lordship_ctx.get("functional_benefics", [])}
    malefics = {e["planet"] for e in lordship_ctx.get("functional_malefics", [])}
    yk = lordship_ctx.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""
    maraka = {m["planet"] for m in lordship_ctx.get("maraka", [])}
    return benefics, malefics, yogakaraka, maraka


def _date_label(dt: datetime) -> str:
    """Short date string for bar labels."""
    return dt.strftime("%Y")


def render_dasha_gantt(
    chart: ChartData,
    mahadashas: list[DashaPeriod],
    current_md: DashaPeriod,
    current_ad: DashaPeriod,
    antardashas: list[DashaPeriod],
    lordship_ctx: dict[str, Any],
    output_path: str | Path | None = None,
) -> bytes | None:
    """Render a horizontal Gantt-style dasha timeline as PNG.

    Args:
        chart: Birth chart data (for name, dob, lagna).
        mahadashas: All 9 Mahadasha periods from compute_mahadashas().
        current_md: Currently running Mahadasha.
        current_ad: Currently running Antardasha.
        antardashas: All ADs within current_md.
        lordship_ctx: Lordship context from build_lordship_context().
        output_path: Save to file if provided; else return PNG bytes.

    Returns:
        PNG bytes if output_path is None, else None (saved to file).
    """
    if not mahadashas:
        return None

    benefics, malefics, yogakaraka, maraka = _extract_sets(lordship_ctx)
    font_props = _get_font_props()

    # Timeline bounds
    timeline_start = mahadashas[0].start
    timeline_end = mahadashas[-1].end
    total_days = (timeline_end - timeline_start).total_seconds() / 86400.0
    if total_days <= 0:
        return None

    # Layout: 9 MD bars + expanded AD row for current MD
    n_md = len(mahadashas)
    ad_row_height = 0.5
    md_row_height = 0.8
    header_height = 1.2
    row_gap = 0.15
    # Total rows: n_md MD bars + 1 AD expansion row
    has_ads = bool(antardashas)
    n_rows = n_md + (1 if has_ads else 0)
    fig_height = header_height + n_rows * (md_row_height + row_gap) + 1.0

    fig, ax = plt.subplots(figsize=(14, max(fig_height, 5)))
    fig.patch.set_facecolor(MPL_CREAM)
    ax.set_facecolor(MPL_CREAM)

    # Saffron header band
    ax.add_patch(FancyBboxPatch(
        (0, n_rows * (md_row_height + row_gap) + 0.1),
        1.0, header_height - 0.2,
        boxstyle="round,pad=0.05",
        facecolor=MPL_SAFFRON, edgecolor="none",
        transform=ax.get_yaxis_transform(),
    ))

    title = f"दशा कालचक्र — {chart.name}"
    subtitle = f"Lagna: {chart.lagna_sign} | DOB: {chart.dob} {chart.tob}"
    title_y = n_rows * (md_row_height + row_gap) + header_height * 0.65
    sub_y = n_rows * (md_row_height + row_gap) + header_height * 0.25

    title_kw: dict[str, Any] = {"ha": "center", "va": "center", "fontsize": 15,
                                 "fontweight": "bold", "color": "white"}
    sub_kw: dict[str, Any] = {"ha": "center", "va": "center", "fontsize": 10,
                               "color": "white"}
    if font_props:
        title_kw["fontproperties"] = font_props
        sub_kw["fontproperties"] = font_props

    mid_x = total_days / 2.0
    ax.text(mid_x, title_y, title, **title_kw)
    ax.text(mid_x, sub_y, subtitle, **sub_kw)

    # Draw MD bars (top to bottom, first MD at top)
    now = datetime.now(tz=timeline_start.tzinfo)
    current_md_index: int | None = None

    for i, md in enumerate(mahadashas):
        if md.lord == current_md.lord and md.start == current_md.start:
            current_md_index = i

    row_y = (n_rows - 1) * (md_row_height + row_gap)
    ad_inserted = False

    for i, md in enumerate(mahadashas):
        x_start = (md.start - timeline_start).total_seconds() / 86400.0
        width = (md.end - md.start).total_seconds() / 86400.0
        color = _planet_color(md.lord, benefics, malefics, yogakaraka, maraka)

        # Draw MD bar
        bar = FancyBboxPatch(
            (x_start, row_y), width, md_row_height,
            boxstyle="round,pad=0.02",
            facecolor=color, edgecolor=MPL_INDIGO,
            linewidth=1.5 if i == current_md_index else 0.8,
            alpha=1.0 if i == current_md_index else 0.75,
        )
        ax.add_patch(bar)

        # Label: Hindi name + English + year range
        hi_name = _PLANET_NAME_HI.get(md.lord, md.lord)
        label = f"{hi_name} ({md.lord})"
        date_range = f"{_date_label(md.start)}-{_date_label(md.end)}"

        label_kw: dict[str, Any] = {
            "ha": "center", "va": "center", "fontsize": 8,
            "fontweight": "bold", "color": "white",
        }
        date_kw: dict[str, Any] = {
            "ha": "center", "va": "center", "fontsize": 6.5,
            "color": "white",
        }
        if font_props:
            label_kw["fontproperties"] = font_props
            date_kw["fontproperties"] = font_props

        cx = x_start + width / 2
        ax.text(cx, row_y + md_row_height * 0.62, label, **label_kw)
        ax.text(cx, row_y + md_row_height * 0.25, date_range, **date_kw)

        # Current position marker
        if i == current_md_index and md.start <= now <= md.end:
            now_x = (now - timeline_start).total_seconds() / 86400.0
            ax.annotate(
                "▼ NOW",
                xy=(now_x, row_y + md_row_height),
                xytext=(now_x, row_y + md_row_height + 0.35),
                fontsize=8, fontweight="bold", color=MPL_SAFFRON,
                ha="center", va="bottom",
                arrowprops={"arrowstyle": "->", "color": MPL_SAFFRON, "lw": 2},
            )

        row_y -= md_row_height + row_gap

        # Insert AD sub-row after current MD
        if i == current_md_index and has_ads and not ad_inserted:
            ad_inserted = True
            _draw_ad_row(
                ax, antardashas, current_ad, timeline_start,
                row_y, ad_row_height, benefics, malefics, yogakaraka, maraka,
                font_props,
            )
            row_y -= ad_row_height + row_gap

    # Axes setup
    ax.set_xlim(-total_days * 0.02, total_days * 1.02)
    y_bottom = row_y - 0.3
    y_top = n_rows * (md_row_height + row_gap) + header_height + 0.2
    ax.set_ylim(y_bottom, y_top)
    ax.axis("off")

    plt.tight_layout(pad=0.5)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(str(path), dpi=150, bbox_inches="tight",
                    facecolor=MPL_CREAM, edgecolor="none")
        plt.close(fig)
        return None

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=MPL_CREAM, edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _draw_ad_row(
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
        color = _planet_color(ad.lord, benefics, malefics, yogakaraka, maraka)
        is_current = (ad.lord == current_ad.lord and ad.start == current_ad.start)

        bar = FancyBboxPatch(
            (x_start, row_y), width, row_h,
            boxstyle="round,pad=0.01",
            facecolor=color, edgecolor=MPL_INDIGO,
            linewidth=1.5 if is_current else 0.5,
            alpha=1.0 if is_current else 0.6,
        )
        ax.add_patch(bar)

        hi_abbr = PLANET_HI.get(ad.lord, ad.lord[:2])
        label_kw: dict[str, Any] = {
            "ha": "center", "va": "center", "fontsize": 6,
            "color": "white", "fontweight": "bold" if is_current else "normal",
        }
        if font_props:
            label_kw["fontproperties"] = font_props

        cx = x_start + width / 2
        ax.text(cx, row_y + row_h / 2, hi_abbr, **label_kw)
