"""North Indian diamond chart — text-based renderer."""
from __future__ import annotations

from jyotish_engine.models.chart import ChartData
from jyotish_engine.constants import SIGNS


# North Indian chart layout: house numbers map to diamond positions
# The diamond shape has 12 cells arranged as:
#        [12]
#     [1]    [11]
#  [2]   [lagna]  [10]
#     [3]    [9]
#  [4]          [8]
#     [5]    [7]
#        [6]

def _get_planets_by_house(chart: ChartData) -> dict[int, list[str]]:
    """Group planet abbreviations by house number."""
    abbrev = {
        "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
        "Rahu": "Ra", "Ketu": "Ke",
    }
    houses: dict[int, list[str]] = {h: [] for h in range(1, 13)}
    for p in chart.planets.values():
        label = abbrev.get(p.name, p.name[:2])
        if p.is_retrograde:
            label += "(R)"
        houses[p.house].append(label)
    return houses


def render_diamond_text(chart: ChartData) -> str:
    """Render a North Indian style diamond chart as text.

    Returns a multi-line string showing the 12 houses in diamond layout
    with planet abbreviations placed in their respective houses.
    """
    houses = _get_planets_by_house(chart)

    def _cell(house_num: int, width: int = 12) -> str:
        """Format house content."""
        sign = SIGNS[(chart.lagna_sign_index + house_num - 1) % 12]
        planets_str = " ".join(houses[house_num])
        label = f"{house_num}:{sign[:3]}"
        if planets_str:
            content = f"{label} {planets_str}"
        else:
            content = label
        return content.center(width)

    # Build the diamond as a text grid
    w = 14
    lines = [
        f"{'':>14}{_cell(12, w)}",
        f"{'':>7}{_cell(1, w)}{_cell(11, w)}",
        f"{_cell(2, w)}{'Lagna'.center(w)}{_cell(10, w)}",
        f"{'':>7}{_cell(3, w)}{_cell(9, w)}",
        f"{_cell(4, w)}{'':>{w}}{_cell(8, w)}",
        f"{'':>7}{_cell(5, w)}{_cell(7, w)}",
        f"{'':>14}{_cell(6, w)}",
    ]

    header = f"  North Indian Chart — {chart.name}"
    subheader = f"  Lagna: {chart.lagna_sign} ({chart.lagna_sign_en}) {chart.lagna_degree:.1f}°"

    return "\n".join([header, subheader, "─" * 56] + lines + ["─" * 56])


def render_chart_summary(chart: ChartData) -> str:
    """Render a concise chart summary with all key data."""
    lines = [
        f"═══ Kundali — {chart.name} ═══",
        f"DOB: {chart.dob} | TOB: {chart.tob} | Place: {chart.place}",
        f"Lagna: {chart.lagna_sign} ({chart.lagna_sign_en} / {chart.lagna_sign_hi}) at {chart.lagna_degree:.1f}°",
        "",
        "Planetary Positions:",
        f"{'Planet':<10} {'Sign':<12} {'House':>5} {'Deg':>7} {'Nakshatra':<15} {'Dignity':<10} {'R':>2} {'C':>2}",
        "─" * 72,
    ]

    for p in chart.planets.values():
        r_flag = "R" if p.is_retrograde else ""
        c_flag = "C" if p.is_combust else ""
        lines.append(
            f"{p.name:<10} {p.sign:<12} {p.house:>5} {p.degree_in_sign:>6.1f}° "
            f"{p.nakshatra:<15} {p.dignity:<10} {r_flag:>2} {c_flag:>2}"
        )

    return "\n".join(lines)
