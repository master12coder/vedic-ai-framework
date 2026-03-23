"""Reference-lagna chart analysis — Chandra Kundali and Surya Kundali.

Re-maps house numbers and lordships from Moon's or Sun's sign as the
first house, providing a complementary perspective to the Rasi chart.

Source: BPHS (throughout), Uttarakalamrita, Phaladeepika.
"""

from __future__ import annotations

from daivai_engine.constants import (
    DUSTHANAS,
    KENDRAS,
    NUM_SIGNS,
    PLANETS,
    SIGN_LORDS,
    SIGNS_EN,
    TRIKONAS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.reference_chart import (
    ReferenceChartAnalysis,
    ReferenceHouse,
    ReferencePlanetPosition,
)


def _house_from_ref(sign_index: int, ref_sign_index: int) -> int:
    """Compute house number (1-12) of a sign relative to a reference sign.

    Args:
        sign_index: The sign index (0-11) of the planet or house cusp.
        ref_sign_index: The sign index (0-11) used as house 1.

    Returns:
        House number 1-12.
    """
    return ((sign_index - ref_sign_index) % NUM_SIGNS) + 1


def _find_yogakaraka(ref_sign_index: int) -> str | None:
    """Identify the yogakaraka planet from the reference lagna.

    Yogakaraka = a single planet that lords over both a kendra (4,7,10 — not 1)
    and a trikona (5,9 — not 1). House 1 is excluded since it is both kendra
    and trikona, and would create a false positive for any lagna lord.

    Args:
        ref_sign_index: Sign index used as house 1.

    Returns:
        Planet name if a yogakaraka exists, else None.

    Source: BPHS Ch.34, Phaladeepika Ch.7 — definition of yogakaraka.
    """
    # Kendra lords (houses 4, 7, 10 — exclude 1)
    kendra_lords: set[str] = set()
    for h in [4, 7, 10]:
        si = (ref_sign_index + h - 1) % NUM_SIGNS
        kendra_lords.add(SIGN_LORDS[si])

    # Trikona lords (houses 5, 9 — exclude 1)
    trikona_lords: set[str] = set()
    for h in [5, 9]:
        si = (ref_sign_index + h - 1) % NUM_SIGNS
        trikona_lords.add(SIGN_LORDS[si])

    overlap = kendra_lords & trikona_lords
    if overlap:
        # Return the first match (deterministic via sorted)
        return sorted(overlap)[0]
    return None


def compute_reference_chart(
    chart: ChartData,
    reference: str = "Moon",
) -> ReferenceChartAnalysis:
    """Analyse the chart with Moon's or Sun's sign as lagna.

    Re-maps all 12 houses, planet positions, and derives key insights
    (yogakaraka, kendra/trikona/dusthana occupants) from the reference
    planet's perspective.

    Args:
        chart: Natal ChartData.
        reference: "Moon" or "Sun".

    Returns:
        ReferenceChartAnalysis with full house/planet mapping.

    Source: BPHS — Chandra Kundali is used throughout for confirming
    Rasi-chart indications. Phaladeepika — Surya Kundali for career
    and public life.
    """
    if reference not in ("Moon", "Sun"):
        msg = f"reference must be 'Moon' or 'Sun', got '{reference}'"
        raise ValueError(msg)

    ref_planet = chart.planets[reference]
    ref_sign_index = ref_planet.sign_index

    # ── Build 12 houses ──────────────────────────────────────────────────
    houses: list[ReferenceHouse] = []
    for h in range(1, 13):
        si = (ref_sign_index + h - 1) % NUM_SIGNS
        lord = SIGN_LORDS[si]

        # Find which ref-house the lord sits in
        if lord in chart.planets:
            lord_si = chart.planets[lord].sign_index
            lord_ref_house = _house_from_ref(lord_si, ref_sign_index)
        else:
            lord_ref_house = h  # fallback

        # Planets occupying this house
        occupants: list[str] = []
        for pname in PLANETS:
            if pname in chart.planets:
                pd = chart.planets[pname]
                if _house_from_ref(pd.sign_index, ref_sign_index) == h:
                    occupants.append(pname)

        houses.append(
            ReferenceHouse(
                house_number=h,
                sign_index=si,
                sign=SIGNS_EN[si],
                lord=lord,
                lord_ref_house=lord_ref_house,
                planets=occupants,
            )
        )

    # ── Map planet positions ─────────────────────────────────────────────
    planet_positions: dict[str, ReferencePlanetPosition] = {}
    planets_in_kendras: list[str] = []
    planets_in_trikonas: list[str] = []
    planets_in_dusthanas: list[str] = []

    for pname in PLANETS:
        if pname not in chart.planets:
            continue
        pd = chart.planets[pname]
        ref_h = _house_from_ref(pd.sign_index, ref_sign_index)
        is_kendra = ref_h in KENDRAS
        is_trikona = ref_h in TRIKONAS
        is_dusthana = ref_h in DUSTHANAS

        planet_positions[pname] = ReferencePlanetPosition(
            planet=pname,
            ref_house=ref_h,
            sign_index=pd.sign_index,
            sign=SIGNS_EN[pd.sign_index],
            dignity=pd.dignity,
            is_ref_kendra=is_kendra,
            is_ref_trikona=is_trikona,
            is_ref_dusthana=is_dusthana,
        )

        if is_kendra:
            planets_in_kendras.append(pname)
        if is_trikona:
            planets_in_trikonas.append(pname)
        if is_dusthana:
            planets_in_dusthanas.append(pname)

    # ── Derived insights ─────────────────────────────────────────────────
    ref_lagna_lord = SIGN_LORDS[ref_sign_index]
    ref_lagna_lord_house = (
        _house_from_ref(chart.planets[ref_lagna_lord].sign_index, ref_sign_index)
        if ref_lagna_lord in chart.planets
        else 1
    )

    yogakaraka = _find_yogakaraka(ref_sign_index)

    # ── Summary ──────────────────────────────────────────────────────────
    summary_parts: list[str] = [
        f"{reference} Kundali: {SIGNS_EN[ref_sign_index]} as 1st house.",
        f"Lagna lord {ref_lagna_lord} in house {ref_lagna_lord_house}.",
    ]
    if yogakaraka:
        yk_house = planet_positions[yogakaraka].ref_house if yogakaraka in planet_positions else "?"
        summary_parts.append(f"Yogakaraka {yogakaraka} in house {yk_house}.")
    if planets_in_kendras:
        summary_parts.append(f"Kendra planets: {', '.join(planets_in_kendras)}.")
    if planets_in_dusthanas:
        summary_parts.append(f"Dusthana planets: {', '.join(planets_in_dusthanas)}.")

    return ReferenceChartAnalysis(
        reference_planet=reference,
        reference_sign_index=ref_sign_index,
        reference_sign=SIGNS_EN[ref_sign_index],
        houses=houses,
        planet_positions=planet_positions,
        ref_lagna_lord=ref_lagna_lord,
        ref_lagna_lord_house=ref_lagna_lord_house,
        yogakaraka_from_ref=yogakaraka,
        planets_in_kendras=planets_in_kendras,
        planets_in_trikonas=planets_in_trikonas,
        planets_in_dusthanas=planets_in_dusthanas,
        summary=" ".join(summary_parts),
    )


def compute_chandra_kundali(chart: ChartData) -> ReferenceChartAnalysis:
    """Analyse chart from Moon's sign as lagna (Chandra Kundali).

    Convenience wrapper around compute_reference_chart.

    Args:
        chart: Natal ChartData.

    Returns:
        ReferenceChartAnalysis with Moon as reference.

    Source: BPHS — Chandra Kundali for mental/emotional analysis.
    """
    return compute_reference_chart(chart, "Moon")


def compute_surya_kundali(chart: ChartData) -> ReferenceChartAnalysis:
    """Analyse chart from Sun's sign as lagna (Surya Kundali).

    Convenience wrapper around compute_reference_chart.

    Args:
        chart: Natal ChartData.

    Returns:
        ReferenceChartAnalysis with Sun as reference.

    Source: Phaladeepika — Surya Kundali for career and authority analysis.
    """
    return compute_reference_chart(chart, "Sun")
