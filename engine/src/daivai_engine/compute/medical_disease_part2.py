"""Medical Astrology — disease yogas 7-13 (Jupiter through Ketu).

Covers: Both Luminaries Afflicted, Jupiter Afflicted in 8th,
Mercury Heavily Afflicted, Venus in 6th/8th, 6th Lord in 8th/12th,
Mars-Saturn Conjunction in Dusthana, Ketu in 6th/8th.

Source: BPHS Ch.68-70, Saravali Ch.6, Phaladeepika Ch.6.
"""

from __future__ import annotations

from daivai_engine.compute.medical_body import (
    _DUSTHANAS,
    _is_afflicted_by_malefic,
    _sixth_lord,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.medical import DiseaseYoga


def _detect_disease_yogas_part2(
    chart: ChartData, meta_by_name: dict, malefics: set[str]
) -> list[DiseaseYoga]:
    """Detect disease yogas 7-13: Both luminaries through Ketu."""
    yogas: list[DiseaseYoga] = []

    sun = chart.planets["Sun"]
    moon = chart.planets["Moon"]
    jupiter = chart.planets["Jupiter"]
    mercury = chart.planets["Mercury"]
    venus = chart.planets["Venus"]
    mars = chart.planets["Mars"]
    saturn = chart.planets["Saturn"]
    ketu = chart.planets["Ketu"]

    # -- 7. Both Luminaries Afflicted -----------------------------------------
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

    # -- 8. Jupiter Afflicted in 8th ------------------------------------------
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

    # -- 9. Mercury Heavily Afflicted -----------------------------------------
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

    # -- 10. Venus in 6th or 8th ----------------------------------------------
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

    # -- 11. 6th Lord in 8th or 12th ------------------------------------------
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

    # -- 12. Mars-Saturn Conjunction in Dusthana ------------------------------
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

    # -- 13. Ketu in 6th or 8th -----------------------------------------------
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
