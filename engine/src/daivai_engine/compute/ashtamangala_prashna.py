"""Ashtamangala Prashna — Kerala horary astrology.

The Ashtamangala (Eight Auspicious Objects) system is the gold standard
for Kerala horary astrology, integrating:
  - 8 Mangala Dravyas mapped to planets and domains
  - Trisphuta / Chatusphuta / Panchasphuta / Pranapada sensitive points
  - Swara Prashna (breath-based directional analysis)
  - Aroodha computation per Jaimini / Prashna Marga
  - Deva Prashna classification (dharma / artha / kama / moksha)
  - Number Prashna via 108-division framework

Source: Prashna Marga (Kerala), Ashtamangala Deva Prashna tradition.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from daivai_engine.compute.ashtamangala_utils import (
    _QUERY_MAP,
    _STRENGTH_HOUSES,
    _get_gulika_longitude,
    classify_query,
    compute_aroodha,
    number_prashna,
)
from daivai_engine.constants import KENDRAS, SIGN_ELEMENTS, SIGN_LORDS, SIGNS
from daivai_engine.models.ashtamangala import (
    AshtamangalaResult,
    MangalaAssessment,
    SphutuResult,
)
from daivai_engine.models.chart import ChartData


__all__ = [
    "analyze_ashtamangala",
    "classify_query",
    "compute_aroodha",
    "number_prashna",
]

_KNOWLEDGE_PATH = Path(__file__).parent.parent / "knowledge" / "ashtamangala_prashna.yaml"

_DUSTHANA_HOUSES: frozenset[int] = frozenset([6, 8, 12])


@lru_cache(maxsize=1)
def _load_knowledge() -> dict[str, list[dict[str, str]]]:
    """Load Ashtamangala Prashna knowledge YAML (cached after first call)."""
    with _KNOWLEDGE_PATH.open() as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


_DEVA_NATURE: dict[str, str] = {
    "dharma": "sattvik",
    "artha": "rajasik",
    "kama": "rajasik",
    "moksha": "tamasik",
}

_DEVA_DESC: dict[str, str] = {
    "dharma": "Dharmic query — Jupiter and Sun are primary karakas.",
    "artha": "Artha (material) query — Mercury, Venus, Jupiter govern.",
    "kama": "Kama (desire/relationship) query — Moon, Venus, Mars govern.",
    "moksha": "Moksha (liberation/hidden) query — Saturn, Ketu, Jupiter govern.",
}


def _compute_sphutas(chart: ChartData) -> SphutuResult:
    """Compute Trisphuta, Chatusphuta, Panchasphuta, and Pranapada.

    Formulas (Prashna Marga Ch.3 / Kerala Ashtamangala tradition):
      Trisphuta    = Lagna + Moon + Gulika              (mod 360)
      Chatusphuta  = Lagna + Moon + Sun + Gulika        (mod 360)
      Panchasphuta = Lagna + Moon + Sun + Jupiter + Gulika (mod 360)
      Pranapada    = Lagna + Moon - Sun                 (mod 360)
    Pranapada = Lot of Fortune; used as life-breath point in horary.
    """
    lagna = chart.lagna_longitude
    moon = chart.planets["Moon"].longitude
    sun = chart.planets["Sun"].longitude
    jupiter = chart.planets["Jupiter"].longitude
    gulika = _get_gulika_longitude(chart)

    trisphuta = (lagna + moon + gulika) % 360.0
    chatusphuta = (lagna + moon + sun + gulika) % 360.0
    panchasphuta = (lagna + moon + sun + jupiter + gulika) % 360.0
    pranapada = (lagna + moon - sun + 360.0) % 360.0

    def sidx(lon: float) -> int:
        return int(lon // 30)

    return SphutuResult(
        trisphuta=round(trisphuta, 4),
        chatusphuta=round(chatusphuta, 4),
        panchasphuta=round(panchasphuta, 4),
        pranapada=round(pranapada, 4),
        trisphuta_sign_index=sidx(trisphuta),
        chatusphuta_sign_index=sidx(chatusphuta),
        panchasphuta_sign_index=sidx(panchasphuta),
        pranapada_sign_index=sidx(pranapada),
        trisphuta_sign=SIGNS[sidx(trisphuta)],
        chatusphuta_sign=SIGNS[sidx(chatusphuta)],
        panchasphuta_sign=SIGNS[sidx(panchasphuta)],
        pranapada_sign=SIGNS[sidx(pranapada)],
    )


def _assess_mangala_dravyas(chart: ChartData, query_type: str) -> list[MangalaAssessment]:
    """Evaluate all 8 Mangala Dravyas for favorability.

    Favorability rules (Prashna Marga Ch.7):
      - Planet in kendra/trikona OR exalted/own/mooltrikona → favorable
      - Planet combust OR in dusthana (6/8/12) → unfavorable
      - Neutral placement → mildly favorable

    The 8th Dravya (Pushpa/Flowers) uses the Lagna lord as its planet,
    symbolizing the chart's primary ruler and auspicious self-expression.
    """
    knowledge = _load_knowledge()
    lagna_lord = SIGN_LORDS[chart.lagna_sign_index]
    house, karaka, _ = _QUERY_MAP.get(query_type, (1, "Moon", "dharma"))
    query_lord = SIGN_LORDS[(chart.lagna_sign_index + house - 1) % 12]

    assessments: list[MangalaAssessment] = []
    for dravya in knowledge["mangala_dravyas"]:
        # Resolve special "LagnaLord" token
        raw_planet = dravya["planet"]
        planet_name = lagna_lord if raw_planet == "LagnaLord" else raw_planet

        planet = chart.planets.get(planet_name)
        if planet is None:
            continue

        ph = planet.house
        is_dignified = planet.dignity in ("exalted", "own", "mooltrikona")
        is_relevant = planet_name in {lagna_lord, query_lord, karaka}

        if planet.is_combust:
            is_favorable = False
            reason = f"{planet_name} is combust — {dravya['name_en']} weakened."
        elif ph in _DUSTHANA_HOUSES:
            is_favorable = False
            reason = f"{planet_name} in dusthana H{ph} — {dravya['name_en']} indicates obstacles."
        elif ph in _STRENGTH_HOUSES or is_dignified:
            is_favorable = True
            qualifier = "karaka and " if is_relevant else ""
            reason = f"{planet_name} is {qualifier}strong in H{ph} ({planet.dignity})."
        else:
            is_favorable = True  # neutral placement = acceptable
            reason = (
                f"{planet_name} in H{ph} ({planet.dignity}) — {dravya['name_en']} is acceptable."
            )

        assessments.append(
            MangalaAssessment(
                dravya=dravya["name"],
                dravya_en=dravya["name_en"],
                planet=planet_name,
                signification=str(dravya["signification"]).strip(),
                is_favorable=is_favorable,
                planet_house=ph,
                planet_dignity=planet.dignity,
                reason=reason,
            )
        )
    return assessments


def analyze_ashtamangala(chart: ChartData, query_type: str) -> AshtamangalaResult:
    """Full Ashtamangala Prashna analysis per Kerala horary tradition.

    Integrates:
      - Deva Prashna classification (dharma/artha/kama/moksha)
      - Aroodha computation (Jaimini / Prashna Marga algorithm)
      - 8 Mangala Dravyas planetary assessment
      - Trisphuta / Chatusphuta / Panchasphuta / Pranapada
      - Swara Prashna (Lagna element resonance analysis)

    Args:
        chart: ChartData for the question moment.
        query_type: Category of the query (marriage, career, etc.).

    Returns:
        AshtamangalaResult with complete Ashtamangala analysis and verdict.
    """
    classification = classify_query(query_type)
    aroodha = compute_aroodha(chart, classification.primary_house)
    dravyas = _assess_mangala_dravyas(chart, query_type)
    sphuta = _compute_sphutas(chart)

    # Most favorable Dravya: prefer karaka planet, then strongest house
    favorable = [d for d in dravyas if d.is_favorable]
    most_favorable = (
        max(favorable, key=lambda d: d.planet_house in _STRENGTH_HOUSES)
        if favorable
        else dravyas[0]
    )

    # Score: each favorable Dravya = +1, unfavorable = part of negative
    positive = sum(1 for d in dravyas if d.is_favorable)
    negative = len(dravyas) - positive

    if aroodha.is_strong:
        positive += 2
    else:
        negative += 1

    # Panchasphuta house relative to lagna
    ps_house = (sphuta.panchasphuta_sign_index - chart.lagna_sign_index) % 12 + 1
    if ps_house in KENDRAS:
        positive += 1
    elif ps_house in _DUSTHANA_HOUSES:
        negative += 1

    # Swara analysis from Lagna element (Prashna Marga Ch.5)
    element = SIGN_ELEMENTS[chart.lagna_sign_index]
    if element in ("Water", "Earth"):
        swara_analysis = (
            f"Lagna in {element} sign — Ida (Moon/left nostril) resonates. "
            "Favorable for receptive, stable outcomes."
        )
    else:
        swara_analysis = (
            f"Lagna in {element} sign — Pingala (Sun/right nostril) resonates. "
            "Favorable for active, assertive pursuits."
        )

    # Verdict
    gap = positive - negative
    if gap >= 3:
        answer, confidence = "YES", "high"
    elif gap <= -3:
        answer, confidence = "NO", "high"
    elif gap > 0:
        answer, confidence = "YES", "medium"
    elif gap < 0:
        answer, confidence = "NO", "medium"
    else:
        answer, confidence = "MAYBE", "low"

    reasoning = (
        f"Deva category: {classification.deva_category} ({classification.nature}). "
        f"Aroodha of H{aroodha.house} in {aroodha.aroodha_sign} — "
        f"{'strong' if aroodha.is_strong else 'weak'}. "
        f"{positive}/{len(dravyas)} Mangala Dravyas favorable. "
        f"Panchasphuta in {sphuta.panchasphuta_sign} (H{ps_house}). "
        f"Most auspicious: {most_favorable.dravya_en} ({most_favorable.planet})."
    )

    return AshtamangalaResult(
        query_type=query_type,
        classification=classification,
        aroodha=aroodha,
        most_favorable_dravya=most_favorable,
        all_dravyas=dravyas,
        sphuta=sphuta,
        swara_analysis=swara_analysis,
        answer=answer,
        confidence=confidence,
        reasoning=reasoning,
        positive_score=positive,
        negative_score=negative,
    )
