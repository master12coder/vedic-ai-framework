"""Jaimini Arudha Padas and Karakamsha computation."""

from __future__ import annotations

from daivai_engine.compute.chart import ChartData
from daivai_engine.compute.divisional import compute_navamsha_sign
from daivai_engine.compute.jaimini_karakas import compute_chara_karakas
from daivai_engine.constants import SIGN_LORDS, SIGNS
from daivai_engine.models.jaimini import ArudhaPada


# Arudha special-case offsets: houses 1 and 7 trigger the 10th-house exception
ARUDHA_EXCEPTION_OFFSET: int = 9  # 10th house = 9 signs forward (0-indexed)

# Number of houses
NUM_HOUSES: int = 12

# Number of signs in the zodiac
NUM_SIGNS: int = 12


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
