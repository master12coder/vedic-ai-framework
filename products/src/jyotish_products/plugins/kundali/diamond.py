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

import io
from pathlib import Path
from typing import Any

import matplotlib


matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from jyotish_engine.constants import SIGNS_HI
from jyotish_engine.models.chart import ChartData, PlanetData
from jyotish_products.plugins.kundali.theme import (
    HOUSE_LABEL_HI,
    MPL_CREAM,
    MPL_GOLD,
    MPL_GRAY,
    MPL_GREEN,
    MPL_INDIGO,
    MPL_RED,
    MPL_SAFFRON,
    MPL_TEXT,
    PLANET_HI,
    get_font_path,
)


# ── Diamond geometry: 12 house text centers ──────────────────────────────
# Traditional North Indian layout inside a 5x5 unit diamond.
# House 1 = top-left triangle, houses go counter-clockwise.
_CENTER_X, _CENTER_Y = 2.5, 2.5
_HOUSE_XY: dict[int, tuple[float, float]] = {
    12: (2.5, 4.2),
    1:  (1.0, 3.3),  11: (4.0, 3.3),
    2:  (0.4, 2.5),  10: (4.6, 2.5),
    3:  (1.0, 1.7),  9:  (4.0, 1.7),
    4:  (2.5, 0.8),
    5:  (1.0, 0.4),  7:  (4.0, 0.4),
    6:  (2.5, 0.0),  8:  (4.6, 1.0),
}

# ── Markers ──────────────────────────────────────────────────────────────
_STATUS = {"exalted": "उच्च", "debilitated": "नीच"}
_RETRO = "वक्री"
_COMBUST = "अस्त"


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
    fp_small = _get_font_props(size=7)
    fp_planet = _get_font_props(size=8.5)
    fp_title = _get_font_props(size=15)

    fig, ax = plt.subplots(figsize=(7.5, 8.5))
    fig.patch.set_facecolor(MPL_CREAM)
    ax.set_xlim(-0.8, 5.8)
    ax.set_ylim(-0.8, 5.8)
    ax.set_aspect("equal")
    ax.axis("off")

    # ── Saffron header band ──
    ax.axhspan(5.2, 5.7, color=MPL_SAFFRON, alpha=0.9)
    ax.text(_CENTER_X, 5.45, f"कुंडली — {chart.name}",
            ha="center", va="center", fontproperties=fp_title, color="white")

    # ── Diamond outline ──
    _draw_diamond(ax)

    # ── Build planet role map ──
    benefic_set, malefic_set, yogakaraka = _parse_roles(lordship_ctx)
    houses_by_planet = _planets_per_house(chart)

    # ── Render each house ──
    for house in range(1, 13):
        x, y = _HOUSE_XY.get(house, (_CENTER_X, _CENTER_Y))
        sign_idx = (chart.lagna_sign_index + house - 1) % 12
        sign_hi = SIGNS_HI[sign_idx]

        # House number + sign
        ax.text(x, y + 0.35, f"{house} {sign_hi}",
                ha="center", va="center", fontproperties=fp_small, color=MPL_GRAY)
        # House significance
        label = HOUSE_LABEL_HI.get(house, "")
        ax.text(x, y + 0.22, label,
                ha="center", va="center", fontproperties=_get_font_props(size=5.5),
                color=MPL_GRAY, alpha=0.7)

        # Planets in this house
        planets = houses_by_planet.get(house, [])
        for i, p in enumerate(planets):
            py = y - 0.02 - i * 0.18
            color = _planet_color(p.name, benefic_set, malefic_set, yogakaraka)
            label = _planet_label(p, chart)
            ax.text(x, py, label, ha="center", va="center",
                    fontproperties=fp_planet, color=color)

    # ── Lagna marker ──
    ax.text(_CENTER_X, _CENTER_Y, "लग्न",
            ha="center", va="center", fontproperties=_get_font_props(size=14),
            color=MPL_GREEN, alpha=0.3)
    ax.text(_CENTER_X, _CENTER_Y - 0.25,
            f"{chart.lagna_sign_hi} {chart.lagna_degree:.0f}°",
            ha="center", va="center", fontproperties=fp_small, color=MPL_INDIGO)

    # ── Aspect lines ──
    _draw_aspects(ax, chart, houses_by_planet)

    # ── Footer ──
    ax.text(_CENTER_X, -0.65,
            f"{chart.dob} | {chart.tob} | {chart.place} | vedic-ai-framework",
            ha="center", va="center", fontproperties=_get_font_props(size=6),
            color=MPL_GRAY)

    plt.tight_layout(pad=0.5)
    return _save_or_bytes(fig, output_path)


# ── Drawing helpers ──────────────────────────────────────────────────────

def _draw_diamond(ax: Any) -> None:
    """Draw the traditional diamond outline and grid lines."""
    # Outer diamond (rotated square)
    dx = [_CENTER_X, 0, _CENTER_X, 5, _CENTER_X]
    dy = [4.8, _CENTER_Y, 0.2, _CENTER_Y, 4.8]
    ax.plot(dx, dy, color=MPL_INDIGO, linewidth=2.5)

    # Cross lines
    ax.plot([0, 5], [_CENTER_Y, _CENTER_Y], color=MPL_INDIGO, linewidth=1.2)
    ax.plot([_CENTER_X, _CENTER_X], [0.2, 4.8], color=MPL_INDIGO, linewidth=1.2)

    # Inner diagonals (creating triangular houses)
    ax.plot([1.25, 3.75], [3.65, 3.65], color=MPL_INDIGO, linewidth=0.6)
    ax.plot([1.25, 3.75], [1.35, 1.35], color=MPL_INDIGO, linewidth=0.6)
    ax.plot([1.25, 1.25], [1.35, 3.65], color=MPL_INDIGO, linewidth=0.6)
    ax.plot([3.75, 3.75], [1.35, 3.65], color=MPL_INDIGO, linewidth=0.6)


def _draw_aspects(ax: Any, chart: ChartData, houses: dict[int, list[PlanetData]]) -> None:
    """Draw dotted aspect lines for Saturn, Jupiter, Mars special aspects."""
    aspect_planets = {"Saturn": [3, 7, 10], "Jupiter": [5, 7, 9], "Mars": [4, 7, 8]}
    for planet_name, aspect_houses in aspect_planets.items():
        p = chart.planets.get(planet_name)
        if p is None:
            continue
        src = _HOUSE_XY.get(p.house)
        if src is None:
            continue
        for ah in aspect_houses:
            if ah == 7:
                continue  # Skip 7th (everyone has it)
            target_house = ((p.house - 1 + ah - 1) % 12) + 1
            dst = _HOUSE_XY.get(target_house)
            if dst is None:
                continue
            ax.plot([src[0], dst[0]], [src[1], dst[1]],
                    linestyle=":", linewidth=0.5, alpha=0.3,
                    color=MPL_GRAY)


def _planet_label(p: PlanetData, chart: ChartData) -> str:
    """Build planet label: 'गु 15°42' (7+10 मारक)'."""
    hi = PLANET_HI.get(p.name, p.name[:2])
    deg = f"{p.degree_in_sign:.0f}°"
    parts = [hi, deg]

    # Status markers
    if p.dignity in _STATUS:
        parts.append(_STATUS[p.dignity])
    if p.is_retrograde:
        parts.append(f"({_RETRO})")
    if p.is_combust:
        parts.append(f"({_COMBUST})")

    return " ".join(parts)


def _planet_color(
    name: str, benefics: set[str], malefics: set[str], yogakaraka: str,
) -> str:
    """Return matplotlib color string based on functional role for THIS lagna."""
    if name == yogakaraka:
        return MPL_GOLD
    if name in benefics:
        return MPL_GREEN
    if name in malefics:
        return MPL_RED
    return MPL_TEXT


def _parse_roles(ctx: dict[str, Any]) -> tuple[set[str], set[str], str]:
    """Extract benefic/malefic/yogakaraka planet sets from lordship context."""
    benefics = {e["planet"] for e in ctx.get("functional_benefics", [])}
    malefics = {e["planet"] for e in ctx.get("functional_malefics", [])}
    yk = ctx.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""
    return benefics, malefics, yogakaraka


def _planets_per_house(chart: ChartData) -> dict[int, list[PlanetData]]:
    """Group planets by house number."""
    result: dict[int, list[PlanetData]] = {}
    for p in chart.planets.values():
        result.setdefault(p.house, []).append(p)
    return result


# ── Font helper ──────────────────────────────────────────────────────────

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
        fig.savefig(str(path), dpi=150, bbox_inches="tight",
                    facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return None
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
