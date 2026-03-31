"""Birth time rectification — main orchestration and scoring.

KP Ruling Planets and lagna helpers are in rectification_ruling.py.
Event helpers are in rectification_events.py.
Source: BPHS Ch.4, KP system.
"""

from __future__ import annotations

from datetime import timedelta

import swisseph as swe

from daivai_engine.compute.datetime_utils import parse_birth_datetime
from daivai_engine.compute.rectification_events import (
    TATTWA_ELEMENT,
    expected_lords_for_event,
    house_lord,
    verify_events,
)
from daivai_engine.compute.rectification_ruling import (
    _compute_lagna_for_time,
    _nak_index_from_longitude,
    get_ruling_planets,
)
from daivai_engine.constants import (
    NAKSHATRA_LORDS,
    SIGN_ELEMENTS,
    SIGN_LORDS,
    SIGNS_EN,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.rectification import (
    EventVerification,
    LifeEvent,
    RectificationCandidate,
    RectificationResult,
    RulingPlanets,
)


# Re-export for backward compatibility and tests
_house_lord = house_lord
_expected_lords_for_event = expected_lords_for_event
_TATTWA_ELEMENT = TATTWA_ELEMENT


# ── Main rectification ──────────────────────────────────────────────────────


def rectify_birth_time(
    chart: ChartData,
    time_range_minutes: int = 30,
    events: list[LifeEvent] | None = None,
    tattwa: str | None = None,
) -> RectificationResult:
    """Rectify birth time using ruling planets, events, and tattwa.

    Generates candidate birth times every 2 minutes within the given range,
    scores each against the current ruling planets, event verifications,
    and tattwa constraints.

    Args:
        chart: The original birth chart.
        time_range_minutes: Search range in minutes (default +-30).
        events: Optional list of known life events for verification.
        tattwa: Optional tattwa name (agni/prithvi/vayu/jal/akash).

    Returns:
        RectificationResult with ranked candidates and best match.
    """
    now_jd = swe.julday(2026, 3, 23, 12.0)
    ruling = get_ruling_planets(now_jd, chart.latitude, chart.longitude)

    mahadashas: list[DashaPeriod] = []
    event_results: list[EventVerification] = []
    if events:
        from daivai_engine.compute.dasha import compute_mahadashas

        mahadashas = compute_mahadashas(chart)
        event_results = verify_events(chart, events, mahadashas)

    candidates = _generate_candidates(
        chart,
        ruling,
        event_results,
        time_range_minutes,
        events,
        tattwa,
    )

    candidates.sort(key=lambda c: c.total_score, reverse=True)
    best = candidates[0] if candidates else None

    confidence = _assess_confidence(best)

    summary = (
        f"Rectification for {chart.tob} (+-{time_range_minutes}min). "
        f"Best candidate: {best.birth_time if best else 'none'} "
        f"({best.lagna_sign if best else 'n/a'} lagna, "
        f"score={best.total_score if best else 0}). "
        f"Confidence: {confidence}."
    )

    return RectificationResult(
        original_birth_time=chart.tob,
        original_lagna=SIGNS_EN[chart.lagna_sign_index],
        ruling_planets_now=ruling,
        event_verifications=event_results,
        candidates=candidates,
        best_candidate=best,
        confidence=confidence,
        summary=summary,
    )


def _generate_candidates(
    chart: ChartData,
    ruling: RulingPlanets,
    event_results: list[EventVerification],
    time_range_minutes: int,
    events: list[LifeEvent] | None,
    tattwa: str | None,
) -> list[RectificationCandidate]:
    """Generate and score candidate birth times.

    Args:
        chart: The original birth chart.
        ruling: Current ruling planets.
        event_results: Pre-computed event verifications.
        time_range_minutes: Search range in minutes.
        events: Optional life events (for method labelling).
        tattwa: Optional tattwa constraint.

    Returns:
        Unsorted list of scored candidates.
    """
    candidates: list[RectificationCandidate] = []
    step = 2
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    method = _determine_method(events, tattwa)
    evt_matches = sum(1 for ev in event_results if ev.matches)

    for offset in range(-time_range_minutes, time_range_minutes + 1, step):
        sid_asc, sign_idx, deg_in_sign = _compute_lagna_for_time(
            chart.julian_day,
            float(offset),
            chart.latitude,
            chart.longitude,
        )
        rp_matches = _score_ruling_matches(sid_asc, sign_idx, ruling)
        tattwa_score = _score_tattwa(sign_idx, tattwa)
        total = float(rp_matches) + tattwa_score + float(evt_matches)
        candidate_dt = birth_dt + timedelta(minutes=offset)

        candidates.append(
            RectificationCandidate(
                birth_time=candidate_dt.strftime("%H:%M"),
                lagna_sign_index=sign_idx,
                lagna_sign=SIGNS_EN[sign_idx],
                lagna_degree=round(deg_in_sign, 2),
                ruling_planet_matches=rp_matches,
                event_matches=evt_matches,
                total_score=round(total, 2),
                method=method,
            )
        )

    return candidates


def _score_ruling_matches(sid_asc: float, sign_idx: int, ruling: RulingPlanets) -> int:
    """Count how many ruling planets match the candidate lagna."""
    lagna_nak_idx = _nak_index_from_longitude(sid_asc)
    matches = 0
    if SIGN_LORDS[sign_idx] in ruling.unique_rulers:
        matches += 1
    if NAKSHATRA_LORDS[lagna_nak_idx] in ruling.unique_rulers:
        matches += 1
    if ruling.moon_sign_lord in ruling.unique_rulers:
        matches += 1
    if ruling.moon_nak_lord in ruling.unique_rulers:
        matches += 1
    if ruling.day_lord in ruling.unique_rulers:
        matches += 1
    return matches


def _score_tattwa(sign_idx: int, tattwa: str | None) -> float:
    """Score the tattwa match for a candidate lagna sign."""
    if not tattwa:
        return 0.0
    expected_element = TATTWA_ELEMENT.get(tattwa.lower(), "")
    return 2.0 if SIGN_ELEMENTS[sign_idx] == expected_element else 0.0


def _determine_method(events: list[LifeEvent] | None, tattwa: str | None) -> str:
    """Determine rectification method label."""
    if events and tattwa:
        return "combined"
    if events:
        return "event_based"
    if tattwa:
        return "tattwa"
    return "ruling_planets"


def _assess_confidence(best: RectificationCandidate | None) -> str:
    """Assess overall confidence from best candidate score."""
    if best and best.total_score >= 5:
        return "high"
    if best and best.total_score >= 3:
        return "medium"
    return "low"
