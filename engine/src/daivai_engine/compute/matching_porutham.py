"""South Indian 10-Porutham marriage compatibility — main entry point.

Implements all 10 poruthams for South Indian (Tamil/Telugu/Kannada) tradition:
  1. Dinam        — Nakshatra distance auspiciousness (mod 9 check)
  2. Ganam        — Temperament: Deva / Manushya / Rakshasa
  3. Yoni         — Animal compatibility (binary: enemy or not)
  4. Rasi         — Moon sign distance compatibility
  5. Rasyadhipati — Moon sign lord friendship
  6. Rajju        — Body cord (ELIMINATORY — same part = dosha)
  7. Vedha        — Nakshatra obstruction pairs (ELIMINATORY)
  8. Vasya        — Sign-based dominance / magnetic control
  9. Mahendra     — Prosperity and longevity of groom
 10. Stree Deergha— Longevity and happiness of bride

Source: Muhurtha Martanda, Tamil Jyotisha tradition, Phaladeepika Ch.19.
"""

from __future__ import annotations

from daivai_engine.compute.matching_porutham_checks import (
    _dinam,
    _ganam,
    _mahendra,
    _rajju,
    _rasi,
    _rasyadhipati,
    _stree_deergha,
    _vasya,
    _vedha,
    _yoni,
)
from daivai_engine.compute.matching_porutham_tables import (
    _NAK_TO_RAJJU,
    _RAJJU_SEVERITY,
)
from daivai_engine.models.matching_porutham import PouruthamResult


__all__ = [
    "_dinam",
    "_ganam",
    "_mahendra",
    "_rajju",
    "_rasi",
    "_rasyadhipati",
    "_stree_deergha",
    "_vasya",
    "_vedha",
    "_yoni",
    "compute_porutham",
]


def compute_porutham(
    boy_nakshatra_index: int,
    girl_nakshatra_index: int,
    boy_moon_sign: int,
    girl_moon_sign: int,
) -> PouruthamResult:
    """Compute South Indian 10-Porutham marriage compatibility.

    Convention: boy = groom, girl = bride (traditional Tamil ordering).

    Rajju and Vedha are eliminatory — their presence marks the match as not
    recommended regardless of total agreed count. Minimum 6/10 for recommended.

    Args:
        boy_nakshatra_index: 0-based Moon nakshatra index of groom (0=Ashwini…26=Revati).
        girl_nakshatra_index: 0-based Moon nakshatra index of bride.
        boy_moon_sign: 0-based Moon sign index of groom (0=Aries…11=Pisces).
        girl_moon_sign: 0-based Moon sign index of bride.

    Returns:
        PouruthamResult with all 10 porutham results and overall recommendation.
    """
    poruthams = [
        _dinam(boy_nakshatra_index, girl_nakshatra_index),
        _ganam(boy_nakshatra_index, girl_nakshatra_index),
        _yoni(boy_nakshatra_index, girl_nakshatra_index),
        _rasi(boy_moon_sign, girl_moon_sign),
        _rasyadhipati(boy_moon_sign, girl_moon_sign),
        _rajju(boy_nakshatra_index, girl_nakshatra_index),
        _vedha(boy_nakshatra_index, girl_nakshatra_index),
        _vasya(boy_moon_sign, girl_moon_sign),
        _mahendra(boy_nakshatra_index, girl_nakshatra_index),
        _stree_deergha(boy_nakshatra_index, girl_nakshatra_index),
    ]

    agreed = sum(1 for p in poruthams if p.agrees)
    rajju_item = next(p for p in poruthams if p.name == "Rajju")
    vedha_item = next(p for p in poruthams if p.name == "Vedha")
    has_rajju = not rajju_item.agrees
    has_vedha = not vedha_item.agrees

    rajju_part = _NAK_TO_RAJJU[boy_nakshatra_index] if has_rajju else None
    rajju_sev = _RAJJU_SEVERITY[rajju_part] if rajju_part else "none"

    eliminatory = has_rajju or has_vedha
    is_recommended = agreed >= 6 and not eliminatory

    if agreed >= 8 and not eliminatory:
        recommendation = f"Excellent match ({agreed}/10) — highly recommended"
    elif agreed >= 6 and not eliminatory:
        recommendation = f"Good match ({agreed}/10) — recommended"
    elif eliminatory:
        doshas = []
        if has_rajju:
            doshas.append(f"Rajju Dosha ({rajju_part}, {rajju_sev})")
        if has_vedha:
            doshas.append("Vedha Dosha")
        recommendation = (
            f"Eliminatory dosha present: {', '.join(doshas)}. "
            f"Match not recommended despite {agreed}/10 agreement."
        )
    else:
        recommendation = f"Below minimum ({agreed}/10 < 6) — remedies and detailed analysis needed"

    return PouruthamResult(
        boy_nakshatra_index=boy_nakshatra_index,
        girl_nakshatra_index=girl_nakshatra_index,
        boy_moon_sign=boy_moon_sign,
        girl_moon_sign=girl_moon_sign,
        poruthams=poruthams,
        agreed_count=agreed,
        total_count=10,
        has_rajju_dosha=has_rajju,
        has_vedha_dosha=has_vedha,
        rajju_body_part=rajju_part,
        rajju_severity=rajju_sev,
        is_recommended=is_recommended,
        recommendation=recommendation,
    )
