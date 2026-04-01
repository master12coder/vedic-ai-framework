"""House Highlighter -- identifies the most relevant houses for a query.

Given a query type and FullChartAnalysis, this module selects primary and
supporting houses, identifies natural karakas, and provides reasoning
explaining why each house matters. This guides the AI interpretation layer
to focus on the right bhava lords and occupants.

Source: BPHS Ch.5 "Bhava Adhyaya", Ch.20 "Bhava Phala".
"""

from __future__ import annotations

from daivai_engine.constants.signs import SIGN_LORDS
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.models import HouseHighlight


# ── Per-house reasoning by query type ────────────────────────────────────────
# Maps house number to {query_type: reason_string}.
# Only houses that are primary for at least one query are included.

_HOUSE_REASONS: dict[int, dict[str, str]] = {
    1: {
        "career": "Lagna reflects personality and initiative in career",
        "marriage": "Lagna represents the self -- compatibility starts here",
        "health": "Lagna is the primary house of physical body and vitality",
        "children": "Lagna lord strength determines ability to raise children",
        "education": "Lagna intelligence and aptitude set learning foundation",
        "wealth": "Lagna lord is the self -- primary wealth generator",
        "spiritual": "Lagna is the physical vessel for spiritual practice",
        "general": "Lagna is the foundation of the entire chart",
        "property": "Lagna lord placement determines fortune in assets",
        "longevity": "Lagna and its lord are primary longevity indicators",
    },
    2: {
        "career": "2nd house shows accumulated wealth from profession",
        "marriage": "2nd house is maraka + represents family after marriage",
        "health": "2nd house governs face, mouth, and dietary health",
        "wealth": "2nd house is dhana bhava -- stored wealth and assets",
        "children": "2nd house represents family lineage continuation",
        "general": "2nd house governs wealth, speech, and family",
        "property": "2nd house shows stored resources for property purchase",
    },
    3: {
        "longevity": "3rd house is the 8th from 8th -- secondary longevity indicator",
    },
    4: {
        "education": "4th house governs formal education and academic setting",
        "general": "4th house represents happiness, property, and mother",
        "property": "4th house is the primary bhava for land and real estate",
    },
    5: {
        "children": "5th house is putra bhava -- primary house of progeny",
        "education": "5th house governs intelligence and higher learning aptitude",
        "wealth": "5th house is purva punya -- past merit yielding sudden gains",
        "spiritual": "5th house governs mantras, devotion, and sadhana",
        "general": "5th house represents intelligence, children, past merit",
    },
    6: {
        "career": "6th house shows competition, service, and daily work",
        "health": "6th house is roga bhava -- primary house of disease",
        "longevity": "6th house affliction can indicate chronic health challenges",
    },
    7: {
        "career": "7th house governs partnerships and business dealings",
        "marriage": "7th house is the primary marriage and partnership house",
        "children": "7th house represents spouse who co-creates children",
        "general": "7th house governs marriage, partnerships, public dealings",
    },
    8: {
        "health": "8th house governs chronic disease, surgery, hidden ailments",
        "marriage": "8th house shows mangalya strength and in-laws",
        "longevity": "8th house is ayus bhava -- primary house of lifespan",
        "spiritual": "8th house governs occult knowledge and transformation",
    },
    9: {
        "children": "9th house is 5th from 5th -- grandchildren and fortune",
        "education": "9th house governs higher education, guru, philosophy",
        "wealth": "9th house is bhagya -- fortune that multiplies wealth",
        "spiritual": "9th house is dharma bhava -- religion, guru, spiritual path",
        "general": "9th house governs fortune, dharma, and father",
    },
    10: {
        "career": "10th house is karma bhava -- primary house of profession",
        "wealth": "10th house shows income from career and social standing",
        "general": "10th house governs career, fame, and public actions",
    },
    11: {
        "career": "11th house shows income, gains, and wish fulfillment",
        "wealth": "11th house is labha bhava -- gains, profits, realized income",
    },
    12: {
        "health": "12th house governs hospitalization and hidden weaknesses",
        "marriage": "12th house shows bed pleasures and foreign settlement",
        "spiritual": "12th house is moksha bhava -- liberation from the world",
    },
}

# ── Query-to-house mapping ───────────────────────────────────────────────────
# (primary_houses, supporting_houses, karaka_planets)

type _HouseSpec = tuple[list[int], list[int], list[str]]

_QUERY_HOUSE_MAP: dict[str, _HouseSpec] = {
    "career": ([1, 10, 7], [2, 11, 6], ["Sun", "Saturn", "Mercury", "Jupiter"]),
    "marriage": ([7, 1, 2], [5, 8, 12], ["Venus", "Jupiter", "Moon"]),
    "health": ([1, 6, 8], [12, 2], ["Sun", "Moon", "Mars"]),
    "children": ([5, 9, 7], [1, 2], ["Jupiter"]),
    "education": ([4, 5, 9], [1, 2], ["Mercury", "Jupiter"]),
    "wealth": ([2, 11, 1], [5, 9, 10], ["Jupiter", "Venus", "Mercury"]),
    "spiritual": ([9, 12, 5], [1, 8], ["Jupiter", "Ketu", "Saturn"]),
    "general": ([1, 7, 10], [4, 5, 9], []),  # karakas resolved dynamically
    "property": ([4, 1, 2], [7, 10], ["Mars", "Venus", "Moon"]),
    "longevity": ([8, 1, 3], [12, 6], ["Saturn"]),
}


def highlight_houses(query_type: str, analysis: FullChartAnalysis) -> HouseHighlight:
    """Identify the most relevant houses and karakas for a query type.

    Args:
        query_type: One of career, marriage, health, children, education,
                    wealth, spiritual, general, property, longevity.
                    Unknown types fall back to "general".
        analysis: Pre-computed FullChartAnalysis from engine.

    Returns:
        HouseHighlight with primary/supporting houses, karaka planets,
        and a reason string summarising the selection logic.
    """
    normalized = query_type.strip().lower()
    spec = _QUERY_HOUSE_MAP.get(normalized, _QUERY_HOUSE_MAP["general"])
    primary, supporting, karakas = spec

    # For "general" queries or empty karakas, inject the lagna lord
    if not karakas:
        karakas = _resolve_general_karakas(analysis)

    # Build the composite reason string
    reason = _build_reason(analysis, primary, supporting, karakas, normalized)

    return HouseHighlight(
        query_type=normalized,
        primary_houses=primary,
        supporting_houses=supporting,
        karaka_planets=karakas,
        reason=reason,
    )


def _resolve_general_karakas(analysis: FullChartAnalysis) -> list[str]:
    """For general queries, derive karakas from the lagna lord.

    The lagna lord is always relevant. Additionally includes Sun (natural
    lagna karaka) and Moon (mind/emotions) for a general overview.

    Returns:
        List of karaka planet names.
    """
    lagna_lord = analysis.lagna_lord
    karakas = [lagna_lord]
    for planet in ("Sun", "Moon"):
        if planet != lagna_lord:
            karakas.append(planet)
    return karakas


def _build_reason(
    analysis: FullChartAnalysis,
    primary: list[int],
    supporting: list[int],
    karakas: list[str],
    query_type: str,
) -> str:
    """Build a composite reason string with chart-specific observations.

    Combines per-house reasoning with karaka conditions and house lord
    dignity observations.

    Returns:
        A single multi-sentence reason string.
    """
    parts: list[str] = []

    # Per-house reasons for primary houses
    for house_num in primary:
        house_map = _HOUSE_REASONS.get(house_num, {})
        reason = house_map.get(query_type)
        if reason:
            parts.append(f"H{house_num}: {reason}.")

    # Supporting houses summary
    if supporting:
        parts.append(f"Supporting: H{', H'.join(str(h) for h in supporting)}.")

    # Karaka planet conditions
    karaka_notes = _assess_karaka_conditions(analysis, karakas)
    parts.extend(karaka_notes)

    # Primary house lord conditions
    lord_notes = _assess_house_lord_conditions(analysis, primary, query_type)
    parts.extend(lord_notes)

    return " ".join(parts)


def _assess_karaka_conditions(
    analysis: FullChartAnalysis,
    karakas: list[str],
) -> list[str]:
    """Check dignity, retrogression, combustion, and vargottam for karakas.

    Returns:
        List of observation strings.
    """
    notes: list[str] = []
    for planet_name in karakas:
        planet = analysis.chart.planets.get(planet_name)
        if not planet:
            continue

        flags: list[str] = []
        if planet.dignity == "exalted":
            flags.append("exalted")
        elif planet.dignity == "debilitated":
            flags.append("debilitated")
        if planet.is_retrograde:
            flags.append("retrograde")
        if planet.is_combust:
            flags.append("combust")
        if planet.name in analysis.vargottam_planets:
            flags.append("vargottam")

        if flags:
            notes.append(
                f"Karaka {planet_name}: {', '.join(flags)} in {planet.sign} (H{planet.house})."
            )
    return notes


def _assess_house_lord_conditions(
    analysis: FullChartAnalysis,
    primary_houses: list[int],
    query_type: str,
) -> list[str]:
    """Examine lords of primary houses for notable conditions.

    A debilitated, combust, or exalted lord significantly affects the
    reliability and nature of predictions for that life area.

    Returns:
        List of observation strings.
    """
    notes: list[str] = []
    lagna_idx = analysis.chart.lagna_sign_index

    for house_num in primary_houses:
        sign_idx = (lagna_idx + house_num - 1) % 12
        lord = SIGN_LORDS[sign_idx]
        planet = analysis.chart.planets.get(lord)
        if not planet:
            continue

        # Only flag noteworthy conditions
        flags: list[str] = []
        if planet.dignity in ("debilitated", "exalted"):
            flags.append(planet.dignity)
        if planet.is_combust:
            flags.append("combust")
        if planet.is_retrograde:
            flags.append("retrograde")

        if flags:
            notes.append(
                f"H{house_num} lord {lord}: {', '.join(flags)} "
                f"in H{planet.house} -- affects {query_type} outlook."
            )
    return notes
