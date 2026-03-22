"""Applicability checks for conditional nakshatra-based Dasha systems."""

from __future__ import annotations

from daivai_engine.constants import SIGN_LORDS
from daivai_engine.models.chart import ChartData


def is_dwisaptati_applicable(chart: ChartData) -> bool:
    """Check if Dwisaptati Sama Dasha applies (lagna lord in 7th house).

    Source: BPHS Ch.50.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)
    if lord is None:
        return False
    return lord.house == 7


def is_shatabdika_applicable(chart: ChartData) -> bool:
    """Check if Shatabdika Dasha applies (lagna lord in lagna / 1st house).

    Source: BPHS Ch.51.
    """
    lord_name = SIGN_LORDS[chart.lagna_sign_index]
    lord = chart.planets.get(lord_name)
    if lord is None:
        return False
    return lord.house == 1


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
    """Check if Panchottari Dasha applies (Cancer lagna AND Moon in lagna).

    Source: BPHS Ch.54.
    """
    if chart.lagna_sign_index != 3:  # 3 = Karka (Cancer)
        return False
    moon = chart.planets.get("Moon")
    if moon is None:
        return False
    return moon.house == 1


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
