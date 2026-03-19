"""Divisional Chart Analysis — D7, D4, D24, D10 interpretation.

Analyzes specific vargas for children, property, education, and career.

Source: BPHS Chapters 16-17.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.compute.divisional import compute_varga
from daivai_engine.constants import SIGN_LORDS
from daivai_engine.models.chart import ChartData


class VargaAnalysis(BaseModel):
    """Interpretation of a specific divisional chart."""

    varga: str  # D7, D4, D24, D10
    varga_name: str
    varga_name_hi: str
    karaka: str  # Significator planet
    karaka_sign: str  # Sign in this varga
    house_lord_sign: str  # Relevant house lord's varga sign
    key_findings: list[str]
    strength: str  # strong / moderate / weak


def analyze_d7_children(chart: ChartData) -> VargaAnalysis:
    """Analyze D7 (Saptamsha) for children indications.

    Karaka: Jupiter (Putra Karaka)
    Key house: 5th lord's D7 placement

    Source: BPHS Ch.17.
    """
    positions = compute_varga(chart, "D7")
    jup_pos = next((p for p in positions if p.planet == "Jupiter"), None)
    fifth_lord = SIGN_LORDS[(chart.lagna_sign_index + 4) % 12]
    fifth_pos = next((p for p in positions if p.planet == fifth_lord), None)

    findings = []
    strength = "moderate"

    if jup_pos:
        findings.append(f"Jupiter in D7: {jup_pos.divisional_sign}")
        if jup_pos.is_vargottam:
            findings.append("Jupiter is Vargottam — strong for children")
            strength = "strong"

    if fifth_pos:
        findings.append(f"5th lord ({fifth_lord}) in D7: {fifth_pos.divisional_sign}")

    return VargaAnalysis(
        varga="D7",
        varga_name="Saptamsha",
        varga_name_hi="सप्तमांश",
        karaka="Jupiter",
        karaka_sign=jup_pos.divisional_sign if jup_pos else "unknown",
        house_lord_sign=fifth_pos.divisional_sign if fifth_pos else "unknown",
        key_findings=findings,
        strength=strength,
    )


def analyze_d4_property(chart: ChartData) -> VargaAnalysis:
    """Analyze D4 (Chaturthamsha) for property/assets.

    Karaka: Mars (Bhumi Karaka)
    Key house: 4th lord's D4 placement

    Source: BPHS Ch.17.
    """
    positions = compute_varga(chart, "D4")
    mars_pos = next((p for p in positions if p.planet == "Mars"), None)
    fourth_lord = SIGN_LORDS[(chart.lagna_sign_index + 3) % 12]
    fourth_pos = next((p for p in positions if p.planet == fourth_lord), None)

    findings = []
    strength = "moderate"

    if mars_pos:
        findings.append(f"Mars in D4: {mars_pos.divisional_sign}")
        if mars_pos.is_vargottam:
            findings.append("Mars Vargottam — strong for property")
            strength = "strong"

    if fourth_pos:
        findings.append(f"4th lord ({fourth_lord}) in D4: {fourth_pos.divisional_sign}")

    return VargaAnalysis(
        varga="D4",
        varga_name="Chaturthamsha",
        varga_name_hi="चतुर्थांश",
        karaka="Mars",
        karaka_sign=mars_pos.divisional_sign if mars_pos else "unknown",
        house_lord_sign=fourth_pos.divisional_sign if fourth_pos else "unknown",
        key_findings=findings,
        strength=strength,
    )


def analyze_d24_education(chart: ChartData) -> VargaAnalysis:
    """Analyze D24 (Chaturvimshamsha) for education.

    Karaka: Mercury + Jupiter
    Key house: 5th lord's D24 placement

    Source: BPHS Ch.17.
    """
    positions = compute_varga(chart, "D24")
    merc_pos = next((p for p in positions if p.planet == "Mercury"), None)
    jup_pos = next((p for p in positions if p.planet == "Jupiter"), None)
    fifth_lord = SIGN_LORDS[(chart.lagna_sign_index + 4) % 12]
    fifth_pos = next((p for p in positions if p.planet == fifth_lord), None)

    findings = []
    strength = "moderate"

    if merc_pos:
        findings.append(f"Mercury in D24: {merc_pos.divisional_sign}")
    if jup_pos:
        findings.append(f"Jupiter in D24: {jup_pos.divisional_sign}")
    if fifth_pos:
        findings.append(f"5th lord ({fifth_lord}) in D24: {fifth_pos.divisional_sign}")

    # Strong if both Mercury and Jupiter are in good dignity
    vargottam_count = sum(1 for p in [merc_pos, jup_pos] if p and p.is_vargottam)
    if vargottam_count >= 1:
        strength = "strong"
        findings.append("Education karaka(s) Vargottam — strong academic potential")

    return VargaAnalysis(
        varga="D24",
        varga_name="Chaturvimshamsha",
        varga_name_hi="चतुर्विंशांश",
        karaka="Mercury/Jupiter",
        karaka_sign=merc_pos.divisional_sign if merc_pos else "unknown",
        house_lord_sign=fifth_pos.divisional_sign if fifth_pos else "unknown",
        key_findings=findings,
        strength=strength,
    )


def analyze_d10_career(chart: ChartData) -> VargaAnalysis:
    """Analyze D10 (Dasamsha) for career.

    Karaka: Sun (authority) + Saturn (service)
    Key house: 10th lord's D10 placement

    Source: BPHS Ch.17.
    """
    positions = compute_varga(chart, "D10")
    sun_pos = next((p for p in positions if p.planet == "Sun"), None)
    sat_pos = next((p for p in positions if p.planet == "Saturn"), None)
    tenth_lord = SIGN_LORDS[(chart.lagna_sign_index + 9) % 12]
    tenth_pos = next((p for p in positions if p.planet == tenth_lord), None)

    findings = []
    strength = "moderate"

    if sun_pos:
        findings.append(f"Sun in D10: {sun_pos.divisional_sign}")
    if sat_pos:
        findings.append(f"Saturn in D10: {sat_pos.divisional_sign}")
    if tenth_pos:
        findings.append(f"10th lord ({tenth_lord}) in D10: {tenth_pos.divisional_sign}")

    if sun_pos and sun_pos.is_vargottam:
        strength = "strong"
        findings.append("Sun Vargottam in D10 — strong career authority")

    return VargaAnalysis(
        varga="D10",
        varga_name="Dasamsha",
        varga_name_hi="दशमांश",
        karaka="Sun/Saturn",
        karaka_sign=sun_pos.divisional_sign if sun_pos else "unknown",
        house_lord_sign=tenth_pos.divisional_sign if tenth_pos else "unknown",
        key_findings=findings,
        strength=strength,
    )
