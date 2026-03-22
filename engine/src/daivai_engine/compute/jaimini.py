"""Jaimini astrology system — orchestrator.

Jaimini is a distinct system within Vedic astrology that uses sign-based
aspects, movable (chara) planetary significators, and Arudha Padas for
prediction. This module integrates Chara Karakas, Rasi aspects, and Arudha Padas.

References:
    - Jaimini Sutras (Upadesha Sutras)
    - B.V. Raman, Studies in Jaimini Astrology
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.jaimini_karakas import (
    CHARA_KARAKA_PLANETS,
    KARAKA_FULL_NAMES,
    KARAKA_HINDI_NAMES,
    KARAKA_NAMES,
    compute_chara_karakas,
)
from daivai_engine.compute.jaimini_padas import (
    compute_arudha_padas,
    compute_karakamsha,
)
from daivai_engine.compute.jaimini_rasi import (
    DUAL_SIGNS,
    FIXED_SIGNS,
    MOVABLE_SIGNS,
    get_jaimini_aspects,
)
from daivai_engine.constants import SIGN_LORDS, SIGNS
from daivai_engine.models.jaimini import ArudhaPada, CharaKaraka, JaiminiRajYoga, JaiminiResult


__all__ = [
    "ARUDHA_EXCEPTION_OFFSET",
    "CHARA_KARAKA_PLANETS",
    "DUAL_SIGNS",
    "FIXED_SIGNS",
    "KARAKA_FULL_NAMES",
    "KARAKA_HINDI_NAMES",
    "KARAKA_NAMES",
    "MOVABLE_SIGNS",
    "NUM_HOUSES",
    "NUM_SIGNS",
    "compute_arudha_padas",
    "compute_chara_karakas",
    "compute_jaimini",
    "compute_karakamsha",
    "detect_jaimini_raj_yogas",
    "get_jaimini_aspects",
]

# Keep for backward compatibility
NUM_SIGNS: int = 12
ARUDHA_EXCEPTION_OFFSET: int = 9
NUM_HOUSES: int = 12


def compute_jaimini(chart: ChartData) -> JaiminiResult:
    """Compute the complete Jaimini analysis for a birth chart.

    Combines Chara Karakas, Arudha Padas, Karakamsha, and Raj Yogas
    into a single comprehensive result.

    Args:
        chart: Computed birth chart with planetary positions.

    Returns:
        JaiminiResult with all Jaimini calculations.
    """
    karakas = compute_chara_karakas(chart)
    padas = compute_arudha_padas(chart)
    karakamsha_sign_index = compute_karakamsha(chart)
    raj_yogas = detect_jaimini_raj_yogas(chart, karakas, padas)

    return JaiminiResult(
        chara_karakas=karakas,
        arudha_padas=padas,
        karakamsha_sign_index=karakamsha_sign_index,
        karakamsha_sign=SIGNS[karakamsha_sign_index],
        atmakaraka=karakas[0].planet,
        darakaraka=karakas[-1].planet,
        raj_yogas=raj_yogas,
    )


def detect_jaimini_raj_yogas(
    chart: ChartData,
    karakas: list[CharaKaraka],
    padas: list[ArudhaPada],
) -> list[JaiminiRajYoga]:
    """Detect Jaimini Raj Yogas in the birth chart.

    Classical Jaimini Raj Yogas (Upadesha Sutras + B.V. Raman):

    1. AK-AmK Yoga: Atmakaraka and Amatyakaraka in mutual sign aspect
       or conjunct — most powerful Raj Yoga (authority + career success).

    2. Karakamsha Raj Yoga: Exalted planet or benefic in Karakamsha sign
       — prominence in the native's soul-directed career.

    3. Arudha Lagna (AL) Yoga: AL (A1) lord in kendra from AL or in
       Karakamsha — public recognition and worldly rise.

    4. Darakaraka in 7th from AK: Favorable for marriage and partnerships.

    5. AmK in Kendra from AK: Career success, rise through position.

    6. Benefic in Arudha Lagna (A1): Public image is strong and
       respected — Raj Yoga from worldly standing.

    Source: Jaimini Upadesha Sutras 1.3-1.4, B.V. Raman.

    Args:
        chart: Birth chart.
        karakas: Pre-computed Chara Karakas.
        padas: Pre-computed Arudha Padas.

    Returns:
        List of detected JaiminiRajYoga objects (present and absent).
    """
    yogas: list[JaiminiRajYoga] = []

    # Build quick lookups
    karaka_map: dict[str, str] = {k.karaka: k.planet for k in karakas}
    ak_planet = karaka_map.get("AK", "")
    amk_planet = karaka_map.get("AmK", "")
    dk_planet = karaka_map.get("DK", "")

    ak_sign = chart.planets[ak_planet].sign_index if ak_planet else -1
    amk_sign = chart.planets[amk_planet].sign_index if amk_planet else -1

    # Arudha Lagna sign (A1)
    al_sign = padas[0].sign_index if padas else -1

    # Karakamsha sign
    karakamsha = compute_karakamsha(chart)

    # ── Yoga 1: AK-AmK Yoga (conjunction or mutual Jaimini aspect) ──────────
    ak_amk_conjunct = ak_sign == amk_sign
    ak_amk_mutual_aspect = (
        ak_sign != amk_sign
        and amk_sign in get_jaimini_aspects(ak_sign)
        and ak_sign in get_jaimini_aspects(amk_sign)
    )
    ak_amk_present = ak_amk_conjunct or ak_amk_mutual_aspect

    yogas.append(
        JaiminiRajYoga(
            name="AK-AmK Yoga",
            name_hi="आत्मकारक-अमात्यकारक योग",
            is_present=ak_amk_present,
            description=(
                f"{ak_planet} (AK) and {amk_planet} (AmK) are "
                f"{'conjunct' if ak_amk_conjunct else 'in mutual sign aspect'} — "
                "supreme Raj Yoga indicating authority, career success, and recognition."
                if ak_amk_present
                else f"{ak_planet} (AK) and {amk_planet} (AmK) are not in mutual aspect."
            ),
            planets_involved=[ak_planet, amk_planet],
            strength="strong" if ak_amk_conjunct else ("moderate" if ak_amk_present else "none"),
        )
    )

    # ── Yoga 2: Karakamsha Yoga (exalted/own planet in Karakamsha) ──────────
    karakamsha_planets = [
        name
        for name, p in chart.planets.items()
        if p.sign_index == karakamsha
        and p.dignity in ("exalted", "own", "mooltrikona")
        and name not in ("Rahu", "Ketu")
    ]
    karakamsha_yoga_present = len(karakamsha_planets) > 0

    yogas.append(
        JaiminiRajYoga(
            name="Karakamsha Raj Yoga",
            name_hi="कारकांश राज योग",
            is_present=karakamsha_yoga_present,
            description=(
                f"Strong planet(s) {', '.join(karakamsha_planets)} in Karakamsha "
                f"({SIGNS[karakamsha]}) — prominence in soul-directed vocation."
                if karakamsha_yoga_present
                else f"No strong planet in Karakamsha ({SIGNS[karakamsha]})."
            ),
            planets_involved=karakamsha_planets,
            strength="strong" if karakamsha_yoga_present else "none",
        )
    )

    # ── Yoga 3: Arudha Lagna Yoga (AL lord in kendra from AL) ───────────────
    if al_sign >= 0:
        al_lord_name = SIGN_LORDS[al_sign]
        al_lord_sign = chart.planets[al_lord_name].sign_index
        dist_from_al = ((al_lord_sign - al_sign) % 12) + 1
        al_lord_in_kendra = dist_from_al in (1, 4, 7, 10)
        al_lord_in_karakamsha = al_lord_sign == karakamsha

        al_yoga_present = al_lord_in_kendra or al_lord_in_karakamsha
        yogas.append(
            JaiminiRajYoga(
                name="Arudha Lagna Yoga",
                name_hi="आरूढ लग्न योग",
                is_present=al_yoga_present,
                description=(
                    f"AL lord {al_lord_name} is "
                    f"{'in kendra from AL' if al_lord_in_kendra else 'in Karakamsha'} — "
                    "public recognition and worldly rise."
                    if al_yoga_present
                    else f"AL lord {al_lord_name} is not in kendra from AL."
                ),
                planets_involved=[al_lord_name],
                strength="moderate" if al_yoga_present else "none",
            )
        )

    # ── Yoga 4: AmK in Kendra from AK ───────────────────────────────────────
    if ak_sign >= 0 and amk_sign >= 0:
        dist_amk_from_ak = ((amk_sign - ak_sign) % 12) + 1
        amk_kendra_from_ak = dist_amk_from_ak in (1, 4, 7, 10)
        yogas.append(
            JaiminiRajYoga(
                name="AmK in Kendra from AK",
                name_hi="अमात्यकारक केंद्र योग",
                is_present=amk_kendra_from_ak,
                description=(
                    f"{amk_planet} (AmK) in house {dist_amk_from_ak} from AK — "
                    "career success and rise through professional position."
                    if amk_kendra_from_ak
                    else f"{amk_planet} (AmK) is not in kendra from {ak_planet} (AK)."
                ),
                planets_involved=[ak_planet, amk_planet],
                strength="moderate" if amk_kendra_from_ak else "none",
            )
        )

    # ── Yoga 5: Benefic in Arudha Lagna (A1) ────────────────────────────────
    benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
    if al_sign >= 0:
        benefics_in_al = [
            name
            for name, p in chart.planets.items()
            if p.sign_index == al_sign and name in benefics
        ]
        benefic_al_yoga = len(benefics_in_al) > 0
        yogas.append(
            JaiminiRajYoga(
                name="Benefic in Arudha Lagna",
                name_hi="आरूढ लग्न शुभ ग्रह योग",
                is_present=benefic_al_yoga,
                description=(
                    f"Benefic(s) {', '.join(benefics_in_al)} in Arudha Lagna "
                    f"({SIGNS[al_sign]}) — strong public image and social recognition."
                    if benefic_al_yoga
                    else f"No benefic in Arudha Lagna ({SIGNS[al_sign]})."
                ),
                planets_involved=benefics_in_al,
                strength="moderate" if benefic_al_yoga else "none",
            )
        )

    # ── Yoga 6: DK in 7th from AK ───────────────────────────────────────────
    if ak_planet and dk_planet:
        dk_sign = chart.planets[dk_planet].sign_index
        dist_dk_from_ak = ((dk_sign - ak_sign) % 12) + 1
        dk_7th_from_ak = dist_dk_from_ak == 7
        yogas.append(
            JaiminiRajYoga(
                name="DK in 7th from AK",
                name_hi="दारकारक सप्तम योग",
                is_present=dk_7th_from_ak,
                description=(
                    f"{dk_planet} (DK) in 7th from {ak_planet} (AK) — "
                    "favorable for marriage and long-term partnerships."
                    if dk_7th_from_ak
                    else f"{dk_planet} (DK) is in house {dist_dk_from_ak} from AK (not 7th)."
                ),
                planets_involved=[ak_planet, dk_planet],
                strength="moderate" if dk_7th_from_ak else "none",
            )
        )

    return yogas
