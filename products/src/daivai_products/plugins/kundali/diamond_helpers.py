"""D1 diamond chart helpers — geometry, drawing, labels, and utilities."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

from daivai_engine.models.chart import ChartData, PlanetData
from daivai_products.plugins.kundali.theme import (
    MPL_GOLD,
    MPL_GRAY,
    MPL_GREEN,
    MPL_INDIGO,
    MPL_RED,
    MPL_TEXT,
    PLANET_HI,
    get_font_path,
)


# ── Diamond geometry: 12 house text centers ──────────────────────────────
# Traditional North Indian layout inside a 5x5 unit diamond.
# House 1 = top-left triangle, houses go counter-clockwise.
CENTER_X, CENTER_Y = 2.5, 2.5
HOUSE_XY: dict[int, tuple[float, float]] = {
    12: (2.5, 4.2),
    1: (1.0, 3.3),
    11: (4.0, 3.3),
    2: (0.4, 2.5),
    10: (4.6, 2.5),
    3: (1.0, 1.7),
    9: (4.0, 1.7),
    4: (2.5, 0.8),
    5: (1.0, 0.4),
    7: (4.0, 0.4),
    6: (2.5, 0.0),
    8: (4.6, 1.0),
}

# ── Markers ──────────────────────────────────────────────────────────────
STATUS = {"exalted": "उच्च", "debilitated": "नीच"}
RETRO = "वक्री"
COMBUST = "अस्त"


# ── Drawing helpers ──────────────────────────────────────────────────────


def draw_diamond(ax: Any) -> None:
    """Draw the traditional diamond outline and grid lines."""
    # Outer diamond (rotated square)
    dx = [CENTER_X, 0, CENTER_X, 5, CENTER_X]
    dy = [4.8, CENTER_Y, 0.2, CENTER_Y, 4.8]
    ax.plot(dx, dy, color=MPL_INDIGO, linewidth=2.5)

    # Cross lines
    ax.plot([0, 5], [CENTER_Y, CENTER_Y], color=MPL_INDIGO, linewidth=1.2)
    ax.plot([CENTER_X, CENTER_X], [0.2, 4.8], color=MPL_INDIGO, linewidth=1.2)

    # Inner diagonals (creating triangular houses)
    ax.plot([1.25, 3.75], [3.65, 3.65], color=MPL_INDIGO, linewidth=0.6)
    ax.plot([1.25, 3.75], [1.35, 1.35], color=MPL_INDIGO, linewidth=0.6)
    ax.plot([1.25, 1.25], [1.35, 3.65], color=MPL_INDIGO, linewidth=0.6)
    ax.plot([3.75, 3.75], [1.35, 3.65], color=MPL_INDIGO, linewidth=0.6)


def draw_aspects(ax: Any, chart: ChartData, houses: dict[int, list[PlanetData]]) -> None:
    """Draw dotted aspect lines for Saturn, Jupiter, Mars special aspects."""
    aspect_planets = {"Saturn": [3, 7, 10], "Jupiter": [5, 7, 9], "Mars": [4, 7, 8]}
    for planet_name, aspect_houses in aspect_planets.items():
        p = chart.planets.get(planet_name)
        if p is None:
            continue
        src = HOUSE_XY.get(p.house)
        if src is None:
            continue
        for ah in aspect_houses:
            if ah == 7:
                continue  # Skip 7th (everyone has it)
            target_house = ((p.house - 1 + ah - 1) % 12) + 1
            dst = HOUSE_XY.get(target_house)
            if dst is None:
                continue
            ax.plot(
                [src[0], dst[0]],
                [src[1], dst[1]],
                linestyle=":",
                linewidth=0.5,
                alpha=0.3,
                color=MPL_GRAY,
            )


# ── Label / color helpers ────────────────────────────────────────────────


def planet_label(p: PlanetData, chart: ChartData) -> str:
    """Build planet label: 'गु 15°42' (7+10 मारक)'."""
    hi = PLANET_HI.get(p.name, p.name[:2])
    deg = f"{p.degree_in_sign:.0f}°"
    parts = [hi, deg]

    # Status markers
    if p.dignity in STATUS:
        parts.append(STATUS[p.dignity])
    if p.is_retrograde:
        parts.append(f"({RETRO})")
    if p.is_combust:
        parts.append(f"({COMBUST})")

    return " ".join(parts)


def planet_color(
    name: str,
    benefics: set[str],
    malefics: set[str],
    yogakaraka: str,
) -> str:
    """Return matplotlib color string based on functional role for THIS lagna."""
    if name == yogakaraka:
        return MPL_GOLD
    if name in benefics:
        return MPL_GREEN
    if name in malefics:
        return MPL_RED
    return MPL_TEXT


def parse_roles(ctx: dict[str, Any]) -> tuple[set[str], set[str], str]:
    """Extract benefic/malefic/yogakaraka planet sets from lordship context."""
    benefics = {e["planet"] for e in ctx.get("functional_benefics", [])}
    malefics = {e["planet"] for e in ctx.get("functional_malefics", [])}
    yk = ctx.get("yogakaraka", {})
    yogakaraka = yk.get("planet", "") if isinstance(yk, dict) else ""
    return benefics, malefics, yogakaraka


def planets_per_house(chart: ChartData) -> dict[int, list[PlanetData]]:
    """Group planets by house number."""
    result: dict[int, list[PlanetData]] = {}
    for p in chart.planets.values():
        result.setdefault(p.house, []).append(p)
    return result


# ── Font helper ──────────────────────────────────────────────────────────


def get_font_props(size: float = 10) -> FontProperties:
    """Get matplotlib FontProperties with Devanagari support."""
    fp_path = get_font_path()
    if fp_path and fp_path.exists():
        return FontProperties(fname=str(fp_path), size=size)
    return FontProperties(size=size)


def save_or_bytes(fig: Any, output_path: str | Path | None) -> bytes | None:
    """Save figure to file or return PNG bytes."""
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            str(path), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none"
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
