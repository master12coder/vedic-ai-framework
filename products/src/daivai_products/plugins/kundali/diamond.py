"""D1 North Indian diamond chart — visual renderer with functional roles.

Renders a traditional North Indian (diamond) birth chart as PNG image with:
- Devanagari planet abbreviations with degrees
- Color coding: benefic(green), malefic(red), yogakaraka(gold)
- Retrograde/combust/exalted/debilitated markers
- Functional lordship roles per planet
- House significance labels
- Aspect lines (dotted) for special aspects
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt

from daivai_engine.constants import SIGNS_HI
from daivai_engine.models.chart import ChartData
from daivai_products.plugins.kundali.diamond_helpers import (
    CENTER_X,
    CENTER_Y,
    HOUSE_XY,
    draw_aspects,
    draw_diamond,
    get_font_props,
    parse_roles,
    planet_color,
    planet_label,
    planets_per_house,
    save_or_bytes,
)
from daivai_products.plugins.kundali.theme import (
    HOUSE_LABEL_HI,
    MPL_CREAM,
    MPL_GRAY,
    MPL_GREEN,
    MPL_INDIGO,
    MPL_SAFFRON,
)


def render_d1_chart(
    chart: ChartData,
    lordship_ctx: dict[str, Any],
    output_path: str | Path | None = None,
) -> bytes | None:
    """Render D1 North Indian diamond chart as PNG image.

    Args:
        chart: Computed birth chart.
        lordship_ctx: Lordship context from build_lordship_context().
        output_path: If provided, save to file. Otherwise return PNG bytes.

    Returns:
        PNG bytes if output_path is None, else None (saved to file).
    """
    fp_small = get_font_props(size=7)
    fp_planet = get_font_props(size=8.5)
    fp_title = get_font_props(size=15)

    fig, ax = plt.subplots(figsize=(7.5, 8.5))
    fig.patch.set_facecolor(MPL_CREAM)
    ax.set_xlim(-0.8, 5.8)
    ax.set_ylim(-0.8, 5.8)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Saffron header band ──
    ax.axhspan(5.2, 5.7, color=MPL_SAFFRON, alpha=0.9)
    ax.text(
        CENTER_X,
        5.45,
        f"कुंडली — {chart.name}",
        ha="center",
        va="center",
        fontproperties=fp_title,
        color="white",
    )

    # ── Diamond outline ──
    draw_diamond(ax)

    # ── Build planet role map ──
    benefic_set, malefic_set, yogakaraka = parse_roles(lordship_ctx)
    houses_by_planet = planets_per_house(chart)

    # ── Render each house ──
    for house in range(1, 13):
        x, y = HOUSE_XY.get(house, (CENTER_X, CENTER_Y))
        sign_idx = (chart.lagna_sign_index + house - 1) % 12
        sign_hi = SIGNS_HI[sign_idx]

        # House number + sign
        ax.text(
            x,
            y + 0.35,
            f"{house} {sign_hi}",
            ha="center",
            va="center",
            fontproperties=fp_small,
            color=MPL_GRAY,
        )
        # House significance
        label = HOUSE_LABEL_HI.get(house, "")
        ax.text(
            x,
            y + 0.22,
            label,
            ha="center",
            va="center",
            fontproperties=get_font_props(size=5.5),
            color=MPL_GRAY,
            alpha=0.7,
        )

        # Planets in this house
        planets = houses_by_planet.get(house, [])
        for i, p in enumerate(planets):
            py = y - 0.02 - i * 0.18
            color = planet_color(p.name, benefic_set, malefic_set, yogakaraka)
            lbl = planet_label(p, chart)
            ax.text(x, py, lbl, ha="center", va="center", fontproperties=fp_planet, color=color)

    # ── Lagna marker ──
    ax.text(
        CENTER_X,
        CENTER_Y,
        "लग्न",
        ha="center",
        va="center",
        fontproperties=get_font_props(size=14),
        color=MPL_GREEN,
        alpha=0.3,
    )
    ax.text(
        CENTER_X,
        CENTER_Y - 0.25,
        f"{chart.lagna_sign_hi} {chart.lagna_degree:.0f}°",
        ha="center",
        va="center",
        fontproperties=fp_small,
        color=MPL_INDIGO,
    )

    # ── Aspect lines ──
    draw_aspects(ax, chart, houses_by_planet)

    # ── Footer ──
    ax.text(
        CENTER_X,
        -0.65,
        f"{chart.dob} | {chart.tob} | {chart.place} | DaivAI",
        ha="center",
        va="center",
        fontproperties=get_font_props(size=6),
        color=MPL_GRAY,
    )

    plt.tight_layout(pad=0.5)
    return save_or_bytes(fig, output_path)
