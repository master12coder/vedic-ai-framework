"""Ashtakavarga heatmap renderer — color-coded bindu grid as PNG image.

Renders an 8-row (7 planets + SAV total) x 12-column (Aries-Pisces) grid.
Each cell shows the bindu count with color coding:
  Green (#2E7D32): 5-8 bindus (strong)
  Gold  (#FF8F00): 3-4 bindus (moderate)
  Red   (#C62828): 0-2 bindus (weak)
SAV row uses separate thresholds: green 30+, gold 25-29, red <25.
"""

from __future__ import annotations

import io
from pathlib import Path

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from jyotish_engine.constants import SIGNS_HI
from jyotish_engine.models.ashtakavarga import AshtakavargaResult
from jyotish_engine.models.chart import ChartData
from jyotish_products.plugins.kundali.theme import (
    MPL_CREAM,
    MPL_GOLD,
    MPL_GREEN,
    MPL_INDIGO,
    MPL_RED,
    MPL_SAFFRON,
    MPL_TEXT,
    PLANET_HI,
    get_font_path,
)


# The 7 Ashtakavarga planets in display order.
_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Row labels: 7 planets + SAV total.
_ROW_LABELS = [PLANET_HI[p] for p in _PLANETS] + ["SAV"]


def _planet_cell_color(bindus: int) -> str:
    """Return cell background color for a planet bindu count (0-8)."""
    if bindus >= 5:
        return MPL_GREEN
    if bindus >= 3:
        return MPL_GOLD
    return MPL_RED


def _sav_cell_color(bindus: int) -> str:
    """Return cell background color for a SAV bindu count (0-56)."""
    if bindus >= 30:
        return MPL_GREEN
    if bindus >= 25:
        return MPL_GOLD
    return MPL_RED


def _load_font() -> FontProperties | None:
    """Load Devanagari font for matplotlib if available."""
    font_path = get_font_path()
    if font_path and font_path.exists():
        return FontProperties(fname=str(font_path))
    return None


def render_ashtakavarga_heatmap(
    chart: ChartData,
    ashtakavarga: AshtakavargaResult,
    output_path: str | Path | None = None,
) -> bytes | None:
    """Render Ashtakavarga heatmap as a color-coded PNG grid.

    Args:
        chart: Computed birth chart (used for title metadata).
        ashtakavarga: Pre-computed Ashtakavarga result with bhinna and sarva.
        output_path: If provided, save PNG to file. Otherwise return bytes.

    Returns:
        PNG bytes if output_path is None, else None (saved to file).
    """
    font_prop = _load_font()
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(MPL_CREAM)
    ax.set_facecolor(MPL_CREAM)
    ax.axis("off")

    n_rows = 8  # 7 planets + SAV
    n_cols = 12  # 12 signs

    # Grid geometry
    cell_w = 0.8
    cell_h = 0.55
    x_start = 1.6
    y_start = 0.2
    header_h = 0.5
    row_label_w = 1.2

    # Total grid dimensions
    grid_w = n_cols * cell_w
    grid_h = n_rows * cell_h

    # Set axis limits
    ax.set_xlim(-0.1, x_start + grid_w + 0.3)
    ax.set_ylim(-0.3, y_start + grid_h + header_h + 1.5)

    # Font kwargs for text calls
    font_kw: dict = {}
    if font_prop:
        font_kw["fontproperties"] = font_prop

    # ── Saffron header band with title ─────────────────────────────────
    title_y = y_start + grid_h + header_h + 0.5
    ax.axhspan(title_y - 0.3, title_y + 0.5, color=MPL_SAFFRON, alpha=0.9)
    ax.text(
        (x_start + grid_w / 2),
        title_y + 0.1,
        f"अष्टकवर्ग — {chart.name}",
        ha="center",
        va="center",
        fontsize=16,
        fontweight="bold",
        color="white",
        **font_kw,
    )

    # ── Column headers (sign names in Hindi) ───────────────────────────
    col_header_y = y_start + grid_h
    for col in range(n_cols):
        cx = x_start + col * cell_w + cell_w / 2
        cy = col_header_y + header_h / 2
        ax.text(
            cx,
            cy,
            SIGNS_HI[col],
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=MPL_INDIGO,
            **font_kw,
        )

    # ── Row headers + data cells ───────────────────────────────────────
    for row in range(n_rows):
        # Row y position (top row = row 0 = first planet)
        ry = y_start + (n_rows - 1 - row) * cell_h

        # Row label
        label = _ROW_LABELS[row]
        lx = x_start - row_label_w / 2
        ly = ry + cell_h / 2
        label_weight = "bold" if row == n_rows - 1 else "normal"
        ax.text(
            lx,
            ly,
            label,
            ha="center",
            va="center",
            fontsize=11,
            fontweight=label_weight,
            color=MPL_TEXT,
            **font_kw,
        )

        # Get bindu values for this row
        if row < 7:
            planet = _PLANETS[row]
            values = ashtakavarga.bhinna[planet]
            color_fn = _planet_cell_color
        else:
            values = ashtakavarga.sarva
            color_fn = _sav_cell_color

        for col in range(n_cols):
            cx = x_start + col * cell_w
            cy = ry
            bindus = values[col]
            bg = color_fn(bindus)

            # Draw cell rectangle
            rect = plt.Rectangle(
                (cx, cy),
                cell_w,
                cell_h,
                facecolor=bg,
                edgecolor="white",
                linewidth=1.5,
            )
            ax.add_patch(rect)

            # Bindu text
            ax.text(
                cx + cell_w / 2,
                cy + cell_h / 2,
                str(bindus),
                ha="center",
                va="center",
                fontsize=11,
                fontweight="bold",
                color="white",
            )

    # ── SAV total annotation ───────────────────────────────────────────
    total = ashtakavarga.total
    total_x = x_start + grid_w + 0.15
    total_y = y_start + cell_h / 2
    ax.text(
        total_x,
        total_y,
        f"= {total}",
        ha="left",
        va="center",
        fontsize=12,
        fontweight="bold",
        color=MPL_INDIGO,
        **font_kw,
    )

    plt.tight_layout(pad=0.5)

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
