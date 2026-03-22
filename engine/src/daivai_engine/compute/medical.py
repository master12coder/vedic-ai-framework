"""Medical Astrology computation — Vaidya Jyotish analysis.

Main entry point. Coordinates Kala Purusha body mapping, disease yoga
detection, tridosha, and Prana/Deha/Mrityu Sphuta from a birth chart.

All rules loaded from engine/knowledge/medical_rules.yaml.
Zero hardcoded constants — all from YAML or engine/constants.py.

Sources:
  BPHS Ch.7 (Kala Purusha), Ch.68-70 (Roga Adhyaya);
  Saravali Ch.6; Phaladeepika Ch.6; Hora Sara Ch.8.
"""

from __future__ import annotations

from daivai_engine.compute.medical_body import (
    _DUSTHANAS,
    _TRIKONAS,
    _sphuta_nakshatra,
    analyze_body_part_vulnerabilities,
)
from daivai_engine.compute.medical_disease import detect_disease_yogas
from daivai_engine.compute.medical_dosha import compute_tridosha
from daivai_engine.constants import SIGNS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.medical import HealthAnalysis, SphutalResult


# ── Trisphuta — Prana / Deha / Mrityu Sphuta ─────────────────


def compute_prana_deha_mrityu_sphuta(chart: ChartData) -> SphutalResult:
    """Compute Prana, Deha, and Mrityu Sphuta for medical prashna analysis.

    Formulas (all modulo 360):
      Prana Sphuta  = Lagna_lon + Sun_lon + Moon_lon
      Deha Sphuta   = Lagna_lon + Mars_lon + Moon_lon
      Mrityu Sphuta = Lagna_lon + Saturn_lon + Moon_lon

    These three points indicate vitality, body affliction, and longevity stress
    respectively. Their sign and nakshatra placement reveal which body area is
    under stress and the nature of the health concern.

    Source: Hora Sara Ch.8 v.4-6; Jataka Parijata Medical Ch.;
            Sarvartha Chintamani Roga Adhyaya.

    Args:
        chart: Fully computed birth chart.

    Returns:
        SphutalResult with all three sputas and interpretive assessment.
    """
    lagna_lon = chart.lagna_longitude
    sun_lon = chart.planets["Sun"].longitude
    moon_lon = chart.planets["Moon"].longitude
    mars_lon = chart.planets["Mars"].longitude
    saturn_lon = chart.planets["Saturn"].longitude

    prana = (lagna_lon + sun_lon + moon_lon) % 360.0
    deha = (lagna_lon + mars_lon + moon_lon) % 360.0
    mrityu = (lagna_lon + saturn_lon + moon_lon) % 360.0

    def _sign_index(lon: float) -> int:
        return int(lon / 30) % 12

    prana_si = _sign_index(prana)
    deha_si = _sign_index(deha)
    mrityu_si = _sign_index(mrityu)

    prana_house = ((prana_si - chart.lagna_sign_index) % 12) + 1
    if prana_house in _TRIKONAS:
        concordance = "favorable"
        vitality = "Strong vitality indicated — Prana Sphuta in trikona"
    elif prana_house in _DUSTHANAS:
        concordance = "challenging"
        vitality = "Vitality under stress — Prana Sphuta in dusthana; health vigilance advised"
    else:
        concordance = "neutral"
        vitality = "Moderate vitality — Prana Sphuta in neutral house"

    if prana_si == mrityu_si:
        concordance = "challenging"
        vitality += "; Prana and Mrityu Sphuta in same sign — critical health flag"

    interpretation = (
        f"Prana Sphuta in {SIGNS[prana_si]} (house {prana_house}) — vitality point. "
        f"Deha Sphuta in {SIGNS[deha_si]} — body affliction point (Mars-Moon-Lagna). "
        f"Mrityu Sphuta in {SIGNS[mrityu_si]} — longevity stress point (Saturn-Moon-Lagna). "
        f"Concordance: {concordance}."
    )

    return SphutalResult(
        prana_sphuta=round(prana, 4),
        prana_sphuta_sign=SIGNS[prana_si],
        prana_sphuta_sign_index=prana_si,
        prana_sphuta_nakshatra=_sphuta_nakshatra(prana),
        deha_sphuta=round(deha, 4),
        deha_sphuta_sign=SIGNS[deha_si],
        deha_sphuta_sign_index=deha_si,
        deha_sphuta_nakshatra=_sphuta_nakshatra(deha),
        mrityu_sphuta=round(mrityu, 4),
        mrityu_sphuta_sign=SIGNS[mrityu_si],
        mrityu_sphuta_sign_index=mrityu_si,
        mrityu_sphuta_nakshatra=_sphuta_nakshatra(mrityu),
        prana_deha_concordance=concordance,
        vitality_assessment=vitality,
        interpretation=interpretation,
    )


# ── Health House Analysis ─────────────────────────────────────


def _analyze_health_houses(chart: ChartData) -> dict[int, list[str]]:
    """Return planet names placed in the three disease houses (6, 8, 12).

    Source: BPHS Ch.68 Arishta Adhyaya v.1-5.
    """
    result: dict[int, list[str]] = {6: [], 8: [], 12: []}
    for planet_name, planet_data in chart.planets.items():
        if planet_data.house in result:
            result[planet_data.house].append(planet_name)
    return result


# ── Main Entry Point ──────────────────────────────────────────


def analyze_health(chart: ChartData) -> HealthAnalysis:
    """Perform complete Vaidya Jyotish analysis of a birth chart.

    Combines:
      - Kala Purusha body mapping (12 zones, vulnerability assessment)
      - Disease yoga detection (13 classical yogas)
      - Tridosha balance computation
      - Prana/Deha/Mrityu Sphuta (Trisphuta for medical prashna)
      - Health house analysis (6th/8th/12th occupants)

    Args:
        chart: Fully computed birth chart.

    Returns:
        HealthAnalysis with complete Vaidya Jyotish picture.
    """
    body_vulnerabilities = analyze_body_part_vulnerabilities(chart)
    disease_yogas = detect_disease_yogas(chart)
    tridosha = compute_tridosha(chart)
    sphuta = compute_prana_deha_mrityu_sphuta(chart)
    health_houses = _analyze_health_houses(chart)

    concerns: list[str] = []
    for vuln in body_vulnerabilities:
        if vuln.vulnerability_level == "high":
            concerns.append(f"{vuln.sign} zone ({', '.join(vuln.body_parts[:2])}) — {vuln.reason}")
    for yoga in disease_yogas:
        if yoga.is_present and yoga.severity in ("high", "moderate"):
            concerns.append(f"{yoga.name}: {yoga.body_system_affected}")

    active_yogas = [y for y in disease_yogas if y.is_present]
    high_vuln_zones = [v for v in body_vulnerabilities if v.vulnerability_level == "high"]

    health_summary = (
        f"Constitution: {tridosha.constitution_type} "
        f"(Vata {tridosha.vata_percentage}%, "
        f"Pitta {tridosha.pitta_percentage}%, "
        f"Kapha {tridosha.kapha_percentage}%). "
        f"{len(active_yogas)} disease yoga(s) active; "
        f"{len(high_vuln_zones)} high-vulnerability body zone(s). "
        f"Vitality: {sphuta.vitality_assessment}."
    )

    return HealthAnalysis(
        body_part_vulnerabilities=body_vulnerabilities,
        disease_yogas=disease_yogas,
        tridosha_balance=tridosha,
        sphuta_result=sphuta,
        health_house_analysis=health_houses,
        dominant_health_concerns=concerns[:10],
        health_summary=health_summary,
    )
