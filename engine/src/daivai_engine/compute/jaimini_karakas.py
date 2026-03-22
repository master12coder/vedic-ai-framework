"""Jaimini Chara Karaka computation."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.models.jaimini import CharaKaraka


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
