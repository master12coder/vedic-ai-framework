"""Shadbala horizontal bar chart renderer — planetary strength visualization.

Renders a horizontal bar chart showing Shadbala ratios for the 7 classical
planets. Bars are green (strong, ratio >= 1.0) or red (weak, ratio < 1.0).
A vertical dashed line marks the 1.0 threshold. The strongest and weakest
planets are highlighted beneath the chart.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from jyotish_engine.models.chart import ChartData
from jyotish_engine.models.strength import ShadbalaResult
from jyotish_products.plugins.kundali.theme import (
    MPL_CREAM,
    MPL_GRAY,
    MPL_GREEN,
    MPL_INDIGO,
    MPL_RED,
    MPL_SAFFRON,
    PLANET_HI,
    get_font_path,
)


def render_shadbala_chart(
    chart: ChartData,
    shadbala: list[ShadbalaResult],
    output_path: str | Path | None = None,
) -> bytes | None:
    """Render horizontal Shadbala strength bars as a PNG image.

    Args:
        chart: Computed birth chart (used for header text).
        shadbala: Pre-computed ShadbalaResult list for 7 classical planets.
        output_path: If provided, save to file. Otherwise return PNG bytes.

    Returns:
        PNG bytes if output_path is None, else None (saved to file).
    """
    # Sort by rank descending so strongest appears at top of chart
    sorted_bala = sorted(shadbala, key=lambda s: s.rank, reverse=True)

    fp_title = _get_font_props(size=14)
    fp_label = _get_font_props(size=10)
    fp_value = _get_font_props(size=9)
    fp_note = _get_font_props(size=10)
    fp_footer = _get_font_props(size=7)

    n = len(sorted_bala)
    fig_height = max(4.0, 1.0 + n * 0.55 + 1.5)
    fig, ax = plt.subplots(figsize=(8, fig_height))
    fig.patch.set_facecolor(MPL_CREAM)
    ax.set_facecolor(MPL_CREAM)

    # -- Saffron header band --
    ax.text(
        0.5,
        1.02,
        f"षड्बल — Shadbala | {chart.name}",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontproperties=fp_title,
        color="white",
        bbox=dict(
            boxstyle="square,pad=0.4",
            facecolor=MPL_SAFFRON,
            edgecolor="none",
        ),
    )

    # -- Build bars --
    y_positions = list(range(n))
    ratios = [s.ratio for s in sorted_bala]
    colors = [MPL_GREEN if s.is_strong else MPL_RED for s in sorted_bala]
    labels = [f"{PLANET_HI.get(s.planet, s.planet)} {s.planet}" for s in sorted_bala]

    bars = ax.barh(y_positions, ratios, color=colors, height=0.6, edgecolor="none")

    # -- Y-axis labels (planet names) --
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels, fontproperties=fp_label)

    # -- Ratio value on each bar --
    for bar, sb in zip(bars, sorted_bala, strict=True):
        x_pos = bar.get_width() + 0.03
        ax.text(
            x_pos,
            bar.get_y() + bar.get_height() / 2,
            f"{sb.ratio:.2f}",
            va="center",
            ha="left",
            fontproperties=fp_value,
            color=MPL_INDIGO,
        )

    # -- Threshold line at 1.0 --
    ax.axvline(x=1.0, color=MPL_GRAY, linestyle="--", linewidth=1.5)
    ax.text(
        1.0,
        n - 0.2,
        "Required",
        ha="center",
        va="bottom",
        fontproperties=_get_font_props(size=8),
        color=MPL_GRAY,
    )

    # -- X-axis --
    max_ratio = max(ratios) if ratios else 2.0
    ax.set_xlim(0, max(max_ratio * 1.15, 1.5))
    ax.set_xlabel("Shadbala Ratio (total / required)", fontproperties=fp_label)

    # -- Remove top and right spines --
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # -- Strongest / weakest annotation --
    strongest, weakest = _find_extremes(shadbala)
    note_lines: list[str] = []
    if strongest:
        hi = PLANET_HI.get(strongest.planet, strongest.planet)
        note_lines.append(f"सबसे बलवान: {hi} ({strongest.ratio:.2f})")
    if weakest:
        hi = PLANET_HI.get(weakest.planet, weakest.planet)
        note_lines.append(f"सबसे कमजोर: {hi} ({weakest.ratio:.2f})")

    if note_lines:
        note_text = "    |    ".join(note_lines)
        ax.text(
            0.5,
            -0.08,
            note_text,
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontproperties=fp_note,
            color=MPL_INDIGO,
        )

    # -- Footer --
    ax.text(
        0.5,
        -0.14,
        f"{chart.dob} | {chart.tob} | {chart.place} | vedic-ai-framework",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontproperties=fp_footer,
        color=MPL_GRAY,
    )

    plt.tight_layout(pad=1.5)
    return _save_or_bytes(fig, output_path)


# -- Helpers ------------------------------------------------------------------


def _find_extremes(
    shadbala: list[ShadbalaResult],
) -> tuple[ShadbalaResult | None, ShadbalaResult | None]:
    """Find strongest (rank 1) and weakest (highest rank) planets."""
    if not shadbala:
        return None, None
    strongest = min(shadbala, key=lambda s: s.rank)
    weakest = max(shadbala, key=lambda s: s.rank)
    return strongest, weakest


def _get_font_props(size: float = 10) -> FontProperties:
    """Get matplotlib FontProperties with Devanagari support."""
    fp_path = get_font_path()
    if fp_path and fp_path.exists():
        return FontProperties(fname=str(fp_path), size=size)
    return FontProperties(size=size)


def _save_or_bytes(fig: Any, output_path: str | Path | None) -> bytes | None:
    """Save figure to file or return PNG bytes."""
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            str(path),
            dpi=150,
            bbox_inches="tight",
            facecolor=fig.get_facecolor(),
            edgecolor="none",
        )
        plt.close(fig)
        return None
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)
    buf.seek(0)
    return buf.read()
