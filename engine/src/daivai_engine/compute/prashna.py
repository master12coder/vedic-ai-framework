"""Prashna Kundli (Horary Chart) — chart for the moment of a question.

No birth data needed — computes chart for question time and place.
Classical analysis follows Prashna Marga and Prasna Tantra:
  1. Lagna lord strength (kendra/trikona position)
  2. Relevant house lord analysis
  3. Moon's condition (waxing, strong, with benefics)
  4. Arudha of the queried house (worldly image of the matter)
  5. Hora lord at question time
  6. Mook Prashna flag (silent query — Moon strength carries extra weight)
  7. Swara analysis (breath-based directional indicator)

Source: Prashna Marga, Prashna Tantra, Tajaka methods.
"""

from __future__ import annotations

from datetime import UTC, datetime

from daivai_engine.compute.ashtamangala_prashna import analyze_ashtamangala
from daivai_engine.compute.chart import compute_chart
from daivai_engine.compute.prashna_helpers import (
    _QUESTION_HOUSES,
    _compute_arudha,
    _compute_hora_lord,
    _compute_swara,
    _is_moon_waxing,
    build_reasoning,
)
from daivai_engine.constants import KENDRAS, SIGN_LORDS, SIGNS, TRIKONAS


__all__ = ["compute_prashna"]


def compute_prashna(
    question: str,
    lat: float,
    lon: float,
    tz_name: str = "Asia/Kolkata",
    question_time: datetime | None = None,
    question_type: str = "general",
    is_mook_prashna: bool = False,
    use_ashtamangala: bool = False,
) -> dict:
    """Compute a Prashna (horary) chart and derive a verdict.

    Args:
        question: The question being asked.
        lat: Latitude of the place where question is asked.
        lon: Longitude of the place.
        tz_name: Timezone name.
        question_time: Exact time of question. Defaults to now.
        question_type: Category (marriage, career, etc.) for house selection.
        is_mook_prashna: True if querent did not speak (Moon analysis is primary).
        use_ashtamangala: If True, includes Kerala Ashtamangala analysis.

    Returns:
        Dict with chart, answer, reasoning, arudha, hora_lord, swara, and key factors.
        If use_ashtamangala=True, also includes "ashtamangala" key.
    """
    if question_time is None:
        question_time = datetime.now(tz=UTC)

    # Compute chart for question moment
    dob = question_time.strftime("%d/%m/%Y")
    tob = question_time.strftime("%H:%M")
    chart = compute_chart(
        name="Prashna",
        dob=dob,
        tob=tob,
        lat=lat,
        lon=lon,
        tz_name=tz_name,
        gender="Male",
    )

    # Core analysis
    relevant_house = _QUESTION_HOUSES.get(question_type, 1)
    lagna_lord = SIGN_LORDS[chart.lagna_sign_index]
    relevant_lord = SIGN_LORDS[(chart.lagna_sign_index + relevant_house - 1) % 12]
    moon = chart.planets["Moon"]

    # Lagna lord analysis
    ll_planet = chart.planets.get(lagna_lord)
    ll_strong = ll_planet is not None and ll_planet.house in KENDRAS + TRIKONAS[1:]
    ll_in_dusthana = ll_planet is not None and ll_planet.house in (6, 8, 12)

    # Relevant house lord analysis
    rl_planet = chart.planets.get(relevant_lord)
    rl_strong = rl_planet is not None and rl_planet.house in KENDRAS + TRIKONAS[1:]
    rl_in_dusthana = rl_planet is not None and rl_planet.house in (6, 8, 12)
    rl_combust = rl_planet is not None and rl_planet.is_combust

    # Moon analysis
    moon_strong = moon.house in KENDRAS + TRIKONAS[1:]
    moon_waxing = _is_moon_waxing(moon.longitude, chart.planets["Sun"].longitude)
    moon_dignified = moon.dignity in ("exalted", "own", "mooltrikona")

    # Arudha of the relevant house (worldly image of the matter) — Prashna Marga
    arudha_sign = _compute_arudha(chart, relevant_house)
    arudha_lord = SIGN_LORDS[arudha_sign]
    arudha_lord_planet = chart.planets.get(arudha_lord)
    arudha_strong = (
        arudha_lord_planet is not None and arudha_lord_planet.house in KENDRAS + TRIKONAS[1:]
    )

    # Hora lord at question time
    hora_lord = _compute_hora_lord(question_time)

    # Swara (breath) indicator — Prashna Marga Ch.5
    swara = _compute_swara(question_time)

    # Verdict computation
    positive = 0
    negative = 0

    # Primary factors
    if ll_strong:
        positive += 2
    elif ll_in_dusthana:
        negative += 2
    else:
        negative += 1

    if rl_strong:
        positive += 2
    elif rl_in_dusthana or rl_combust:
        negative += 2

    if moon_strong:
        positive += 1
    if moon_waxing:
        positive += 1
    if moon_dignified:
        positive += 1
    if not moon_strong and not moon_waxing:
        negative += 1

    if arudha_strong:
        positive += 1

    # Hora lord positively aspecting relevant house adds weight
    if hora_lord in (lagna_lord, relevant_lord):
        positive += 1

    # Mook prashna: Moon position is primary when querent is silent
    if is_mook_prashna:
        if moon_strong and moon_waxing:
            positive += 1
        else:
            negative += 1

    # Derive answer
    if positive >= 5:
        answer = "YES"
    elif negative >= 5:
        answer = "NO"
    elif positive > negative:
        answer = "YES"
    elif negative > positive:
        answer = "NO"
    else:
        answer = "MAYBE"

    reasoning = build_reasoning(
        lagna_lord=lagna_lord,
        ll_strong=ll_strong,
        ll_in_dusthana=ll_in_dusthana,
        relevant_lord=relevant_lord,
        rl_strong=rl_strong,
        rl_in_dusthana=rl_in_dusthana,
        rl_combust=rl_combust,
        moon_strong=moon_strong,
        moon_waxing=moon_waxing,
        moon_dignified=moon_dignified,
        arudha_sign=arudha_sign,
        arudha_strong=arudha_strong,
        hora_lord=hora_lord,
        swara=swara,
        house=relevant_house,
        qtype=question_type,
        is_mook=is_mook_prashna,
    )

    return {
        "question": question,
        "question_time": question_time.isoformat(),
        "chart": chart,
        "answer": answer,
        "reasoning": reasoning,
        # Core factors
        "lagna_lord": lagna_lord,
        "relevant_house": relevant_house,
        "relevant_lord": relevant_lord,
        "moon_strong": moon_strong,
        "moon_waxing": moon_waxing,
        # Arudha (worldly image of the matter)
        "arudha_sign": arudha_sign,
        "arudha_sign_name": SIGNS[arudha_sign],
        "arudha_lord": arudha_lord,
        "arudha_strong": arudha_strong,
        # Hora analysis
        "hora_lord": hora_lord,
        # Swara (breath) direction
        "swara": swara,
        # Mook flag
        "is_mook_prashna": is_mook_prashna,
        # Score breakdown
        "positive_factors": positive,
        "negative_factors": negative,
        # Kerala Ashtamangala analysis (optional)
        "ashtamangala": (analyze_ashtamangala(chart, question_type) if use_ashtamangala else None),
    }
