"""Ashtakoot (36 Guna) matching for marriage compatibility.

Implements all 8 kootas with proper exception handling for doshas:
  - Bhakoot dosha exceptions (nakshatra lord friendship mitigation)
  - Nadi dosha noted (detailed exceptions in compatibility_advanced.py)
  - Vedha dosha awareness (13 nakshatra pairs that obstruct each other)

Source: Muhurta Chintamani, BPHS matching chapter, Phaladeepika.
"""

from __future__ import annotations

from daivai_engine.compute.matching_kootas import (
    _VEDHA_PAIRS,
    _bhakoot_score,
    _gana_score,
    _graha_maitri_score,
    _nadi_score,
    _tara_score,
    _varna_score,
    _vasya_score,
    _yoni_score,
)
from daivai_engine.constants import NAKSHATRAS
from daivai_engine.models.matching import MatchingResult


__all__ = [
    "_VEDHA_PAIRS",
    "_bhakoot_score",
    "_gana_score",
    "_graha_maitri_score",
    "_nadi_score",
    "_tara_score",
    "_varna_score",
    "_vasya_score",
    "_yoni_score",
    "compute_ashtakoot",
]


def compute_ashtakoot(
    person1_nakshatra_index: int,
    person1_moon_sign: int,
    person2_nakshatra_index: int,
    person2_moon_sign: int,
) -> MatchingResult:
    """Compute Ashtakoot (36 guna) matching.

    Convention: person1 = boy, person2 = girl (traditional).

    Includes:
    - All 8 kootas with proper exception handling for doshas
    - Vedha dosha check (13 traditional obstruction pairs)
    - Dosha summary notes for Nadi and Bhakoot
    - 18-point minimum threshold logic per BPHS
    """
    kootas = [
        _varna_score(person1_moon_sign, person2_moon_sign),
        _vasya_score(person1_moon_sign, person2_moon_sign),
        _tara_score(person1_nakshatra_index, person2_nakshatra_index),
        _yoni_score(person1_nakshatra_index, person2_nakshatra_index),
        _graha_maitri_score(person1_nakshatra_index, person2_nakshatra_index),
        _gana_score(person1_nakshatra_index, person2_nakshatra_index),
        _bhakoot_score(
            person1_moon_sign, person2_moon_sign, person1_nakshatra_index, person2_nakshatra_index
        ),
        _nadi_score(person1_nakshatra_index, person2_nakshatra_index),
    ]

    total = sum(k.obtained for k in kootas)
    max_total = 36.0
    percentage = (total / max_total) * 100

    # Vedha dosha check — Muhurta Chintamani
    has_vedha = frozenset({person1_nakshatra_index, person2_nakshatra_index}) in _VEDHA_PAIRS
    nak1_name = NAKSHATRAS[person1_nakshatra_index]
    nak2_name = NAKSHATRAS[person2_nakshatra_index]
    vedha_note = (
        f"Vedha Dosha: {nak1_name} and {nak2_name} are obstructing nakshatras — "
        "timing obstacles in the union. Remedies recommended."
        if has_vedha
        else ""
    )

    # Dosha notes
    dosha_notes: list[str] = []
    nadi_koota = next(k for k in kootas if k.name == "Nadi")
    if nadi_koota.obtained == 0.0:
        dosha_notes.append(
            "Nadi Dosha present (same nadi) — most serious dosha. "
            "Consult compatibility_advanced for exceptions."
        )
    bhakoot_koota = next(k for k in kootas if k.name == "Bhakoot")
    if bhakoot_koota.obtained == 0.0:
        dosha_notes.append(f"Bhakoot Dosha: {bhakoot_koota.description}")
    if has_vedha:
        dosha_notes.append(vedha_note)

    # Recommendation with 18-point threshold — BPHS
    if total >= 25:
        recommendation = "Excellent match (≥25/36) — highly recommended"
    elif total >= 18:
        recommendation = "Good match (≥18/36) — recommended with minor considerations"
    elif total >= 14:
        recommendation = "Average match (14-17/36) — proceed with caution and remedies"
    else:
        recommendation = (
            "Below minimum threshold (<14/36) — detailed chart analysis needed before proceeding"
        )

    return MatchingResult(
        person1_nakshatra_index=person1_nakshatra_index,
        person1_moon_sign=person1_moon_sign,
        person2_nakshatra_index=person2_nakshatra_index,
        person2_moon_sign=person2_moon_sign,
        kootas=kootas,
        total_obtained=total,
        total_max=max_total,
        percentage=round(percentage, 1),
        recommendation=recommendation,
        has_vedha_dosha=has_vedha,
        vedha_note=vedha_note,
        dosha_notes=dosha_notes,
    )
