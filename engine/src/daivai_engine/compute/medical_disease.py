"""Medical Astrology — disease yoga detection (Vaidya Jyotish).

Implements 13 classical disease-indicating planetary combinations
from BPHS Ch.68-70, Saravali Ch.6, and Phaladeepika Ch.6.

Part 1 (yogas 1-6) lives here; Part 2 (yogas 7-13) is in
medical_disease_part2.py.
"""

from __future__ import annotations

from daivai_engine.compute.medical_body import (
    _DUSTHANAS,
    _is_afflicted_by_malefic,
    _lagnesh,
    _load_rules,
    _natural_malefics,
)
from daivai_engine.compute.medical_disease_part2 import (
    _detect_disease_yogas_part2,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.medical import DiseaseYoga


def _detect_disease_yogas_part1(
    chart: ChartData, meta_by_name: dict, malefics: set[str]
) -> list[DiseaseYoga]:
    """Detect disease yogas 1-6: Sun, Moon, Mars, Saturn, Rahu, Lagnesh."""
    yogas: list[DiseaseYoga] = []

    sun = chart.planets["Sun"]
    moon = chart.planets["Moon"]
    mars = chart.planets["Mars"]
    saturn = chart.planets["Saturn"]
    rahu = chart.planets["Rahu"]

    # -- 1. Sun Afflicted in Dusthana -----------------------------------------
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
                f"Sun in {sun.house}th house (6/8/12), afflicted by malefic — vitality/heart risk"
                if is_present
                else f"Sun in {sun.house}th house — condition not met"
            ),
            source=m["source"],
        )
    )

    # -- 2. Moon Afflicted in Dusthana ----------------------------------------
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

    # -- 3. Mars in 6th or 8th ------------------------------------------------
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

    # -- 4. Saturn in Dusthana ------------------------------------------------
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

    # -- 5. Rahu in 6th or 8th ------------------------------------------------
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

    # -- 6. Lagna Lord in Dusthana --------------------------------------------
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

    return yogas


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
    meta_by_name = {y["name"]: y for y in yoga_meta}
    malefics = _natural_malefics()

    yogas: list[DiseaseYoga] = []
    yogas.extend(_detect_disease_yogas_part1(chart, meta_by_name, malefics))
    yogas.extend(_detect_disease_yogas_part2(chart, meta_by_name, malefics))
    return yogas
