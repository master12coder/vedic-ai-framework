"""Applicability checks for conditional nakshatra-based Dasha systems."""

from __future__ import annotations

from daivai_engine.constants import SIGN_LORDS
from daivai_engine.models.chart import ChartData


__all__ = [
    "is_ashtottari_applicable",
    "is_chaturaseeti_applicable",
    "is_dwadashottari_applicable",
    "is_dwisaptati_applicable",
    "is_panchottari_applicable",
    "is_shashtihayani_applicable",
    "is_shatabdika_applicable",
    "is_shatrimsha_applicable",
    "is_shodashottari_applicable",
]


def _lagna_navamsha_sign(chart: ChartData) -> int:
    """Compute the navamsha sign of the Lagna degree.

    Each navamsha spans 3°20' (1/9 of a sign). The navamsha sign is
    used to determine Vargottama Lagna (rashi sign == navamsha sign).

    Returns:
        Navamsha sign index (0-11).
    """
    navamsha_unit = 30.0 / 9.0  # 3.3333 degrees
    sign_navamsha_start = chart.lagna_sign_index * 9
    degree_in_sign = chart.lagna_longitude % 30.0
    navamsha_idx_in_sign = int(degree_in_sign / navamsha_unit)
    return (sign_navamsha_start + navamsha_idx_in_sign) % 12


def is_ashtottari_applicable(chart: ChartData) -> bool:
    """Check if Ashtottari Dasha applies (Rahu in kendra/trikona from Lagna lord).

    Kendra = houses 1, 4, 7, 10. Trikona = houses 1, 5, 9.
    Combined set = {1, 4, 5, 7, 9, 10}.

    Source: BPHS Ch.49.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)
    rahu = chart.planets.get("Rahu")
    if lord is None or rahu is None:
        return False
    # House of Rahu counted from the lagna lord's position
    rahu_from_lord = (rahu.sign_index - lord.sign_index) % 12 + 1
    kendra_trikona = {1, 4, 5, 7, 9, 10}
    return rahu_from_lord in kendra_trikona


def is_shodashottari_applicable(chart: ChartData) -> bool:
    """Check if Shodashottari Dasha applies (Krishna Paksha birth, Moon on Poorna Tithi).

    Krishna Paksha = waning moon (Sun-Moon longitude diff > 180°).
    Poorna Tithi = tithis 5, 10, 15, 20, 25, 30 (every fifth tithi).

    Source: BPHS Ch.49.
    """
    sun = chart.planets.get("Sun")
    moon = chart.planets.get("Moon")
    if sun is None or moon is None:
        return False

    # Tithi from elongation: Moon ahead of Sun by (tithi-1)*12 degrees
    elongation = (moon.longitude - sun.longitude) % 360.0
    tithi = int(elongation / 12.0) + 1  # 1-30

    # Krishna Paksha: tithis 16-30 (after full moon)
    krishna_paksha = tithi > 15

    # Poorna (complete) Tithi: divisible by 5
    poorna_tithi = tithi % 5 == 0

    return krishna_paksha and poorna_tithi


def is_dwisaptati_applicable(chart: ChartData) -> bool:
    """Check if Dwisaptati Sama Dasha applies.

    Condition: Lagna lord in 7th house OR 7th lord in Lagna (1st house).

    Source: BPHS Ch.50.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)

    # Condition 1: Lagna lord in 7th
    lagna_lord_in_7th = lord is not None and lord.house == 7

    # Condition 2: 7th lord in Lagna
    seventh_lord_name = SIGN_LORDS[(chart.lagna_sign_index + 6) % 12]
    seventh_lord = chart.planets.get(seventh_lord_name)
    seventh_lord_in_1st = seventh_lord is not None and seventh_lord.house == 1

    return lagna_lord_in_7th or seventh_lord_in_1st


def is_shatabdika_applicable(chart: ChartData) -> bool:
    """Check if Shatabdika Dasha applies (Lagna is in Vargottama — same sign in D1 and D9).

    A Vargottama Lagna means the Ascendant falls in the same sign in both
    the Rashi (D1) and Navamsha (D9) charts.

    Source: BPHS Ch.51.
    """
    navamsha_sign = _lagna_navamsha_sign(chart)
    return navamsha_sign == chart.lagna_sign_index


def is_chaturaseeti_applicable(chart: ChartData) -> bool:
    """Check if Chaturaseeti Sama Dasha applies (lagna lord in 10th house).

    Source: BPHS Ch.52.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)
    if lord is None:
        return False
    return lord.house == 10


def is_dwadashottari_applicable(chart: ChartData) -> bool:
    """Check if Dwadashottari Dasha applies (Venus in lagna / 1st house).

    Source: BPHS Ch.53.
    """
    venus = chart.planets.get("Venus")
    if venus is None:
        return False
    return venus.house == 1


def is_panchottari_applicable(chart: ChartData) -> bool:
    """Check if Panchottari Dasha applies (Moon in Dhanishtha nakshatra).

    Source: BPHS Ch.54. Dhanishtha = nakshatra index 23 (0-based).
    """
    moon = chart.planets.get("Moon")
    if moon is None:
        return False
    return moon.nakshatra_index == 23  # Dhanishtha


def is_shashtihayani_applicable(chart: ChartData) -> bool:
    """Check if Shashtihayani Dasha applies (Sun in lagna / 1st house).

    Source: BPHS Ch.55.
    """
    sun = chart.planets.get("Sun")
    if sun is None:
        return False
    return sun.house == 1


def is_shatrimsha_applicable(chart: ChartData) -> bool:
    """Check if Shatrimsha Sama Dasha applies (Mars in lagna / 1st house).

    Source: BPHS Ch.56.
    """
    mars = chart.planets.get("Mars")
    if mars is None:
        return False
    return mars.house == 1
