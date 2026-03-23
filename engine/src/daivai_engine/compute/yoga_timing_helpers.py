"""Yoga timing helper functions — sorting, summary building, activation checks.

Internal helpers for yoga_timing.py. Not part of the public API.

Source: BPHS Ch.25, Phaladeepika Ch.20.
"""

from __future__ import annotations

from datetime import datetime

from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.yoga import YogaResult
from daivai_engine.models.yoga_timing import (
    YogaActivationPeriod,
    YogaTimingResult,
)


def check_current_activation(
    yoga_planets: set[str],
    current_md: DashaPeriod,
    current_ad: DashaPeriod,
    now: datetime,
) -> tuple[bool, str | None]:
    """Check if a yoga is currently active based on running dasha.

    Args:
        yoga_planets: Set of planet names forming the yoga.
        current_md: Currently running Mahadasha.
        current_ad: Currently running Antardasha.
        now: Current datetime.

    Returns:
        (is_active, activation_strength): strength is "dual"/"primary"/"secondary"/None.
    """
    if not (current_md.start <= now <= current_md.end):
        return False, None

    md_match = current_md.lord in yoga_planets
    ad_match = current_ad.lord in yoga_planets

    if md_match and ad_match and current_md.lord != current_ad.lord:
        return True, "dual"
    if md_match:
        return True, "primary"
    if ad_match:
        return True, "secondary"
    return False, None


def find_next_activation(
    periods: list[YogaActivationPeriod],
    now: datetime,
) -> YogaActivationPeriod | None:
    """Find the next future activation period after now.

    Prioritizes dual activation, then primary, then secondary.

    Args:
        periods: All activation periods for a yoga.
        now: Current datetime.

    Returns:
        Next future activation period, or None if none exist.
    """
    future = [p for p in periods if p.start > now]
    if not future:
        return None

    # Sort by strength priority then by start date
    strength_order = {"dual": 0, "primary": 1, "secondary": 2}
    future.sort(
        key=lambda p: (strength_order.get(p.activation_strength, 3), p.start),
    )
    return future[0]


def yoga_sort_key(result: YogaTimingResult) -> tuple[int, int, float]:
    """Sort key for yoga results — higher = more significant.

    Priority: currently_active > effect > total_activation_years.

    Args:
        result: Yoga timing result.

    Returns:
        Sort tuple (active_score, effect_score, years).
    """
    active_score = 1 if result.is_currently_active else 0
    effect_map = {"benefic": 2, "mixed": 1, "malefic": 0}
    effect_score = effect_map.get(result.effect, 1)
    return (active_score, effect_score, result.total_activation_years)


def find_most_significant(
    results: list[YogaTimingResult],
) -> YogaTimingResult | None:
    """Find the most significant yoga with an upcoming activation.

    Selects the strongest present benefic yoga that has a future
    activation window.

    Args:
        results: Sorted list of yoga timing results.

    Returns:
        Most significant result, or None.
    """
    for r in results:
        if r.strength != "cancelled" and r.next_activation is not None:
            return r
    # Fallback: any result with activation periods
    for r in results:
        if r.activation_periods:
            return r
    return None


def build_yoga_summary(
    yoga: YogaResult,
    is_active: bool,
    strength: str | None,
    next_act: YogaActivationPeriod | None,
    total_years: float,
) -> str:
    """Build summary for a single yoga timing result.

    Args:
        yoga: The detected yoga.
        is_active: Whether yoga is currently active.
        strength: Current activation strength.
        next_act: Next future activation.
        total_years: Total activation years.

    Returns:
        Summary string.
    """
    parts: list[str] = [f"{yoga.name} ({yoga.effect}, {yoga.strength})"]

    if is_active:
        parts.append(f"ACTIVE NOW ({strength})")
    elif next_act:
        parts.append(f"Next: {next_act.lord} ({next_act.start.strftime('%d/%m/%Y')})")
    else:
        parts.append("No future activation in dasha timeline")

    parts.append(f"Total activation: {total_years} years")
    return " | ".join(parts)


def build_all_summary(
    results: list[YogaTimingResult],
    active_names: list[str],
    upcoming: list[tuple[str, str]],
) -> str:
    """Build aggregate summary for all yoga timings.

    Args:
        results: All yoga timing results.
        active_names: Names of currently active yogas.
        upcoming: List of (yoga_name, period_description) tuples.

    Returns:
        Aggregate summary string.
    """
    parts: list[str] = [f"{len(results)} yogas analyzed"]

    if active_names:
        parts.append(f"Active now: {', '.join(active_names)}")
    else:
        parts.append("No yogas currently active via dasha")

    if upcoming:
        top = upcoming[:3]
        upcoming_str = "; ".join(f"{n}: {d}" for n, d in top)
        parts.append(f"Upcoming: {upcoming_str}")

    return " | ".join(parts)
