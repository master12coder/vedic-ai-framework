"""Event-based verification helpers for birth time rectification.

Checks whether running dasha/antardasha lords match the expected
significators for known life events (marriage, career, children, etc.).

Source: BPHS Ch.4, KP system.
"""

from __future__ import annotations

from datetime import datetime

from daivai_engine.constants import SIGN_LORDS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.rectification import (
    EventVerification,
    LifeEvent,
)


# Expected house offsets (0-indexed from lagna) for each event type.
# The house lord at (lagna_sign_index + offset) % 12 should be the dasha lord.
_EVENT_EXPECTED_LORDS: dict[str, list[int]] = {
    "marriage": [6],  # 7th house offset
    "first_child": [4],  # 5th house offset
    "career_start": [9],  # 10th house offset
    "parent_death": [8],  # 9th house offset
}

# Tattwa to zodiac element mapping
TATTWA_ELEMENT: dict[str, str] = {
    "agni": "Fire",
    "prithvi": "Earth",
    "vayu": "Air",
    "jal": "Water",
    "akash": "Air",  # Akash maps to Air signs
}


def house_lord(chart: ChartData, house_num: int) -> str:
    """Return the lord of a given house (1-12) in the chart.

    Args:
        chart: The birth chart.
        house_num: House number (1-12).

    Returns:
        Planet name that lords over the house.
    """
    sign_idx = (chart.lagna_sign_index + house_num - 1) % 12
    return SIGN_LORDS[sign_idx]


def expected_lords_for_event(chart: ChartData, event_type: str) -> list[str]:
    """Return the expected dasha/antardasha lords for a given event type.

    Args:
        chart: The birth chart.
        event_type: One of 'marriage', 'first_child', 'career_start', 'parent_death'.

    Returns:
        List of planet names expected to be active during such an event.
    """
    house_offsets = _EVENT_EXPECTED_LORDS.get(event_type, [])
    lords: list[str] = []
    for offset in house_offsets:
        lords.append(house_lord(chart, offset + 1))

    # Add natural significators
    if event_type == "marriage":
        lords.append("Venus")
    elif event_type == "first_child":
        lords.append("Jupiter")
    elif event_type == "career_start":
        lords.append(house_lord(chart, 10))
    elif event_type == "parent_death":
        lords.append("Sun")

    return list(set(lords))


def find_dasha_at_date(
    mahadashas: list[DashaPeriod],
    target_dt: datetime,
) -> tuple[str, str]:
    """Find the Mahadasha and Antardasha lord active at a given date.

    Args:
        mahadashas: List of Mahadasha periods.
        target_dt: The date to check.

    Returns:
        Tuple of (mahadasha_lord, antardasha_lord).
    """
    from daivai_engine.compute.dasha import compute_antardashas

    for md in mahadashas:
        if md.start <= target_dt <= md.end:
            antardashas = compute_antardashas(md)
            for ad in antardashas:
                if ad.start <= target_dt <= ad.end:
                    return md.lord, ad.lord
            return md.lord, md.lord
    # Fallback: return the last mahadasha lord
    if mahadashas:
        return mahadashas[-1].lord, mahadashas[-1].lord
    return "Unknown", "Unknown"


def verify_events(
    chart: ChartData,
    events: list[LifeEvent],
    mahadashas: list[DashaPeriod],
) -> list[EventVerification]:
    """Verify life events against dasha periods.

    For each event, checks whether the running dasha/antardasha lord matches
    the expected significator for that event type.

    Args:
        chart: The birth chart.
        events: List of known life events with dates.
        mahadashas: Computed Mahadasha periods.

    Returns:
        List of EventVerification results.
    """
    results: list[EventVerification] = []

    for event in events:
        # Parse event date
        day_s, month_s, year_s = event.date.split("/")
        try:
            from zoneinfo import ZoneInfo

            event_dt = datetime(
                int(year_s),
                int(month_s),
                int(day_s),
                12,
                0,
                tzinfo=ZoneInfo(chart.timezone_name),
            )
        except Exception:
            event_dt = datetime(int(year_s), int(month_s), int(day_s), 12, 0)

        md_lord, ad_lord = find_dasha_at_date(mahadashas, event_dt)
        expected = expected_lords_for_event(chart, event.event_type)

        matches = md_lord in expected or ad_lord in expected

        if md_lord in expected and ad_lord in expected:
            confidence = "high"
        elif matches:
            confidence = "medium"
        else:
            confidence = "low"

        results.append(
            EventVerification(
                event=event,
                dasha_lord_at_event=md_lord,
                antardasha_lord_at_event=ad_lord,
                expected_lords=expected,
                matches=matches,
                confidence=confidence,
            )
        )

    return results
