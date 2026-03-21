"""Jaimini astrology system — Chara Karakas, sign aspects, Arudha Padas, Karakamsha.

Jaimini is a distinct system within Vedic astrology that uses sign-based
aspects, movable (chara) planetary significators, and Arudha Padas for
prediction. This module implements the core Jaimini calculations.

References:
    - Jaimini Sutras (Upadesha Sutras)
    - B.V. Raman, Studies in Jaimini Astrology
"""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.divisional import compute_navamsha_sign
from daivai_engine.constants import SIGN_LORDS, SIGNS
from daivai_engine.models.jaimini import ArudhaPada, CharaKaraka, JaiminiRajYoga, JaiminiResult


# ── Constants ────────────────────────────────────────────────────────────────

# Planets eligible for Chara Karaka assignment (7-planet scheme, excluding nodes)
CHARA_KARAKA_PLANETS: list[str] = [
    "Sun",
    "Moon",
    "Mars",
    "Mercury",
    "Jupiter",
    "Venus",
    "Saturn",
]

# Karaka names in order from highest to lowest degree in sign
KARAKA_NAMES: list[str] = ["AK", "AmK", "BK", "MK", "PK", "GK", "DK"]

KARAKA_FULL_NAMES: list[str] = [
    "Atmakaraka",
    "Amatyakaraka",
    "Bhratrikaraka",
    "Matrikaraka",
    "Putrakaraka",
    "Gnatikaraka",
    "Darakaraka",
]

KARAKA_HINDI_NAMES: list[str] = [
    "आत्मकारक",
    "अमात्यकारक",
    "भ्रातृकारक",
    "मातृकारक",
    "पुत्रकारक",
    "ज्ञातिकारक",
    "दारकारक",
]

# Sign modalities (0-indexed sign → modality)
# Movable (Chara): Aries(0), Cancer(3), Libra(6), Capricorn(9)
# Fixed (Sthira): Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
# Dual (Dwiswabhava): Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
MOVABLE_SIGNS: set[int] = {0, 3, 6, 9}
FIXED_SIGNS: set[int] = {1, 4, 7, 10}
DUAL_SIGNS: set[int] = {2, 5, 8, 11}

# Number of signs in the zodiac
NUM_SIGNS: int = 12

# Arudha special-case offsets: houses 1 and 7 trigger the 10th-house exception
ARUDHA_EXCEPTION_OFFSET: int = 9  # 10th house = 9 signs forward (0-indexed)

# Number of houses
NUM_HOUSES: int = 12


# ── Chara Karakas ────────────────────────────────────────────────────────────


def compute_chara_karakas(chart: ChartData) -> list[CharaKaraka]:
    """Compute the 7 Chara Karakas based on planetary degrees within their signs.

    In the Jaimini system, each planet's degree within its sign determines
    its karaka status. The planet with the highest degree becomes
    Atmakaraka (soul significator), and so on in descending order.

    Uses the 7-karaka scheme (excluding Rahu and Ketu).

    Args:
        chart: Computed birth chart with planetary positions.

    Returns:
        List of 7 CharaKaraka objects, ordered from AK (highest degree) to
        DK (lowest degree).
    """
    # Collect planet name and degree-in-sign for eligible planets
    planet_degrees: list[tuple[str, float]] = []
    for planet_name in CHARA_KARAKA_PLANETS:
        planet_data = chart.planets[planet_name]
        planet_degrees.append((planet_name, planet_data.degree_in_sign))

    # Sort by degree in sign, descending (highest degree = Atmakaraka)
    planet_degrees.sort(key=lambda x: x[1], reverse=True)

    karakas: list[CharaKaraka] = []
    for i, (planet_name, degree) in enumerate(planet_degrees):
        karakas.append(
            CharaKaraka(
                karaka=KARAKA_NAMES[i],
                karaka_full=KARAKA_FULL_NAMES[i],
                karaka_hi=KARAKA_HINDI_NAMES[i],
                planet=planet_name,
                degree_in_sign=degree,
            )
        )

    return karakas


# ── Jaimini Sign Aspects ─────────────────────────────────────────────────────


def _get_sign_modality(sign_index: int) -> str:
    """Return the modality of a sign: 'movable', 'fixed', or 'dual'.

    Args:
        sign_index: Sign index (0-11).

    Returns:
        Modality string.
    """
    if sign_index in MOVABLE_SIGNS:
        return "movable"
    if sign_index in FIXED_SIGNS:
        return "fixed"
    return "dual"


def get_jaimini_aspects(sign_index: int) -> list[int]:
    """Compute which signs a given sign aspects in the Jaimini system.

    Jaimini aspects are sign-based (rashi drishti), not planet-based:
    - Movable signs aspect all fixed signs EXCEPT the one adjacent to them.
    - Fixed signs aspect all movable signs EXCEPT the one adjacent to them.
    - Dual signs aspect all other dual signs.

    Args:
        sign_index: The aspecting sign (0-11).

    Returns:
        List of sign indices (0-11) that are aspected.

    Raises:
        ValueError: If sign_index is not in range 0-11.
    """
    if not 0 <= sign_index < NUM_SIGNS:
        raise ValueError(f"Invalid sign index: {sign_index}. Must be 0-11.")

    modality = _get_sign_modality(sign_index)

    if modality == "movable":
        # Aspect all fixed signs except the adjacent one (next sign)
        adjacent_fixed = (sign_index + 1) % NUM_SIGNS
        return [s for s in FIXED_SIGNS if s != adjacent_fixed]

    if modality == "fixed":
        # Aspect all movable signs except the adjacent one (previous sign)
        adjacent_movable = (sign_index - 1) % NUM_SIGNS
        return [s for s in MOVABLE_SIGNS if s != adjacent_movable]

    # Dual signs aspect all other dual signs
    return [s for s in DUAL_SIGNS if s != sign_index]


# ── Arudha Padas ─────────────────────────────────────────────────────────────


def _sign_distance(from_sign: int, to_sign: int) -> int:
    """Count the number of signs from from_sign to to_sign (inclusive of to_sign).

    The count is 1-based: same sign = 1, next sign = 2, etc.

    Args:
        from_sign: Starting sign index (0-11).
        to_sign: Target sign index (0-11).

    Returns:
        Distance in signs (1-12).
    """
    return ((to_sign - from_sign) % NUM_SIGNS) + 1


def _compute_single_arudha(house_sign: int, lord_sign: int) -> int:
    """Compute the Arudha Pada sign for a single house.

    Algorithm:
    1. Count signs from house to its lord (inclusive) = N
    2. Count N signs from the lord = Arudha
    3. If Arudha falls in the same house or 7th from it, take 10th from house

    Args:
        house_sign: Sign index of the house (0-11).
        lord_sign: Sign index where the house lord is placed (0-11).

    Returns:
        Sign index of the Arudha Pada (0-11).
    """
    # Step 1: Count from house to lord
    distance = _sign_distance(house_sign, lord_sign)

    # Step 2: Count same distance from lord
    arudha_sign = (lord_sign + distance - 1) % NUM_SIGNS

    # Step 3: Exception — if arudha is the house itself or 7th from it
    seventh_from_house = (house_sign + 6) % NUM_SIGNS
    if arudha_sign in (house_sign, seventh_from_house):
        arudha_sign = (house_sign + ARUDHA_EXCEPTION_OFFSET) % NUM_SIGNS

    return arudha_sign


def compute_arudha_padas(chart: ChartData) -> list[ArudhaPada]:
    """Compute Arudha Padas (A1-A12) for all twelve houses.

    The Arudha Pada represents the worldly projection/image of a house.
    A1 (Arudha Lagna / Pada Lagna) is the most important, showing how
    the world perceives the native.

    Args:
        chart: Computed birth chart with planetary positions.

    Returns:
        List of 12 ArudhaPada objects (A1 through A12).
    """
    padas: list[ArudhaPada] = []

    for house_num in range(1, NUM_HOUSES + 1):
        # Sign of this house (whole-sign houses)
        house_sign = (chart.lagna_sign_index + house_num - 1) % NUM_SIGNS

        # Lord of this house
        lord_name = SIGN_LORDS[house_sign]

        # Sign where the lord is placed
        lord_sign = chart.planets[lord_name].sign_index

        # Compute arudha
        arudha_sign = _compute_single_arudha(house_sign, lord_sign)

        padas.append(
            ArudhaPada(
                house=house_num,
                name=f"A{house_num}",
                sign_index=arudha_sign,
                sign=SIGNS[arudha_sign],
            )
        )

    return padas


# ── Karakamsha ───────────────────────────────────────────────────────────────


def compute_karakamsha(chart: ChartData) -> int:
    """Compute the Karakamsha — the Navamsha sign of the Atmakaraka.

    The Karakamsha is pivotal in Jaimini astrology for determining
    the native's spiritual inclination, career, and life purpose.

    Args:
        chart: Computed birth chart with planetary positions.

    Returns:
        Sign index (0-11) of the Karakamsha.
    """
    # Find the Atmakaraka (planet with highest degree in sign)
    karakas = compute_chara_karakas(chart)
    atmakaraka_name = karakas[0].planet

    # Get Atmakaraka's longitude and compute its Navamsha sign
    ak_longitude = chart.planets[atmakaraka_name].longitude
    return compute_navamsha_sign(ak_longitude)


# ── Full Jaimini Analysis ────────────────────────────────────────────────────


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


# ── Jaimini Raj Yogas ────────────────────────────────────────────────────────


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
