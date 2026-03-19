"""Pure SVG North Indian diamond chart -- for HTML/PDF rendering.

Generates self-contained SVG strings (no matplotlib) with 500x500 viewBox.
Color-coded planets, Devanagari labels, status markers.
Used by the HTML kundali template and WeasyPrint PDF.
"""

from __future__ import annotations

from typing import Any
from xml.sax.saxutils import escape

from daivai_engine.constants import SIGNS_HI
from daivai_engine.models.chart import ChartData, PlanetData
from daivai_products.plugins.kundali.theme import (
    HOUSE_LABEL_HI,
    MPL_CREAM,
    MPL_GRAY,
    MPL_GREEN,
    MPL_INDIGO,
    PLANET_HI,
    planet_color_hex,
)


# ── Diamond geometry: 500x500 viewBox ────────────────────────────────────
_VB = 500
_CX, _CY = 250, 250

# House text centers -- scaled from the 300x300 web chart to 500x500
_HOUSE_XY: dict[int, tuple[float, float]] = {
    12: (250, 62),
    1: (100, 142),
    11: (400, 142),
    2: (25, 250),
    10: (475, 250),
    3: (100, 358),
    9: (400, 358),
    4: (250, 438),
    5: (100, 442),
    7: (400, 442),
    6: (250, 483),
    8: (475, 358),
}

# Status markers
_STATUS_MARKS = {"exalted": "उच्च", "debilitated": "नीच"}
_RETRO = "वक्री"
_COMBUST = "अस्त"


def render_d1_svg(
    chart: ChartData,
    lordship_ctx: dict[str, Any],
) -> str:
    """Render D1 North Indian diamond chart as an SVG string.

    Args:
        chart: Computed birth chart.
        lordship_ctx: Lordship context from build_lordship_context().

    Returns:
        Complete SVG element as a string.
    """
    benefics, malefics, yogakaraka = _parse_roles(lordship_ctx)
    houses = _planets_per_house(chart)

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {_VB} {_VB}" xmlns="http://www.w3.org/2000/svg"'
        f" style=\"font-family: 'Noto Sans Devanagari', sans-serif;\">"
    )

    # Background
    parts.append(f'<rect width="{_VB}" height="{_VB}" fill="{MPL_CREAM}"/>')

    # Diamond outline
    parts.append(_diamond_lines())

    # Center: Lagna
    parts.append(
        f'<text x="{_CX}" y="{_CY - 5}" text-anchor="middle"'
        f' font-size="22" fill="{MPL_GREEN}" opacity="0.3"'
        f' font-weight="600">लग्न</text>'
    )
    parts.append(
        f'<text x="{_CX}" y="{_CY + 18}" text-anchor="middle"'
        f' font-size="13" fill="{MPL_INDIGO}">'
        f"{escape(chart.lagna_sign_hi)} {chart.lagna_degree:.0f}°</text>"
    )

    # Houses with signs and planets
    for house in range(1, 13):
        x, y = _HOUSE_XY[house]
        sign_idx = (chart.lagna_sign_index + house - 1) % 12
        sign_hi = SIGNS_HI[sign_idx]
        house_label = HOUSE_LABEL_HI.get(house, "")

        # House number + sign
        parts.append(
            f'<text x="{x}" y="{y - 12}" text-anchor="middle"'
            f' font-size="11" fill="{MPL_GRAY}">'
            f"{house} {escape(sign_hi)}</text>"
        )
        # House significance
        parts.append(
            f'<text x="{x}" y="{y}" text-anchor="middle"'
            f' font-size="9" fill="{MPL_GRAY}" opacity="0.6">'
            f"{escape(house_label)}</text>"
        )

        # Planets
        planets = houses.get(house, [])
        for i, p in enumerate(planets):
            py = y + 16 + i * 20
            color = planet_color_hex(p.name, benefics, malefics, yogakaraka)
            label = _planet_label(p)
            parts.append(
                f'<text x="{x}" y="{py}" text-anchor="middle"'
                f' font-size="13" fill="{color}" font-weight="600">'
                f"{escape(label)}</text>"
            )

    parts.append("</svg>")
    return "\n".join(parts)


def render_divisional_svg(
    chart: ChartData,
    positions: list[Any],
    title: str,
    lordship_ctx: dict[str, Any],
) -> str:
    """Render a divisional chart (D9, D10, etc.) as SVG.

    Args:
        chart: Birth chart (for lagna reference).
        positions: List of divisional planet positions.
        title: Chart title (e.g. 'D9 Navamsha').
        lordship_ctx: Lordship context for color coding.

    Returns:
        Complete SVG element as a string.
    """
    benefics, malefics, yogakaraka = _parse_roles(lordship_ctx)

    # Build house→planets mapping from divisional positions
    # DivisionalPosition has divisional_sign_index (0-11), compute house from lagna
    houses: dict[int, list[Any]] = {}
    for pos in positions:
        if hasattr(pos, "divisional_sign_index"):
            # House = sign offset from lagna + 1
            house = ((pos.divisional_sign_index - chart.lagna_sign_index) % 12) + 1
        elif hasattr(pos, "house"):
            house = pos.house
        else:
            house = 1
        houses.setdefault(house, []).append(pos)

    parts: list[str] = []
    parts.append(
        f'<svg viewBox="0 0 {_VB} {_VB}" xmlns="http://www.w3.org/2000/svg"'
        f" style=\"font-family: 'Noto Sans Devanagari', sans-serif;\">"
    )
    parts.append(f'<rect width="{_VB}" height="{_VB}" fill="{MPL_CREAM}"/>')
    parts.append(_diamond_lines())

    # Title in center
    parts.append(
        f'<text x="{_CX}" y="{_CY}" text-anchor="middle"'
        f' font-size="16" fill="{MPL_INDIGO}" opacity="0.4"'
        f' font-weight="600">{escape(title)}</text>'
    )

    # Planets per house
    for house in range(1, 13):
        x, y = _HOUSE_XY[house]
        sign_idx = (chart.lagna_sign_index + house - 1) % 12
        sign_hi = SIGNS_HI[sign_idx]

        parts.append(
            f'<text x="{x}" y="{y - 12}" text-anchor="middle"'
            f' font-size="11" fill="{MPL_GRAY}">'
            f"{house} {escape(sign_hi)}</text>"
        )

        planets = houses.get(house, [])
        for i, pos in enumerate(planets):
            py = y + 10 + i * 18
            name = pos.planet if hasattr(pos, "planet") else getattr(pos, "name", "")
            color = planet_color_hex(name, benefics, malefics, yogakaraka)
            hi = PLANET_HI.get(name, name[:2])
            parts.append(
                f'<text x="{x}" y="{py}" text-anchor="middle"'
                f' font-size="12" fill="{color}" font-weight="600">'
                f"{escape(hi)}</text>"
            )

    parts.append("</svg>")
    return "\n".join(parts)


# ── Internal helpers ─────────────────────────────────────────────────────


def _diamond_lines() -> str:
    """Generate SVG lines for the diamond outline and grid."""
    c = MPL_INDIGO
    return (
        # Outer diamond
        f'<polygon points="{_CX},17 {_VB - 17},{_CY} {_CX},{_VB - 17} 17,{_CY}"'
        f' fill="none" stroke="{c}" stroke-width="2.5"/>'
        # Cross lines
        f'<line x1="17" y1="{_CY}" x2="{_VB - 17}" y2="{_CY}"'
        f' stroke="{c}" stroke-width="1.2"/>'
        f'<line x1="{_CX}" y1="17" x2="{_CX}" y2="{_VB - 17}"'
        f' stroke="{c}" stroke-width="1.2"/>'
        # Inner grid (house dividers)
        f'<line x1="133" y1="133" x2="367" y2="133" stroke="{c}" stroke-width="0.7"/>'
        f'<line x1="133" y1="367" x2="367" y2="367" stroke="{c}" stroke-width="0.7"/>'
        f'<line x1="133" y1="133" x2="133" y2="367" stroke="{c}" stroke-width="0.7"/>'
        f'<line x1="367" y1="133" x2="367" y2="367" stroke="{c}" stroke-width="0.7"/>'
    )


def _planet_label(p: PlanetData) -> str:
    """Build planet label: 'गु 15° (वक्री)'."""
    hi = PLANET_HI.get(p.name, p.name[:2])
    parts = [hi, f"{p.degree_in_sign:.0f}°"]

    if p.dignity in _STATUS_MARKS:
        parts.append(_STATUS_MARKS[p.dignity])
    if p.is_retrograde:
        parts.append(f"({_RETRO})")
    if p.is_combust:
        parts.append(f"({_COMBUST})")

    return " ".join(parts)


def _parse_roles(ctx: dict[str, Any]) -> tuple[set[str], set[str], str]:
    """Extract benefic/malefic/yogakaraka sets from lordship context."""
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
