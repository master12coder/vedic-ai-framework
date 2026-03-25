"""Synchronised dasha timeline for multiple family members.

Aligns Vimshottari Mahadasha / Antardasha timelines across charts and
identifies overlapping favourable or challenging windows.  Used in Family
Bond Kundali for coordinated planning (investments, career moves, health
caution periods).

Source: Vimshottari dasha periods + functional nature classification.
"""

from __future__ import annotations

from datetime import datetime

from daivai_engine.compute.dasha import compute_antardashas, compute_mahadashas
from daivai_engine.compute.datetime_utils import now_ist
from daivai_engine.compute.functional_nature import get_functional_nature
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.family_bond import DashaSyncEntry, DashaSyncResult


_FAVORABLE = {"benefic", "yogakaraka"}
_CHALLENGING = {"malefic", "maraka"}


def compute_dasha_sync(
    charts: list[ChartData],
    ref_date: datetime | None = None,
) -> DashaSyncResult:
    """Compute synchronised dasha state for all family members.

    For each member, finds the current Mahadasha and Antardasha at *ref_date*
    (defaults to now), classifies each dasha lord's functional nature, and
    identifies windows where multiple members are simultaneously in favourable
    or challenging dashas.

    Args:
        charts: List of computed birth charts.
        ref_date: Reference date/time (defaults to ``datetime.now()``).

    Returns:
        DashaSyncResult with per-member dasha state and window analysis.
    """
    now = ref_date or now_ist()

    entries: list[DashaSyncEntry] = []
    for chart in charts:
        entry = _build_entry(chart, now)
        if entry is not None:
            entries.append(entry)

    favorable_windows = _find_favorable_windows(entries)
    challenging_windows = _find_challenging_windows(entries)
    summary = _build_summary(entries, favorable_windows, challenging_windows)

    return DashaSyncResult(
        entries=entries,
        favorable_windows=favorable_windows,
        challenging_windows=challenging_windows,
        summary=summary,
    )


def _build_entry(chart: ChartData, now: datetime) -> DashaSyncEntry | None:
    """Build a DashaSyncEntry for one chart at a given time."""
    mahadashas = compute_mahadashas(chart)
    current_md = _find_period(mahadashas, now)
    if current_md is None:
        return None

    # Find current antardasha within the mahadasha
    antardashas = compute_antardashas(current_md)
    current_ad = _find_period(antardashas, now)
    ad_lord = current_ad.lord if current_ad else None

    md_nature = get_functional_nature(current_md.lord, chart.lagna_sign)

    return DashaSyncEntry(
        name=chart.name,
        current_md_lord=current_md.lord,
        current_ad_lord=ad_lord,
        md_nature=md_nature,
        md_start=current_md.start,
        md_end=current_md.end,
    )


def _find_period(periods: list[DashaPeriod], now: datetime) -> DashaPeriod | None:
    """Find the period that contains *now*."""
    for p in periods:
        if p.start <= now <= p.end:
            return p
    return periods[-1] if periods else None


def _find_favorable_windows(entries: list[DashaSyncEntry]) -> list[str]:
    """Identify when multiple members are in benefic/yogakaraka dashas."""
    favorable = [e for e in entries if e.md_nature.classification in _FAVORABLE]
    if len(favorable) >= 2:
        names = ", ".join(e.name for e in favorable)
        return [f"Current: {names} are in favourable Mahadashas — family growth window."]
    return []


def _find_challenging_windows(entries: list[DashaSyncEntry]) -> list[str]:
    """Identify when multiple members are in malefic/maraka dashas."""
    challenging = [e for e in entries if e.md_nature.classification in _CHALLENGING]
    if len(challenging) >= 2:
        names = ", ".join(e.name for e in challenging)
        return [f"Current: {names} are in challenging Mahadashas — exercise caution."]
    return []


def _build_summary(
    entries: list[DashaSyncEntry],
    favorable: list[str],
    challenging: list[str],
) -> str:
    """Build a one-paragraph summary."""
    parts = [f"Dasha sync for {len(entries)} members."]
    for e in entries:
        ad_str = f"/{e.current_ad_lord} AD" if e.current_ad_lord else ""
        parts.append(f"{e.name}: {e.current_md_lord} MD{ad_str} ({e.md_nature.classification}).")
    if favorable:
        parts.append(favorable[0])
    if challenging:
        parts.append(challenging[0])
    return " ".join(parts)
