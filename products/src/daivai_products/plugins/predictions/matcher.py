"""Dasha-event matching engine — correlate life events to dasha periods.

For each life event, finds the running MD/AD at that date, checks which
houses those lords rule, and scores the match quality against the event
type's expected house significations.

Source: BPHS Ch.25, Phaladeepika Ch.26.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from daivai_engine.compute.chart_utils import get_house_lord
from daivai_engine.compute.dasha import compute_antardashas
from daivai_engine.models.analysis import FullChartAnalysis
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_products.store.events import LifeEvent


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

MatchQuality = Literal["strong", "moderate", "weak"]


class DashaEventMatch(BaseModel):
    """Result of matching a single life event to its dasha period."""

    model_config = ConfigDict(frozen=True)

    event: str
    event_date: str
    event_type: str
    dasha_lord: str
    antardasha_lord: str
    relevant_houses: list[int]
    match_quality: MatchQuality
    explanation: str


# ---------------------------------------------------------------------------
# House signification map — which houses govern which event types
# ---------------------------------------------------------------------------

# Maps event_type (as stored in LifeEvent.event_type) to the house numbers
# that are primary significators for that domain.
_EVENT_HOUSES: dict[str, list[int]] = {
    "marriage": [7, 2],  # 7th = partnerships, 2nd = family
    "career": [10, 6, 2],  # 10th = career, 6th = service, 2nd = income
    "health": [1, 6, 8],  # 1st = body, 6th = disease, 8th = longevity
    "child": [5, 9],  # 5th = children, 9th = fortune
    "education": [4, 5, 9],  # 4th = learning, 5th = intellect, 9th = higher ed
    "property": [4, 2],  # 4th = property/vehicle, 2nd = wealth
    "travel": [3, 9, 12],  # 3rd = short travel, 9th = long travel, 12th = foreign
    "finance": [2, 11, 5],  # 2nd = wealth, 11th = gains, 5th = speculation
    "spirituality": [9, 12, 5],  # 9th = dharma, 12th = moksha, 5th = mantra
    "legal": [6, 7, 8],  # 6th = litigation, 7th = opponent, 8th = obstacles
}

# Natural significator planets for event types (karaka)
_EVENT_KARAKAS: dict[str, list[str]] = {
    "marriage": ["Venus"],
    "career": ["Saturn", "Sun"],
    "health": ["Sun"],
    "child": ["Jupiter"],
    "education": ["Jupiter", "Mercury"],
    "property": ["Mars", "Venus"],
    "travel": ["Rahu", "Moon"],
    "finance": ["Jupiter", "Venus"],
    "spirituality": ["Jupiter", "Ketu"],
    "legal": ["Saturn", "Mars"],
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_houses_owned(chart: ChartData, planet: str) -> list[int]:
    """Get all houses owned (lorded) by a planet in this chart.

    Args:
        chart: Natal chart.
        planet: Planet name.

    Returns:
        List of house numbers (1-12) owned by the planet.
    """
    owned: list[int] = []
    for house in range(1, 13):
        if get_house_lord(chart, house) == planet:
            owned.append(house)
    return owned


def _find_dasha_at_date(
    mahadashas: list[DashaPeriod],
    target_dt: datetime,
) -> tuple[str, str]:
    """Find the MD and AD lord active at a given date.

    Args:
        mahadashas: List of Mahadasha periods.
        target_dt: The date to check.

    Returns:
        Tuple of (mahadasha_lord, antardasha_lord).
    """
    for md in mahadashas:
        if md.start <= target_dt <= md.end:
            antardashas = compute_antardashas(md)
            for ad in antardashas:
                if ad.start <= target_dt <= ad.end:
                    return md.lord, ad.lord
            return md.lord, md.lord
    if mahadashas:
        return mahadashas[-1].lord, mahadashas[-1].lord
    return "Unknown", "Unknown"


def _parse_event_date(date_str: str) -> datetime | None:
    """Parse event date string to datetime. Supports YYYY-MM-DD and DD/MM/YYYY.

    Args:
        date_str: Date string.

    Returns:
        Parsed datetime at noon, or None if unparseable.
    """
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m"):
        try:
            dt = datetime.strptime(date_str, fmt)
            # Normalize to noon to avoid boundary issues
            return dt.replace(hour=12, minute=0, second=0)
        except ValueError:
            continue
    return None


def _compute_overlap(owned_houses: list[int], expected_houses: list[int]) -> int:
    """Count how many of the dasha lord's houses match the expected event houses.

    Args:
        owned_houses: Houses owned by a dasha lord.
        expected_houses: Houses expected for the event type.

    Returns:
        Number of overlapping houses.
    """
    return len(set(owned_houses) & set(expected_houses))


def _score_match(
    chart: ChartData,
    md_lord: str,
    ad_lord: str,
    event_type: str,
) -> tuple[MatchQuality, list[int], str]:
    """Score the match quality of dasha lords for an event type.

    Scoring logic:
    - strong: MD or AD lord owns 2+ relevant houses, OR MD lord owns 1 AND is
      natural karaka for the event
    - moderate: MD or AD lord owns 1 relevant house, OR AD lord is karaka
    - weak: no house overlap but lord is placed in or aspects a relevant house,
      or no correlation found

    Args:
        chart: Natal chart data.
        md_lord: Mahadasha lord planet name.
        ad_lord: Antardasha lord planet name.
        event_type: Category of the life event.

    Returns:
        Tuple of (quality, relevant_houses, explanation).
    """
    expected = _EVENT_HOUSES.get(event_type, [])
    karakas = _EVENT_KARAKAS.get(event_type, [])

    md_houses = _get_houses_owned(chart, md_lord)
    ad_houses = _get_houses_owned(chart, ad_lord)

    md_overlap = _compute_overlap(md_houses, expected)
    ad_overlap = _compute_overlap(ad_houses, expected)
    total_overlap = md_overlap + ad_overlap

    relevant = sorted(set(md_houses + ad_houses) & set(expected))

    # Build explanation parts
    parts: list[str] = []

    if md_overlap > 0:
        matched = sorted(set(md_houses) & set(expected))
        parts.append(f"MD lord {md_lord} rules house(s) {matched}")
    if ad_overlap > 0:
        matched = sorted(set(ad_houses) & set(expected))
        parts.append(f"AD lord {ad_lord} rules house(s) {matched}")

    md_is_karaka = md_lord in karakas
    ad_is_karaka = ad_lord in karakas

    if md_is_karaka:
        parts.append(f"{md_lord} is natural karaka for {event_type}")
    if ad_is_karaka:
        parts.append(f"{ad_lord} is natural karaka for {event_type}")

    # Determine quality
    if total_overlap >= 2 or (md_overlap >= 1 and md_is_karaka):
        quality: MatchQuality = "strong"
    elif total_overlap >= 1 or ad_is_karaka or md_is_karaka:
        quality = "moderate"
    else:
        quality = "weak"
        if not parts:
            parts.append(
                f"No direct house overlap between {md_lord}/{ad_lord} "
                f"and expected houses {expected} for {event_type}"
            )

    explanation = "; ".join(parts) if parts else "No significant correlation found"
    return quality, relevant, explanation


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def match_events_to_dashas(
    analysis: FullChartAnalysis,
    events: list[LifeEvent],
) -> list[DashaEventMatch]:
    """Match life events to their corresponding dasha periods.

    For each event:
    1. Find which MD/AD was running on that date
    2. Check if the dasha lord rules houses relevant to that event type
    3. Score the match quality based on house ownership and significations

    Args:
        analysis: Full pre-computed chart analysis containing mahadashas.
        events: List of life events with dates and types.

    Returns:
        List of DashaEventMatch results, one per successfully parsed event.
    """
    if not events:
        return []

    mahadashas = analysis.mahadashas
    chart = analysis.chart
    results: list[DashaEventMatch] = []

    for event in events:
        event_dt = _parse_event_date(event.event_date)
        if event_dt is None:
            continue

        # Make event_dt timezone-aware if mahadashas are timezone-aware
        if mahadashas and mahadashas[0].start.tzinfo is not None:
            event_dt = event_dt.replace(tzinfo=mahadashas[0].start.tzinfo)

        md_lord, ad_lord = _find_dasha_at_date(mahadashas, event_dt)

        if md_lord == "Unknown":
            continue

        event_type = event.event_type or "career"
        quality, relevant, explanation = _score_match(
            chart,
            md_lord,
            ad_lord,
            event_type,
        )

        results.append(
            DashaEventMatch(
                event=event.description or event.event_type,
                event_date=event.event_date,
                event_type=event_type,
                dasha_lord=md_lord,
                antardasha_lord=ad_lord,
                relevant_houses=relevant,
                match_quality=quality,
                explanation=explanation,
            )
        )

    return results
