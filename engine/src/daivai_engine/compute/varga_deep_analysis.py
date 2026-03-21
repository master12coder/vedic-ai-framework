"""Varga Deep Analysis — D9, D10, D7, D12, and cross-varga confirmation.

Goes beyond basic varga computation to interpret each divisional chart:
  D9  — soul/dharma (lagna), spouse (7th house), vargottama confirmation
  D10 — career personality (lagna), career domain (10th house)
  D7  — children indicators (5th house), Jupiter karaka
  D12 — karmic signature (lagna), parent analysis (4th/9th houses)

Cross-varga confirmation: a planet in own sign or exaltation in all
three of D1 + D9 + D60 gives CERTAIN results per BPHS Shodashvarga rules.

Source: BPHS Chapters 16-17, 24.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.compute.divisional import (
    compute_dasamsha_sign,
    compute_dwadashamsha_sign,
    compute_navamsha_sign,
    compute_saptamsha_sign,
    compute_shashtyamsha_sign,
    compute_varga,
)
from daivai_engine.constants import SIGN_LORDS, SIGNS
from daivai_engine.models.chart import ChartData


class VargaDeepResult(BaseModel):
    """Deep analysis result for a single divisional chart."""

    varga: str  # D9, D10, D7, D12
    varga_name: str
    varga_lagna_sign: str
    varga_lagna_sign_index: int  # 0-11
    key_house_sign: str  # Most relevant house sign (7th for D9, 10th for D10, etc.)
    key_house_index: int  # House number (1-12)
    key_planets: list[str]  # Planets in the key house
    vargottama_planets: list[str]
    key_findings: list[str]
    strength: str  # strong / moderate / weak


class CrossVargaResult(BaseModel):
    """Cross-varga strength confirmation for a single planet across D1+D9+D60."""

    planet: str
    d1_sign: str
    d9_sign: str
    d60_sign: str
    in_d1_own_or_exalt: bool
    in_d9_own_or_exalt: bool
    in_d60_own_or_exalt: bool
    certainty: str  # certain / probable / possible / weak


# Own signs per planet (sign indices 0-11)
_OWN_SIGNS: dict[str, list[int]] = {
    "Sun": [4],
    "Moon": [3],
    "Mars": [0, 7],
    "Mercury": [2, 5],
    "Jupiter": [8, 11],
    "Venus": [1, 6],
    "Saturn": [9, 10],
    "Rahu": [],
    "Ketu": [],
}

# Exaltation sign index per planet
_EXALT_SIGNS: dict[str, int] = {
    "Sun": 0,  # Aries
    "Moon": 1,  # Taurus
    "Mars": 9,  # Capricorn
    "Mercury": 5,  # Virgo
    "Jupiter": 3,  # Cancer
    "Venus": 11,  # Pisces
    "Saturn": 6,  # Libra
    "Rahu": 2,  # Gemini
    "Ketu": 8,  # Sagittarius
}


def _strong_in_sign(planet: str, sign_index: int) -> bool:
    """True if planet is in own sign or exaltation."""
    return sign_index in _OWN_SIGNS.get(planet, []) or _EXALT_SIGNS.get(planet) == sign_index


def analyze_d9_deep(chart: ChartData) -> VargaDeepResult:
    """Deep D9 Navamsha analysis — lagna, 7th house (spouse), vargottama.

    D9 lagna reveals dharmic orientation and soul purpose.
    D9 7th shows spouse nature and marital karma.
    Vargottama planets deliver maximum results with reliability.

    Source: BPHS Ch.24.
    """
    d9_lagna = compute_navamsha_sign(chart.lagna_longitude)
    d9_7th = (d9_lagna + 6) % 12

    positions = compute_varga(chart, "D9")
    pos_map = {p.planet: p for p in positions}

    vargottama = [p.planet for p in positions if p.is_vargottam]
    planets_in_7th = [p.planet for p in positions if p.divisional_sign_index == d9_7th]

    findings: list[str] = [
        f"D9 Lagna: {SIGNS[d9_lagna]} — dharmic orientation and soul purpose",
        f"D9 7th house: {SIGNS[d9_7th]} — spouse nature and marital karma",
    ]
    if vargottama:
        findings.append(f"Vargottama (maximum strength): {', '.join(vargottama)}")
    if planets_in_7th:
        findings.append(f"Planets in D9 7th ({SIGNS[d9_7th]}): {', '.join(planets_in_7th)}")

    d9_7th_lord = SIGN_LORDS[d9_7th]
    if d9_7th_lord in pos_map:
        findings.append(
            f"D9 7th lord ({d9_7th_lord}) placed in: {pos_map[d9_7th_lord].divisional_sign}"
        )

    strength = "strong" if len(vargottama) >= 2 else ("moderate" if vargottama else "weak")
    return VargaDeepResult(
        varga="D9",
        varga_name="Navamsha",
        varga_lagna_sign=SIGNS[d9_lagna],
        varga_lagna_sign_index=d9_lagna,
        key_house_sign=SIGNS[d9_7th],
        key_house_index=7,
        key_planets=planets_in_7th,
        vargottama_planets=vargottama,
        key_findings=findings,
        strength=strength,
    )


def analyze_d10_deep(chart: ChartData) -> VargaDeepResult:
    """Deep D10 Dasamsha analysis — career personality (lagna) and domain (10th).

    D10 lagna indicates public personality and professional approach.
    D10 10th house reveals the career domain and professional karma.

    Source: BPHS Ch.17.
    """
    d10_lagna = compute_dasamsha_sign(chart.lagna_longitude)
    d10_10th = (d10_lagna + 9) % 12

    positions = compute_varga(chart, "D10")
    pos_map = {p.planet: p for p in positions}

    vargottama = [p.planet for p in positions if p.is_vargottam]
    planets_in_10th = [p.planet for p in positions if p.divisional_sign_index == d10_10th]

    findings: list[str] = [
        f"D10 Lagna: {SIGNS[d10_lagna]} — career personality and public approach",
        f"D10 10th house: {SIGNS[d10_10th]} — career domain and professional karma",
    ]
    if planets_in_10th:
        findings.append(f"Planets in D10 10th ({SIGNS[d10_10th]}): {', '.join(planets_in_10th)}")

    d10_10th_lord = SIGN_LORDS[d10_10th]
    if d10_10th_lord in pos_map:
        findings.append(
            f"D10 10th lord ({d10_10th_lord}) in D10: {pos_map[d10_10th_lord].divisional_sign}"
        )
    if vargottama:
        findings.append(f"Vargottama in D10: {', '.join(vargottama)} — reliable career promise")

    strength = "strong" if planets_in_10th else "moderate"
    return VargaDeepResult(
        varga="D10",
        varga_name="Dasamsha",
        varga_lagna_sign=SIGNS[d10_lagna],
        varga_lagna_sign_index=d10_lagna,
        key_house_sign=SIGNS[d10_10th],
        key_house_index=10,
        key_planets=planets_in_10th,
        vargottama_planets=vargottama,
        key_findings=findings,
        strength=strength,
    )


def analyze_d7_deep(chart: ChartData) -> VargaDeepResult:
    """Deep D7 Saptamsha analysis — children indicators from 5th house.

    D7 5th house is the primary children indicator.
    Jupiter as Putra Karaka is checked in both D7 and D7 5th.

    Source: BPHS Ch.17.
    """
    d7_lagna = compute_saptamsha_sign(chart.lagna_longitude)
    d7_5th = (d7_lagna + 4) % 12

    positions = compute_varga(chart, "D7")
    pos_map = {p.planet: p for p in positions}

    vargottama = [p.planet for p in positions if p.is_vargottam]
    planets_in_5th = [p.planet for p in positions if p.divisional_sign_index == d7_5th]

    findings: list[str] = [
        f"D7 Lagna: {SIGNS[d7_lagna]}",
        f"D7 5th house: {SIGNS[d7_5th]} — primary children indicator",
    ]
    if planets_in_5th:
        findings.append(f"Planets in D7 5th ({SIGNS[d7_5th]}): {', '.join(planets_in_5th)}")

    if "Jupiter" in pos_map:
        jup_sign = pos_map["Jupiter"].divisional_sign
        findings.append(f"Jupiter (Putra Karaka) in D7: {jup_sign}")
        if pos_map["Jupiter"].divisional_sign_index == d7_5th:
            findings.append("Jupiter in D7 5th — strong children promise")

    d7_5th_lord = SIGN_LORDS[d7_5th]
    if d7_5th_lord in pos_map:
        findings.append(
            f"D7 5th lord ({d7_5th_lord}) in D7: {pos_map[d7_5th_lord].divisional_sign}"
        )

    strength = "strong" if "Jupiter" in planets_in_5th or vargottama else "moderate"
    return VargaDeepResult(
        varga="D7",
        varga_name="Saptamsha",
        varga_lagna_sign=SIGNS[d7_lagna],
        varga_lagna_sign_index=d7_lagna,
        key_house_sign=SIGNS[d7_5th],
        key_house_index=5,
        key_planets=planets_in_5th,
        vargottama_planets=vargottama,
        key_findings=findings,
        strength=strength,
    )


def analyze_d12_deep(chart: ChartData) -> VargaDeepResult:
    """Deep D12 Dwadashamsha analysis — karmic signature and parent karma.

    D12 lagna = ancestral/karmic orientation.
    D12 4th = mother karma (Moon as natural karaka).
    D12 9th = father karma (Sun as natural karaka).

    Source: BPHS Ch.17.
    """
    d12_lagna = compute_dwadashamsha_sign(chart.lagna_longitude)
    d12_4th = (d12_lagna + 3) % 12  # Mother
    d12_9th = (d12_lagna + 8) % 12  # Father

    positions = compute_varga(chart, "D12")
    pos_map = {p.planet: p for p in positions}

    vargottama = [p.planet for p in positions if p.is_vargottam]
    planets_in_4th = [p.planet for p in positions if p.divisional_sign_index == d12_4th]
    planets_in_9th = [p.planet for p in positions if p.divisional_sign_index == d12_9th]

    findings: list[str] = [
        f"D12 Lagna: {SIGNS[d12_lagna]} — karmic signature and ancestral energy",
        f"D12 4th ({SIGNS[d12_4th]}) — mother karma",
        f"D12 9th ({SIGNS[d12_9th]}) — father karma",
    ]
    if planets_in_4th:
        findings.append(f"Planets in D12 4th: {', '.join(planets_in_4th)}")
    if planets_in_9th:
        findings.append(f"Planets in D12 9th: {', '.join(planets_in_9th)}")
    if "Moon" in pos_map:
        findings.append(f"Moon (mother karaka) in D12: {pos_map['Moon'].divisional_sign}")
    if "Sun" in pos_map:
        findings.append(f"Sun (father karaka) in D12: {pos_map['Sun'].divisional_sign}")

    parental_count = len(set(planets_in_4th + planets_in_9th))
    strength = "strong" if parental_count >= 2 else "moderate"
    return VargaDeepResult(
        varga="D12",
        varga_name="Dwadashamsha",
        varga_lagna_sign=SIGNS[d12_lagna],
        varga_lagna_sign_index=d12_lagna,
        key_house_sign=SIGNS[d12_9th],
        key_house_index=9,
        key_planets=planets_in_9th,
        vargottama_planets=vargottama,
        key_findings=findings,
        strength=strength,
    )


def cross_varga_confirm(chart: ChartData, planet: str) -> CrossVargaResult:
    """Confirm a planet's results via D1 + D9 + D60 strength agreement.

    A planet in own sign or exaltation in all three of D1, D9, and D60
    gives CERTAIN results. Strong in 2 = probable; 1 = possible; 0 = weak.

    Source: BPHS Shodashvarga chapter — vimshopaka and multi-varga rules.

    Args:
        chart: A fully computed birth chart.
        planet: Planet name to check (must be in constants.PLANETS).

    Returns:
        CrossVargaResult with per-chart dignity flags and certainty level.
    """
    p = chart.planets[planet]
    d1_sign = p.sign_index
    d9_sign = compute_navamsha_sign(p.longitude)
    d60_sign = compute_shashtyamsha_sign(p.longitude)

    d1_strong = _strong_in_sign(planet, d1_sign)
    d9_strong = _strong_in_sign(planet, d9_sign)
    d60_strong = _strong_in_sign(planet, d60_sign)

    count = sum([d1_strong, d9_strong, d60_strong])
    if count == 3:
        certainty = "certain"
    elif count == 2:
        certainty = "probable"
    elif count == 1:
        certainty = "possible"
    else:
        certainty = "weak"

    return CrossVargaResult(
        planet=planet,
        d1_sign=SIGNS[d1_sign],
        d9_sign=SIGNS[d9_sign],
        d60_sign=SIGNS[d60_sign],
        in_d1_own_or_exalt=d1_strong,
        in_d9_own_or_exalt=d9_strong,
        in_d60_own_or_exalt=d60_strong,
        certainty=certainty,
    )
