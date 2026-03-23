"""Gochara (Transit Analysis) — unified computation with Vedha and Moorthy Nirnaya.

Implements Phaladeepika Ch.26 transit analysis:
  1. Gochara: planet-in-house-from-Moon result (YAML-driven)
  2. Vedha: obstruction check — natal planet in vedha house blocks benefit
  3. Ashtakavarga: BAV bindu count modifies final score
  4. Moorthy Nirnaya: Poorna/Madhya/Swalpa/Nishphala from bindus
  5. Special phenomena: Sade Sati, Kantak Shani, Ashtama Shani, etc.
  6. Double transit: houses where both Jupiter and Saturn are active

Source: Phaladeepika Ch.26, BPHS transit chapter.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.datetime_utils import now_ist
from daivai_engine.compute.transit import compute_transits
from daivai_engine.compute.vedha import check_vedha
from daivai_engine.constants import SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.gochara import (
    Favorability,
    GocharaAnalysis,
    GocharaPlanetResult,
    GocharaVedha,
    MoorthyClass,
)


# ── YAML data ─────────────────────────────────────────────────────────────────

_DATA_FILE = Path(__file__).parent.parent / "knowledge" / "gochara_rules.yaml"
_DATA: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    """Load and cache the Gochara YAML rules."""
    global _DATA
    if _DATA is None:
        with open(_DATA_FILE) as f:
            _DATA = yaml.safe_load(f)
    return _DATA


# ── BAV modifier table ────────────────────────────────────────────────────────

# Bindu count → score modifier (Ashtakavarga contribution)
_BINDU_TO_MOD: list[tuple[range, int]] = [
    (range(0, 2), -2),  # 0-1 bindus: very unfavorable
    (range(2, 4), -1),  # 2-3 bindus: unfavorable
    (range(4, 5), 0),  # 4 bindus:   neutral
    (range(5, 7), +1),  # 5-6 bindus: favorable
    (range(7, 9), +2),  # 7-8 bindus: very favorable
]

# Sade Sati: Saturn in 12th/1st/2nd from Moon
_SADESATI_HOUSES = {12: "Rising", 1: "Peak", 2: "Setting"}


# ── Public API ────────────────────────────────────────────────────────────────


def compute_gochara(
    chart: ChartData,
    target_date: datetime | None = None,
) -> GocharaAnalysis:
    """Compute full Gochara (transit) analysis for a natal chart.

    Combines gochara base score (Phaladeepika Ch.26), Ashtakavarga BAV
    bindu count, Vedha obstruction, and Moorthy Nirnaya classification.

    Args:
        chart: Natal birth chart.
        target_date: Transit date (default: current IST time).

    Returns:
        GocharaAnalysis with all planet results, special phenomena, and summary.
    """
    if target_date is None:
        target_date = now_ist()

    data = _load()
    scores_table: dict[str, list[int]] = data["scores"]
    results_table: dict[str, dict[int, str]] = data["results"]
    special_names: dict[str, dict[int, str]] = data["special_names"]

    moon_sign = chart.planets["Moon"].sign_index
    ak_result = compute_ashtakavarga(chart)
    transit_data = compute_transits(chart, target_date)

    planet_results: list[GocharaPlanetResult] = []
    for tp in transit_data.transits:
        result = _compute_planet_result(
            planet_name=tp.name,
            transit_sign=tp.sign_index,
            moon_sign=moon_sign,
            chart=chart,
            ak_bhinna=ak_result.bhinna,
            scores_table=scores_table,
            results_table=results_table,
            special_names=special_names,
        )
        planet_results.append(result)

    # Sade Sati detection
    saturn = next((r for r in planet_results if r.planet == "Saturn"), None)
    sadesati_active = saturn is not None and saturn.house_from_moon in _SADESATI_HOUSES
    sadesati_phase = _SADESATI_HOUSES.get(saturn.house_from_moon) if saturn else None
    sadesati_intensity = (
        _sadesati_intensity(saturn.transit_sign_index)
        if (sadesati_active and saturn is not None)
        else None
    )

    double_houses = _detect_double_transit(chart, planet_results)
    total = sum(r.final_score for r in planet_results)
    overall = max(-10, min(10, total // 2))
    summary = _build_summary(planet_results, sadesati_active, sadesati_phase)

    return GocharaAnalysis(
        target_date=target_date.strftime("%d/%m/%Y"),
        chart_name=chart.name,
        moon_sign_index=moon_sign,
        moon_sign=SIGNS[moon_sign],
        planet_results=planet_results,
        sadesati_active=sadesati_active,
        sadesati_phase=sadesati_phase,
        sadesati_intensity=sadesati_intensity,
        double_transit_houses=double_houses,
        overall_rating=overall,
        summary=summary,
    )


# ── Private helpers ────────────────────────────────────────────────────────────


def _compute_planet_result(
    planet_name: str,
    transit_sign: int,
    moon_sign: int,
    chart: ChartData,
    ak_bhinna: dict[str, list[int]],
    scores_table: dict[str, list[int]],
    results_table: dict[str, dict[int, str]],
    special_names: dict[str, dict[int, str]],
) -> GocharaPlanetResult:
    """Compute gochara result for a single planet."""
    house_from_moon = ((transit_sign - moon_sign) % 12) + 1

    # Gochara base score from YAML (house index is 0-based in list)
    planet_scores = scores_table.get(planet_name, [0] * 12)
    gochara_score = planet_scores[house_from_moon - 1]

    favorability = _score_to_favorability(gochara_score)
    result_text = results_table.get(planet_name, {}).get(house_from_moon, "")
    special = special_names.get(planet_name, {}).get(house_from_moon)

    # BAV bindus (Rahu/Ketu not in BAV → neutral 4)
    bav_bindus = ak_bhinna.get(planet_name, [4] * 12)[transit_sign]
    moorthy = _classify_moorthy(bav_bindus)
    bav_mod = _bav_modifier(bav_bindus)

    # Vedha — only relevant for beneficial transits
    vedha_info: GocharaVedha | None = None
    vedha_active = False
    if gochara_score > 0:
        vp_list = check_vedha(chart, planet_name, transit_sign)
        if vp_list:
            vp = vp_list[0]
            vedha_info = GocharaVedha(
                vedha_house=vp.vedha_house,
                is_active=vp.is_blocked,
                blocking_planet=vp.blocking_planet,
            )
            vedha_active = vp.is_blocked

    # Final score: vedha zeroes out benefit; otherwise clamp gochara + BAV
    final = 0 if vedha_active else max(-4, min(4, gochara_score + bav_mod))

    return GocharaPlanetResult(
        planet=planet_name,
        transit_sign_index=transit_sign,
        transit_sign=SIGNS[transit_sign],
        house_from_moon=house_from_moon,
        gochara_score=gochara_score,
        favorability=favorability,
        result_text=result_text,
        special_name=special,
        vedha=vedha_info,
        vedha_active=vedha_active,
        bav_bindus=bav_bindus,
        moorthy=moorthy,
        final_score=final,
    )


def _classify_moorthy(bindus: int) -> MoorthyClass:
    """Classify transit quality from BAV bindu count."""
    if bindus >= 5:
        return MoorthyClass.poorna
    if bindus >= 3:
        return MoorthyClass.madhya
    if bindus >= 1:
        return MoorthyClass.swalpa
    return MoorthyClass.nishphala


def _bav_modifier(bindus: int) -> int:
    """Map BAV bindu count to additive score modifier."""
    for rng, mod in _BINDU_TO_MOD:
        if bindus in rng:
            return mod
    return 0


def _score_to_favorability(score: int) -> Favorability:
    """Map numeric gochara score to favorability label."""
    mapping = {
        2: Favorability.very_favorable,
        1: Favorability.favorable,
        0: Favorability.neutral,
        -1: Favorability.unfavorable,
        -2: Favorability.very_unfavorable,
    }
    return mapping.get(score, Favorability.neutral)


def _sadesati_intensity(saturn_sign: int) -> str:
    """Sade Sati intensity based on Saturn's transit sign dignity."""
    if saturn_sign in (6, 9, 10):  # Libra (exalted), Capricorn, Aquarius (own)
        return "mild"
    if saturn_sign == 0:  # Aries — Saturn debilitated
        return "severe"
    return "moderate"


def _detect_double_transit(
    chart: ChartData,
    planet_results: list[GocharaPlanetResult],
) -> list[int]:
    """Detect houses where both Jupiter and Saturn are active from Moon.

    Double transit (K.N. Rao method): Jupiter and Saturn must both be
    transiting (or aspecting) the same house for major life events.

    Returns list of house numbers (1-12) with active double transit.
    """
    jup = next((r for r in planet_results if r.planet == "Jupiter"), None)
    sat = next((r for r in planet_results if r.planet == "Saturn"), None)
    if not jup or not sat:
        return []

    jup_transit_house = jup.house_from_moon
    sat_transit_house = sat.house_from_moon

    # Aspected houses (Jupiter: 5,7,9; Saturn: 3,7,10 from their transit house)
    def _aspected(transit_h: int, extras: list[int]) -> set[int]:
        houses: set[int] = {transit_h}
        houses.add(((transit_h - 1 + 6) % 12) + 1)  # 7th from transit house
        for extra in extras:
            houses.add(((transit_h - 1 + extra - 1) % 12) + 1)
        return houses

    jup_houses = _aspected(jup_transit_house, [5, 9])
    sat_houses = _aspected(sat_transit_house, [3, 10])
    return sorted(jup_houses & sat_houses)


def _build_summary(
    results: list[GocharaPlanetResult],
    sadesati: bool,
    phase: str | None,
) -> str:
    """Build a brief human-readable transit summary."""
    parts: list[str] = []

    if sadesati:
        parts.append(f"Sade Sati active ({phase} phase)")

    favorable = [r.planet for r in results if r.final_score >= 2]
    difficult = [r.planet for r in results if r.final_score <= -2]

    if favorable:
        parts.append(f"Favorable: {', '.join(favorable)}")
    if difficult:
        parts.append(f"Challenging: {', '.join(difficult)}")

    special = [r.special_name for r in results if r.special_name]
    if special:
        parts.append(", ".join(special))

    return " | ".join(parts) if parts else "Mixed transit period"
