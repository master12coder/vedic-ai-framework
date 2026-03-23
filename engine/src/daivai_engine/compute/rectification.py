"""Birth time rectification — KP Ruling Planets, events, and Tattwa.

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
from daivai_engine.constants import (
    DAY_PLANET,
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN_DEG,
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


# ── KP Ruling Planets ───────────────────────────────────────────────────────


def _nak_index_from_longitude(lon: float) -> int:
    """Return nakshatra index (0-26) from sidereal longitude."""
    return int(lon / NAKSHATRA_SPAN_DEG) % 27


def _weekday_lord(jd: float) -> str:
    """Return the day lord for a given Julian Day.

    swe.day_of_week returns: 0=Mon, 1=Tue, ..., 6=Sun.
    DAY_PLANET uses: 0=Sun, 1=Mon, 2=Tue, ...
    """
    dow = swe.day_of_week(jd)  # 0=Mon, 6=Sun
    day_idx = (dow + 1) % 7  # Convert: Mon(0)->1, Sun(6)->0
    return DAY_PLANET.get(day_idx, "Sun")


def get_ruling_planets(jd: float, lat: float, lon: float) -> RulingPlanets:
    """Compute the 5 KP ruling planets for a given moment.

    The five rulers are:
    1. Moon's nakshatra lord
    2. Moon's sign lord
    3. Lagna's nakshatra lord
    4. Lagna's sign lord
    5. Day lord

    Args:
        jd: Julian Day (UT).
        lat: Geographic latitude.
        lon: Geographic longitude.

    Returns:
        RulingPlanets with all 5 rulers and deduplicated list.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd)

    # Moon position
    moon_result = swe.calc_ut(jd, swe.MOON)
    moon_trop = moon_result[0][0]
    moon_sid = (moon_trop - ayanamsha) % FULL_CIRCLE_DEG
    moon_sign_idx = int(moon_sid / DEGREES_PER_SIGN)
    moon_nak_idx = _nak_index_from_longitude(moon_sid)

    moon_nak_lord = NAKSHATRA_LORDS[moon_nak_idx]
    moon_sign_lord = SIGN_LORDS[moon_sign_idx]

    # Lagna position
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    lagna_sid = (ascmc[0] - ayanamsha) % FULL_CIRCLE_DEG
    lagna_sign_idx = int(lagna_sid / DEGREES_PER_SIGN)
    lagna_nak_idx = _nak_index_from_longitude(lagna_sid)

    lagna_nak_lord = NAKSHATRA_LORDS[lagna_nak_idx]
    lagna_sign_lord = SIGN_LORDS[lagna_sign_idx]

    # Day lord
    day_lord = _weekday_lord(jd)

    # Deduplicated unique rulers (preserving order of first appearance)
    all_five = [moon_nak_lord, moon_sign_lord, lagna_nak_lord, lagna_sign_lord, day_lord]
    seen: set[str] = set()
    unique: list[str] = []
    for r in all_five:
        if r not in seen:
            seen.add(r)
            unique.append(r)

    return RulingPlanets(
        moon_nak_lord=moon_nak_lord,
        moon_sign_lord=moon_sign_lord,
        lagna_nak_lord=lagna_nak_lord,
        lagna_sign_lord=lagna_sign_lord,
        day_lord=day_lord,
        unique_rulers=unique,
    )


# ── Lagna computation ───────────────────────────────────────────────────────


def _compute_lagna_for_time(
    base_jd: float,
    time_offset_minutes: float,
    lat: float,
    lon: float,
) -> tuple[float, int, float]:
    """Compute sidereal lagna for an offset from base JD.

    Args:
        base_jd: Base Julian Day.
        time_offset_minutes: Offset in minutes from base.
        lat: Geographic latitude.
        lon: Geographic longitude.

    Returns:
        Tuple of (sidereal_asc_longitude, sign_index, degree_in_sign).
    """
    jd = base_jd + time_offset_minutes / 1440.0
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa_ut(jd)
    _cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P")
    sid_asc = (ascmc[0] - ayanamsha) % FULL_CIRCLE_DEG
    sign_idx = int(sid_asc / DEGREES_PER_SIGN)
    deg_in_sign = sid_asc % DEGREES_PER_SIGN
    return sid_asc, sign_idx, deg_in_sign


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
