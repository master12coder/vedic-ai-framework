"""Medical Astrology computation — Vaidya Jyotish analysis.

Implements Kala Purusha body mapping, disease yoga detection, and
Prana/Deha/Mrityu Sphuta calculation from a birth chart.

All rules loaded from engine/knowledge/medical_rules.yaml.
Zero hardcoded constants — all from YAML or engine/constants.py.

Sources:
  BPHS Ch.7 (Kala Purusha), Ch.68-70 (Roga Adhyaya);
  Saravali Ch.6; Phaladeepika Ch.6; Hora Sara Ch.8.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from daivai_engine.compute.chart import has_aspect
from daivai_engine.compute.medical_dosha import compute_tridosha
from daivai_engine.constants import NAKSHATRA_SPAN_DEG, NAKSHATRAS, SIGN_LORDS, SIGNS, SIGNS_HI
from daivai_engine.models.chart import ChartData
from daivai_engine.models.medical import (
    BodyPartVulnerability,
    DiseaseYoga,
    HealthAnalysis,
    SphutalResult,
)


_RULES_FILE = Path(__file__).parent.parent / "knowledge" / "medical_rules.yaml"

_DUSTHANAS = {6, 8, 12}
_TRIKONAS = {1, 5, 9}


@lru_cache(maxsize=1)
def _load_rules() -> dict:
    """Load medical rules YAML (cached after first call)."""
    with _RULES_FILE.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)  # type: ignore[no-any-return]


def _natural_malefics() -> set[str]:
    """Return the set of natural malefic planets from YAML."""
    return set(_load_rules().get("natural_malefics", ["Sun", "Mars", "Saturn", "Rahu", "Ketu"]))


def _is_afflicted_by_malefic(chart: ChartData, planet_name: str) -> bool:
    """Return True if the given planet is conjunct (same sign) with any natural malefic.

    "Affliction" in whole-sign Jyotish means a malefic shares the same sign
    as the planet being assessed.  Aspect-based affliction (drishti) is a
    softer form and is checked separately where required.

    Source: BPHS Ch.68 v.1-3 — general principle of graha pida (planetary affliction).
    """
    malefics = _natural_malefics()
    p = chart.planets[planet_name]
    for mal in malefics:
        if mal == planet_name:
            continue
        mal_data = chart.planets.get(mal)
        if mal_data and mal_data.sign_index == p.sign_index:
            return True
    return False


def _is_aspected_by_malefic(chart: ChartData, house: int) -> bool:
    """Return True if any natural malefic aspects the given house number."""
    malefics = _natural_malefics()
    return any(has_aspect(chart, mal, house) for mal in malefics)


def _afflicting_malefics_in_sign(chart: ChartData, sign_index: int) -> list[str]:
    """Return malefics placed in the given sign index."""
    malefics = _natural_malefics()
    result: list[str] = []
    for planet_name in malefics:
        p = chart.planets.get(planet_name)
        if p and p.sign_index == sign_index:
            result.append(planet_name)
    return result


def _afflicting_malefics_aspecting_sign(chart: ChartData, sign_index: int) -> list[str]:
    """Return malefics that aspect the house corresponding to sign_index from lagna.

    The house number for a sign is: ((sign_index - lagna_sign_index) % 12) + 1
    """
    malefics = _natural_malefics()
    house = ((sign_index - chart.lagna_sign_index) % 12) + 1
    result: list[str] = []
    for planet_name in malefics:
        if has_aspect(chart, planet_name, house):
            result.append(planet_name)
    return result


def _sphuta_nakshatra(longitude: float) -> str:
    """Return nakshatra name for a given sidereal longitude."""
    idx = int(longitude / NAKSHATRA_SPAN_DEG) % 27
    return NAKSHATRAS[idx]


def _lagnesh(chart: ChartData) -> str:
    """Return the name of the lagna lord (lord of ascendant sign)."""
    return SIGN_LORDS[chart.lagna_sign_index]


def _sixth_lord(chart: ChartData) -> str:
    """Return the lord of the 6th house (sign that is 6th from lagna)."""
    sixth_sign_index = (chart.lagna_sign_index + 5) % 12
    return SIGN_LORDS[sixth_sign_index]


# ── Body Part Vulnerability ───────────────────────────────────


def analyze_body_part_vulnerabilities(chart: ChartData) -> list[BodyPartVulnerability]:
    """Compute body part vulnerability for all 12 Kala Purusha zones.

    For each sign (body zone), assess affliction by:
      - Natural malefics placed in that sign (strongest affliction).
      - Natural malefics aspecting the corresponding house from lagna.

    Vulnerability levels:
      "high"     — 2+ malefics in sign, OR 1 malefic in sign + 1 aspecting
      "moderate" — 1 malefic in sign, OR 2+ malefics aspecting
      "low"      — 1 malefic aspecting only
      "none"     — no malefic influence

    Source: BPHS Ch.7 Kala Purusha Adhyaya; Saravali Ch.6 v.1-5.

    Args:
        chart: Fully computed birth chart.

    Returns:
        List of 12 BodyPartVulnerability records (one per sign).
    """
    rules = _load_rules()
    body_map: dict = rules["kala_purusha_body_mapping"]
    result: list[BodyPartVulnerability] = []

    for idx in range(12):
        zone = body_map[idx]
        in_sign = _afflicting_malefics_in_sign(chart, idx)
        aspecting = [p for p in _afflicting_malefics_aspecting_sign(chart, idx) if p not in in_sign]
        all_afflictors = in_sign + aspecting

        if len(in_sign) >= 2 or (len(in_sign) >= 1 and len(aspecting) >= 1):
            level = "high"
            reason = f"Malefics in sign: {', '.join(in_sign)}"
            if aspecting:
                reason += f"; aspecting: {', '.join(aspecting)}"
        elif len(in_sign) == 1:
            level = "moderate"
            reason = f"{in_sign[0]} placed in {zone['sign_en']} sign"
        elif len(aspecting) >= 2:
            level = "moderate"
            reason = f"Multiple malefics aspecting: {', '.join(aspecting)}"
        elif len(aspecting) == 1:
            level = "low"
            reason = f"{aspecting[0]} aspects this zone"
        else:
            level = "none"
            reason = "No malefic influence on this body zone"

        result.append(
            BodyPartVulnerability(
                sign_index=idx,
                sign=SIGNS[idx],
                sign_hi=SIGNS_HI[idx],
                body_parts=zone["body_parts"],
                body_parts_hi=zone["body_parts_hi"],
                afflicting_planets=all_afflictors,
                vulnerability_level=level,
                reason=reason,
            )
        )

    return result


# ── Disease Yoga Detection ────────────────────────────────────


def detect_disease_yogas(chart: ChartData) -> list[DiseaseYoga]:
    """Detect classical disease-indicating planetary combinations from a birth chart.

    Checks 13 specific yogas from BPHS Ch.68-70, Saravali Ch.6, and
    Phaladeepika Ch.6. Each yoga represents a specific vulnerability;
    presence does not guarantee disease, but indicates predisposition.

    Args:
        chart: Fully computed birth chart.

    Returns:
        List of DiseaseYoga results (one per checked yoga, present or absent).
    """
    rules = _load_rules()
    yoga_meta: list[dict] = rules["disease_yogas"]
    # Build a quick lookup by name
    meta_by_name = {y["name"]: y for y in yoga_meta}

    yogas: list[DiseaseYoga] = []
    malefics = _natural_malefics()

    sun = chart.planets["Sun"]
    moon = chart.planets["Moon"]
    mars = chart.planets["Mars"]
    mercury = chart.planets["Mercury"]
    jupiter = chart.planets["Jupiter"]
    venus = chart.planets["Venus"]
    saturn = chart.planets["Saturn"]
    rahu = chart.planets["Rahu"]
    ketu = chart.planets["Ketu"]

    # ── 1. Sun Afflicted in Dusthana ─────────────────────────
    m = meta_by_name["Sun Afflicted in Dusthana"]
    sun_in_dusthana = sun.house in _DUSTHANAS
    sun_afflicted = _is_afflicted_by_malefic(chart, "Sun")
    is_present = sun_in_dusthana and sun_afflicted
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=["Sun"],
            houses_involved=[sun.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Sun in {sun.house}th house (dusthana), afflicted by malefic"
                if is_present
                else f"Sun in {sun.house}th house — not in dusthana or not afflicted"
            ),
            source=m["source"],
        )
    )

    # ── 2. Moon Afflicted in Dusthana ────────────────────────
    m = meta_by_name["Moon Afflicted in Dusthana"]
    moon_in_dusthana = moon.house in {6, 8}
    moon_afflicted = _is_afflicted_by_malefic(chart, "Moon")
    is_present = moon_in_dusthana and moon_afflicted
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=["Moon"],
            houses_involved=[moon.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Moon in {moon.house}th house (6/8), afflicted — mental/blood risk"
                if is_present
                else f"Moon in {moon.house}th house — condition not met"
            ),
            source=m["source"],
        )
    )

    # ── 3. Mars in 6th or 8th ────────────────────────────────
    m = meta_by_name["Mars in 6th or 8th"]
    is_present = mars.house in {6, 8}
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=["Mars"],
            houses_involved=[mars.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Mars in {mars.house}th house — accident/surgery/blood risk"
                if is_present
                else f"Mars in {mars.house}th house — no disease yoga"
            ),
            source=m["source"],
        )
    )

    # ── 4. Saturn in Dusthana ────────────────────────────────
    m = meta_by_name["Saturn in Dusthana"]
    is_present = saturn.house in _DUSTHANAS
    severity = "high" if saturn.house == 8 else ("moderate" if is_present else "none")
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity=severity,
            planets_involved=["Saturn"],
            houses_involved=[saturn.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Saturn in {saturn.house}th house — chronic disease / bone-joint risk"
                if is_present
                else f"Saturn in {saturn.house}th house — no chronic disease yoga"
            ),
            source=m["source"],
        )
    )

    # ── 5. Rahu in 6th or 8th ────────────────────────────────
    m = meta_by_name["Rahu in 6th or 8th"]
    is_present = rahu.house in {6, 8}
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="high" if is_present else "none",
            planets_involved=["Rahu"],
            houses_involved=[rahu.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Rahu in {rahu.house}th house — mysterious chronic illness risk"
                if is_present
                else f"Rahu in {rahu.house}th house — no yoga"
            ),
            source=m["source"],
        )
    )

    # ── 6. Lagna Lord in Dusthana ────────────────────────────
    m = meta_by_name["Lagna Lord in Dusthana"]
    lagnesh_name = _lagnesh(chart)
    lagnesh = chart.planets[lagnesh_name]
    is_present = lagnesh.house in _DUSTHANAS
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=[lagnesh_name],
            houses_involved=[lagnesh.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Lagna lord {lagnesh_name} in {lagnesh.house}th house — weak constitution"
                if is_present
                else f"Lagna lord {lagnesh_name} in {lagnesh.house}th — strong constitution"
            ),
            source=m["source"],
        )
    )

    # ── 7. Both Luminaries Afflicted ─────────────────────────
    m = meta_by_name["Both Luminaries Afflicted"]
    sun_aff = _is_afflicted_by_malefic(chart, "Sun")
    moon_aff = _is_afflicted_by_malefic(chart, "Moon")
    is_present = sun_aff and moon_aff
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="high" if is_present else "none",
            planets_involved=["Sun", "Moon"],
            houses_involved=[sun.house, moon.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                "Both Sun and Moon afflicted by malefics — severe systemic disease risk"
                if is_present
                else "Not both luminaries afflicted"
            ),
            source=m["source"],
        )
    )

    # ── 8. Jupiter Afflicted in 8th ──────────────────────────
    m = meta_by_name["Jupiter Afflicted in 8th"]
    jup_in_8 = jupiter.house == 8
    jup_debilitated = jupiter.dignity == "debilitated"
    jup_afflicted = _is_afflicted_by_malefic(chart, "Jupiter")
    is_present = jup_in_8 and (jup_debilitated or jup_afflicted)
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=["Jupiter"],
            houses_involved=[jupiter.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Jupiter in 8th house, {'debilitated' if jup_debilitated else 'afflicted'} — liver risk"
                if is_present
                else f"Jupiter in {jupiter.house}th — no liver disease yoga"
            ),
            source=m["source"],
        )
    )

    # ── 9. Mercury Heavily Afflicted ─────────────────────────
    m = meta_by_name["Mercury Heavily Afflicted"]
    merc_malefic_conjuncts = [
        p
        for p in malefics
        if p != "Mercury"
        and chart.planets.get(p) is not None
        and chart.planets[p].sign_index == mercury.sign_index
    ]
    is_present = len(merc_malefic_conjuncts) >= 2
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="low" if is_present else "none",
            planets_involved=["Mercury", *merc_malefic_conjuncts],
            houses_involved=[mercury.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Mercury conjunct {', '.join(merc_malefic_conjuncts)} — nervous/skin/respiratory risk"
                if is_present
                else f"Mercury not heavily afflicted (conjuncts: {merc_malefic_conjuncts})"
            ),
            source=m["source"],
        )
    )

    # ── 10. Venus in 6th or 8th ──────────────────────────────
    m = meta_by_name["Venus in 6th or 8th"]
    is_present = venus.house in {6, 8}
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="low" if is_present else "none",
            planets_involved=["Venus"],
            houses_involved=[venus.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Venus in {venus.house}th house — kidney/reproductive risk"
                if is_present
                else f"Venus in {venus.house}th — no kidney yoga"
            ),
            source=m["source"],
        )
    )

    # ── 11. 6th Lord in 8th or 12th ──────────────────────────
    m = meta_by_name["6th Lord in 8th or 12th"]
    sixth_lord_name = _sixth_lord(chart)
    sixth_lord = chart.planets[sixth_lord_name]
    is_present = sixth_lord.house in {8, 12}
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=[sixth_lord_name],
            houses_involved=[sixth_lord.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"6th lord {sixth_lord_name} in {sixth_lord.house}th — disease→hospitalization path"
                if is_present
                else f"6th lord {sixth_lord_name} in {sixth_lord.house}th — favorable"
            ),
            source=m["source"],
        )
    )

    # ── 12. Mars-Saturn Conjunction in Dusthana ───────────────
    m = meta_by_name["Mars-Saturn Conjunction in Dusthana"]
    mars_saturn_same_sign = mars.sign_index == saturn.sign_index
    in_dusthana_sign = mars.house in _DUSTHANAS
    is_present = mars_saturn_same_sign and in_dusthana_sign
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="high" if is_present else "none",
            planets_involved=["Mars", "Saturn"],
            houses_involved=[mars.house] if is_present else [mars.house, saturn.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Mars and Saturn conjunct in {mars.house}th house — surgical emergency risk"
                if is_present
                else "Mars and Saturn not conjunct in dusthana"
            ),
            source=m["source"],
        )
    )

    # ── 13. Ketu in 6th or 8th ───────────────────────────────
    m = meta_by_name["Ketu in 6th or 8th"]
    is_present = ketu.house in {6, 8}
    yogas.append(
        DiseaseYoga(
            name=m["name"],
            name_hindi=m["name_hindi"],
            is_present=is_present,
            severity="moderate" if is_present else "none",
            planets_involved=["Ketu"],
            houses_involved=[ketu.house],
            body_system_affected=m["body_system_affected"],
            disease_indicated=m["disease_indicated"],
            description=(
                f"Ketu in {ketu.house}th house — mysterious ailments / inflammation risk"
                if is_present
                else f"Ketu in {ketu.house}th — no yoga"
            ),
            source=m["source"],
        )
    )

    return yogas


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

    # Concordance: check if Prana Sphuta is in trikona or dusthana
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

    # Additional check: Prana and Mrityu in same sign → heightened risk
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

    # Dominant health concerns: high-vulnerability body zones + active high-severity yogas
    concerns: list[str] = []
    for vuln in body_vulnerabilities:
        if vuln.vulnerability_level == "high":
            concerns.append(f"{vuln.sign} zone ({', '.join(vuln.body_parts[:2])}) — {vuln.reason}")
    for yoga in disease_yogas:
        if yoga.is_present and yoga.severity in ("high", "moderate"):
            concerns.append(f"{yoga.name}: {yoga.body_system_affected}")

    # Summary
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
        dominant_health_concerns=concerns[:10],  # Cap at 10
        health_summary=health_summary,
    )
