"""Chart Selector -- decides which divisional charts to display for a query.

Given a query type (career, marriage, health, etc.) and a pre-computed
FullChartAnalysis, this module selects the primary divisional chart and
supporting charts that are most relevant, factoring in vargottam planets,
current dasha lords, and house-specific conditions.

Source: BPHS Ch.6-7 (Varga Significations), five-layers.md Layer 3 spec.
"""

from __future__ import annotations

from daivai_engine.constants.signs import SIGN_LORDS
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.models import ChartSelection


# ── Query-to-chart mapping ───────────────────────────────────────────────────
# Each entry: (primary_chart, supporting_charts, key_planets, key_houses)
# key_planets: planets whose involvement may boost additional charts
# key_houses: houses whose lord condition may refine selection

type _ChartSpec = tuple[str, list[str], list[str], list[int]]

_QUERY_CHART_MAP: dict[str, _ChartSpec] = {
    "career": (
        "D10",
        ["D1", "D9", "D60", "D24"],
        ["Sun", "Saturn", "Mercury", "Jupiter"],
        [1, 10, 7],
    ),
    "marriage": (
        "D9",
        ["D1", "D7", "D60", "D30"],
        ["Venus", "Jupiter", "Moon"],
        [7, 1, 2],
    ),
    "health": (
        "D30",
        ["D1", "D9", "D3", "D60"],
        ["Sun", "Moon", "Mars"],
        [1, 6, 8],
    ),
    "children": (
        "D7",
        ["D1", "D9", "D60", "D12"],
        ["Jupiter"],
        [5, 9, 7],
    ),
    "education": (
        "D24",
        ["D1", "D9", "D60", "D20"],
        ["Mercury", "Jupiter"],
        [4, 5, 9],
    ),
    "wealth": (
        "D2",
        ["D1", "D9", "D60", "D10"],
        ["Jupiter", "Venus", "Mercury"],
        [2, 11, 1],
    ),
    "spiritual": (
        "D20",
        ["D1", "D9", "D60", "D27"],
        ["Jupiter", "Ketu", "Saturn"],
        [9, 12, 5],
    ),
    "general": (
        "D1",
        ["D9", "D10", "D60"],
        [],
        [1, 7, 10],
    ),
    "property": (
        "D4",
        ["D1", "D9", "D60", "D2"],
        ["Mars", "Venus"],
        [4, 1, 2],
    ),
    "longevity": (
        "D3",
        ["D1", "D9", "D60", "D30"],
        ["Saturn"],
        [8, 1, 3],
    ),
}


def select_charts(query_type: str, analysis: FullChartAnalysis) -> ChartSelection:
    """Select relevant divisional charts for a given query type.

    Args:
        query_type: One of career, marriage, health, children, education,
                    wealth, spiritual, general, property, longevity.
                    Unknown types fall back to "general".
        analysis: Pre-computed FullChartAnalysis from engine.

    Returns:
        ChartSelection with the primary chart, supporting charts, and a
        reason string explaining the selection logic.
    """
    normalized = query_type.strip().lower()
    spec = _QUERY_CHART_MAP.get(normalized, _QUERY_CHART_MAP["general"])
    primary, supporting, key_planets, key_houses = spec

    # Build a mutable copy of supporting charts for potential additions
    supporting = list(supporting)

    # Build reasoning parts
    reason_parts: list[str] = [
        f"Query '{normalized}': primary chart {primary}, supported by {', '.join(supporting)}.",
    ]

    # Check vargottam planets -- boost D9 if relevant vargottam planet found
    vargottam_note = _check_vargottam_relevance(analysis, key_planets, key_houses)
    if vargottam_note:
        reason_parts.append(vargottam_note)

    # Check dasha lord involvement -- if current MD/AD lord is a key planet,
    # note it in the reasoning as it confirms chart relevance
    dasha_notes = _check_dasha_relevance(analysis, key_planets, normalized, supporting)
    reason_parts.extend(dasha_notes)

    # Check house lord conditions for the key houses
    house_notes = _check_house_conditions(analysis, key_houses, normalized)
    reason_parts.extend(house_notes)

    return ChartSelection(
        query_type=normalized,
        primary_chart=primary,
        supporting_charts=supporting,
        reason=" ".join(reason_parts),
    )


def _check_vargottam_relevance(
    analysis: FullChartAnalysis,
    key_planets: list[str],
    key_houses: list[int],
) -> str:
    """Identify vargottam planets relevant to this query.

    A planet is relevant if it is either a key planet for the query type
    or lords one of the key houses.

    Returns:
        Reasoning note about vargottam relevance, or empty string.
    """
    if not analysis.vargottam_planets:
        return ""

    lagna_idx = analysis.chart.lagna_sign_index
    house_lords = _get_house_lords(lagna_idx, key_houses)

    relevant: list[str] = []
    for planet in analysis.vargottam_planets:
        if planet in key_planets or planet in house_lords:
            relevant.append(planet)

    if relevant:
        return (
            f"Vargottam planets relevant to this query: "
            f"{', '.join(relevant)} -- D9 cross-check elevated."
        )
    return ""


def _check_dasha_relevance(
    analysis: FullChartAnalysis,
    key_planets: list[str],
    query_type: str,
    supporting: list[str],
) -> list[str]:
    """Check if current dasha lords are key planets for this query.

    If the MD or AD lord is a key planet, add relevant divisional chart
    to supporting list (if not already present) and note it.

    Args:
        supporting: Mutable list -- may be modified in-place.

    Returns:
        List of reasoning strings.
    """
    notes: list[str] = []
    md_lord = analysis.current_md.lord
    ad_lord = analysis.current_ad.lord

    # Extra chart to add when dasha lord matches a key planet
    dasha_chart_boost: dict[str, str] = {
        "career": "D10",
        "marriage": "D9",
        "children": "D7",
        "education": "D24",
        "wealth": "D2",
        "spiritual": "D20",
        "property": "D4",
        "longevity": "D3",
    }

    chart = dasha_chart_boost.get(query_type)
    if not chart:
        return notes

    if md_lord in key_planets:
        if chart not in supporting:
            supporting.append(chart)
        notes.append(
            f"Mahadasha lord {md_lord} is a {query_type} significator "
            f"-- {chart} analysis confirmed."
        )

    if ad_lord in key_planets and ad_lord != md_lord:
        if chart not in supporting:
            supporting.append(chart)
        notes.append(
            f"Antardasha lord {ad_lord} also signifies {query_type} "
            f"-- {chart} relevance reinforced."
        )

    return notes


def _check_house_conditions(
    analysis: FullChartAnalysis,
    key_houses: list[int],
    query_type: str,
) -> list[str]:
    """Examine key house lords for noteworthy conditions.

    Produces reasoning notes about retrograde, combust, debilitated, or
    exalted lords of the key houses that affect interpretation confidence.

    Returns:
        List of reasoning strings.
    """
    notes: list[str] = []
    lagna_idx = analysis.chart.lagna_sign_index

    for house_num in key_houses:
        sign_idx = (lagna_idx + house_num - 1) % 12
        lord = SIGN_LORDS[sign_idx]

        planet_data = analysis.chart.planets.get(lord)
        if not planet_data:
            continue

        conditions: list[str] = []
        if planet_data.is_retrograde:
            conditions.append("retrograde")
        if planet_data.is_combust:
            conditions.append("combust")
        if planet_data.dignity == "debilitated":
            conditions.append("debilitated")
        elif planet_data.dignity == "exalted":
            conditions.append("exalted")

        if conditions:
            status = ", ".join(conditions)
            notes.append(
                f"House {house_num} lord {lord} is {status} -- "
                f"D9 cross-check important for {query_type} accuracy."
            )

    return notes


def _get_house_lords(lagna_sign_index: int, houses: list[int]) -> list[str]:
    """Return the lordship planet for each given house number.

    Args:
        lagna_sign_index: 0-11 sign index of the lagna.
        houses: List of house numbers (1-12).

    Returns:
        Deduplicated list of planet names that lord the given houses.
    """
    lords: list[str] = []
    for house_num in houses:
        sign_idx = (lagna_sign_index + house_num - 1) % 12
        lord = SIGN_LORDS[sign_idx]
        if lord not in lords:
            lords.append(lord)
    return lords
