"""Yoga activation timing — maps natal yogas to their fructification dashas.

A yoga is a promise in the natal chart. It delivers results during the
Vimshottari dasha of the planets that form it. This module identifies
all activation windows across the 120-year dasha timeline.

Source: BPHS Ch.25, Phaladeepika Ch.20.
"""

from __future__ import annotations

from datetime import datetime

from daivai_engine.compute.dasha import (
    compute_antardashas,
    compute_mahadashas,
    find_current_dasha,
)
from daivai_engine.compute.datetime_utils import now_ist
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.compute.yoga_timing_helpers import (
    build_all_summary,
    build_yoga_summary,
    check_current_activation,
    find_most_significant,
    find_next_activation,
    yoga_sort_key,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.yoga import YogaResult
from daivai_engine.models.yoga_timing import (
    AllYogaTimings,
    YogaActivationPeriod,
    YogaTimingResult,
)


def compute_yoga_timing(
    chart: ChartData,
    yoga: YogaResult,
    mahadashas: list[DashaPeriod],
    current_md: DashaPeriod,
    current_ad: DashaPeriod,
    now: datetime,
) -> YogaTimingResult:
    """Compute activation timing for a single yoga.

    Scans the full Mahadasha timeline to find every period where a
    forming planet is the MD or AD lord. Dual activation (both MD
    and AD are forming planets) is the strongest trigger.

    Source: BPHS Ch.25 — dasha lords deliver yoga results when they are
    forming planets. Phaladeepika Ch.20.

    Args:
        chart: Natal birth chart.
        yoga: Detected yoga result with planets_involved.
        mahadashas: Full list of 9 Mahadasha periods from birth.
        current_md: Currently running Mahadasha.
        current_ad: Currently running Antardasha.
        now: Current datetime for is_currently_active check.

    Returns:
        YogaTimingResult with all activation windows and current status.
    """
    yoga_planets = set(yoga.planets_involved)
    activation_periods: list[YogaActivationPeriod] = []

    # Scan all MDs and their ADs for yoga planet matches
    for md in mahadashas:
        md_is_yoga_planet = md.lord in yoga_planets
        ads = compute_antardashas(md)

        for ad in ads:
            ad_is_yoga_planet = ad.lord in yoga_planets

            if md_is_yoga_planet and ad_is_yoga_planet and md.lord != ad.lord:
                activation_periods.append(
                    YogaActivationPeriod(
                        dasha_level="MD-AD",
                        lord=f"{md.lord}-{ad.lord}",
                        parent_lord=md.lord,
                        start=ad.start,
                        end=ad.end,
                        activation_strength="dual",
                    )
                )
            elif md_is_yoga_planet and not ad_is_yoga_planet:
                activation_periods.append(
                    YogaActivationPeriod(
                        dasha_level="MD",
                        lord=md.lord,
                        parent_lord=None,
                        start=ad.start,
                        end=ad.end,
                        activation_strength="primary",
                    )
                )
            elif ad_is_yoga_planet and not md_is_yoga_planet:
                activation_periods.append(
                    YogaActivationPeriod(
                        dasha_level="AD",
                        lord=ad.lord,
                        parent_lord=md.lord,
                        start=ad.start,
                        end=ad.end,
                        activation_strength="secondary",
                    )
                )

    # Total activation years
    total_days = sum((ap.end - ap.start).total_seconds() / 86400.0 for ap in activation_periods)
    total_years = round(total_days / 365.25, 2)

    # Current activation status
    is_active, current_strength = check_current_activation(
        yoga_planets,
        current_md,
        current_ad,
        now,
    )

    # Next future activation
    next_act = find_next_activation(activation_periods, now)

    # Summary
    summary = build_yoga_summary(yoga, is_active, current_strength, next_act, total_years)

    return YogaTimingResult(
        yoga_name=yoga.name,
        planets_involved=yoga.planets_involved,
        houses_involved=yoga.houses_involved,
        effect=yoga.effect,
        strength=yoga.strength,
        activation_periods=activation_periods,
        total_activation_years=total_years,
        is_currently_active=is_active,
        current_activation_strength=current_strength,
        next_activation=next_act,
        summary=summary,
    )


def compute_all_yoga_timings(
    chart: ChartData,
    target_date: datetime | None = None,
) -> AllYogaTimings:
    """Compute timing analysis for all detected yogas in a chart.

    Detects all yogas, computes Mahadashas, then finds activation windows
    for every present yoga. Results sorted by significance.

    Source: BPHS Ch.25, Phaladeepika Ch.20.

    Args:
        chart: Natal birth chart.
        target_date: Reference date for current/next activation.
            Defaults to current IST time.

    Returns:
        AllYogaTimings with individual results and aggregate summaries.
    """
    if target_date is None:
        target_date = now_ist()

    # Detect all yogas
    all_yogas = detect_all_yogas(chart)
    present_yogas = [y for y in all_yogas if y.is_present]

    # Compute full dasha timeline
    mahadashas = compute_mahadashas(chart)
    current_md, current_ad, _ = find_current_dasha(chart, target_date)

    # Compute timing for each present yoga
    results: list[YogaTimingResult] = []
    for yoga in present_yogas:
        timing = compute_yoga_timing(
            chart,
            yoga,
            mahadashas,
            current_md,
            current_ad,
            target_date,
        )
        results.append(timing)

    # Sort by significance
    results.sort(key=yoga_sort_key, reverse=True)

    # Aggregate data
    active_names = [r.yoga_name for r in results if r.is_currently_active]

    upcoming: list[tuple[str, str]] = []
    for r in results:
        if r.next_activation is not None:
            desc = (
                f"{r.next_activation.lord} "
                f"({r.next_activation.start.strftime('%d/%m/%Y')} - "
                f"{r.next_activation.end.strftime('%d/%m/%Y')})"
            )
            upcoming.append((r.yoga_name, desc))

    most_sig = find_most_significant(results)
    summary = build_all_summary(results, active_names, upcoming)

    return AllYogaTimings(
        yogas=results,
        currently_active_yogas=active_names,
        upcoming_activations=upcoming,
        most_significant=most_sig,
        summary=summary,
    )
