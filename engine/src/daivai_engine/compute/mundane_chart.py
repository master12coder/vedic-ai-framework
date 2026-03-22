"""Mundane Astrology — country/foundation chart analysis and disaster yoga detection.

Applies Brihat Samhita disaster yogas, mundane house significations,
and identifies afflicted/benefic houses and dominant planets.

Sources: Brihat Samhita (Varahamihira), BPHS Ch.71-75.
"""

from __future__ import annotations

import logging

import swisseph as swe

from daivai_engine.constants import (
    FULL_CIRCLE_DEG,
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    SIGN_LORDS,
    SIGNS,
    SWE_PLANETS,
)
from daivai_engine.knowledge.loader import load_mundane_rules
from daivai_engine.models.chart import ChartData
from daivai_engine.models.mundane import DisasterYoga, MundaneChartAnalysis


logger = logging.getLogger(__name__)

# Nakshatra span in degrees
_NAK_SPAN = FULL_CIRCLE_DEG / 27  # 13.333...°
_MAX_NAK_IDX = 26

# Planet names mapped to Swiss Ephemeris IDs for mundane use
_MUNDANE_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Dusthana houses (malefic houses in mundane charts)
_DUSTHANAS = {6, 8, 12}

# Malefic planets for mundane analysis
_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu"}

# Benefic planets
_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}


def _get_nakshatra(longitude: float) -> tuple[int, str, str]:
    """Return (index, name, lord) for a sidereal longitude."""
    idx = min(int(longitude / _NAK_SPAN), _MAX_NAK_IDX)
    name = NAKSHATRAS[idx]
    lord = NAKSHATRA_LORDS[idx]
    return idx, name, lord


def _longitude_to_sign(longitude: float) -> tuple[int, str]:
    """Return (sign_index, sign_name) from sidereal longitude."""
    sign_idx = int(longitude / 30) % 12
    return sign_idx, SIGNS[sign_idx]


def _get_planet_longitude(jd: float, planet_name: str) -> float:
    """Compute sidereal longitude of a planet at Julian Day."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    swe_id = SWE_PLANETS.get(planet_name)
    if swe_id is None:
        raise ValueError(f"Unknown planet for mundane: {planet_name}")
    result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL)
    return float(result[0][0]) % FULL_CIRCLE_DEG


def _house_from_lagna(planet_sign_idx: int, lagna_sign_idx: int) -> int:
    """Compute house number (1-12) of a planet given lagna sign index."""
    return ((planet_sign_idx - lagna_sign_idx) % 12) + 1


def analyze_mundane_chart(
    chart: ChartData,
    country: str | None = None,
    chart_type: str = "country_foundation",
) -> MundaneChartAnalysis:
    """Analyze a chart for mundane (national/world) predictions.

    Applies Brihat Samhita disaster yogas, mundane house significations,
    and identifies afflicted/benefic houses and dominant planets.

    Args:
        chart: A ChartData object (foundation chart, ingress chart, etc.).
        country: Optional country name for context.
        chart_type: Type of mundane chart being analyzed.

    Returns:
        MundaneChartAnalysis with house predictions, disaster yogas, and severity score.
    """
    rules = load_mundane_rules()
    house_sigs: dict = rules.get("house_significations", {})

    lagna_idx = chart.lagna_sign_index
    lagna_sign = chart.lagna_sign
    lagna_lord = SIGN_LORDS[lagna_idx]

    # Map each planet to its mundane house
    planet_houses: dict[str, int] = {}
    for pname, pdata in chart.planets.items():
        planet_houses[pname] = _house_from_lagna(pdata.sign_index, lagna_idx)

    # House analysis: gather significations for occupied/afflicted houses
    house_analysis: dict[int, list[str]] = {}
    afflicted_houses: list[int] = []
    benefic_houses: list[int] = []

    for house in range(1, 13):
        occupants = [p for p, h in planet_houses.items() if h == house]
        malefic_occupants = [p for p in occupants if p in _MALEFICS]
        benefic_occupants = [p for p in occupants if p in _BENEFICS]

        sig_data = house_sigs.get(house, {})
        domain_rules: list[str] = sig_data.get("rules", [])
        predictions: list[str] = []

        if malefic_occupants:
            for rule in domain_rules[:2]:  # top 2 domains
                predictions.append(
                    f"Stress in: {rule} (afflicted by {', '.join(malefic_occupants)})"
                )
            afflicted_houses.append(house)
        elif benefic_occupants:
            for rule in domain_rules[:2]:
                predictions.append(
                    f"Prosperity in: {rule} (supported by {', '.join(benefic_occupants)})"
                )
            benefic_houses.append(house)

        if predictions:
            house_analysis[house] = predictions

    # Detect disaster yogas
    disaster_yogas = _detect_disaster_yogas(chart, planet_houses, rules)

    # Dominant and weak planets by speed and dignity
    dominant_planets = [
        p
        for p, d in chart.planets.items()
        if d.dignity in ("exalted", "own", "mooltrikona") and not d.is_combust
    ]
    weak_planets = [
        p for p, d in chart.planets.items() if d.dignity == "debilitated" or d.is_combust
    ]

    # Severity score: 0-10 based on number of disaster yogas and afflictions
    severity = min(10.0, len(disaster_yogas) * 2.0 + len(afflicted_houses) * 0.5)

    # Generate overall predictions
    all_predictions: list[str] = []
    for yoga in disaster_yogas:
        all_predictions.append(f"{yoga.name}: {yoga.description}")
    for _house, preds in house_analysis.items():
        all_predictions.extend(preds)

    return MundaneChartAnalysis(
        chart_type=chart_type,
        chart_date=chart.dob,
        country=country,
        lagna_sign=lagna_sign,
        lagna_lord=lagna_lord,
        house_analysis=house_analysis,
        disaster_yogas=disaster_yogas,
        afflicted_houses=sorted(set(afflicted_houses)),
        benefic_houses=sorted(set(benefic_houses)),
        dominant_planets=dominant_planets,
        weak_planets=weak_planets,
        predictions=all_predictions,
        severity_score=severity,
    )


def _detect_disaster_yogas(
    chart: ChartData,
    planet_houses: dict[str, int],
    rules: dict,
) -> list[DisasterYoga]:
    """Detect Brihat Samhita disaster yogas in a mundane chart."""
    yogas: list[DisasterYoga] = []
    yoga_defs: list[dict] = rules.get("disaster_yogas", [])
    lagna_idx = chart.lagna_sign_index

    for defn in yoga_defs:
        condition = defn.get("condition", "")
        planets_involved: list[str] = []
        matched = False

        match condition:
            case "malefics_in_lagna_of_ingress":
                malefics_in_1 = [p for p, h in planet_houses.items() if h == 1 and p in _MALEFICS]
                if malefics_in_1:
                    matched = True
                    planets_involved = malefics_in_1

            case "moon_conjunct_malefic_in_4th":
                moon_house = planet_houses.get("Moon")
                if moon_house == 4:
                    malefics_in_4 = [
                        p for p, h in planet_houses.items() if h == 4 and p in _MALEFICS
                    ]
                    if malefics_in_4:
                        matched = True
                        planets_involved = ["Moon", *malefics_in_4]

            case "8th_lord_in_lagna_conjunct_malefic":
                eighth_sign_idx = (lagna_idx + 7) % 12
                eighth_lord = SIGN_LORDS[eighth_sign_idx]
                eighth_lord_house = planet_houses.get(eighth_lord)
                if eighth_lord_house == 1:
                    malefics_in_1 = [
                        p for p, h in planet_houses.items() if h == 1 and p in _MALEFICS
                    ]
                    if malefics_in_1:
                        matched = True
                        planets_involved = [eighth_lord, *malefics_in_1]

            case "6th_lord_in_10th_or_7th":
                sixth_sign_idx = (lagna_idx + 5) % 12
                sixth_lord = SIGN_LORDS[sixth_sign_idx]
                sixth_lord_house = planet_houses.get(sixth_lord)
                if sixth_lord_house in (7, 10):
                    matched = True
                    planets_involved = [sixth_lord]

            case "6th_lord_conjunct_moon_in_malefic_sign":
                sixth_sign_idx = (lagna_idx + 5) % 12
                sixth_lord = SIGN_LORDS[sixth_sign_idx]
                sixth_lord_house = planet_houses.get(sixth_lord)
                moon_house = planet_houses.get("Moon")
                if sixth_lord_house == moon_house and moon_house is not None:
                    moon_sign_idx = chart.planets["Moon"].sign_index
                    moon_sign_lord = SIGN_LORDS[moon_sign_idx]
                    if moon_sign_lord in _MALEFICS:
                        matched = True
                        planets_involved = [sixth_lord, "Moon"]

            case "2nd_and_11th_lords_afflicted_by_malefics":
                second_lord = SIGN_LORDS[(lagna_idx + 1) % 12]
                eleventh_lord = SIGN_LORDS[(lagna_idx + 10) % 12]
                second_house = planet_houses.get(second_lord)
                eleventh_house = planet_houses.get(eleventh_lord)
                malefic_houses = {h for p, h in planet_houses.items() if p in _MALEFICS}
                if second_house in malefic_houses or eleventh_house in malefic_houses:
                    matched = True
                    planets_involved = [second_lord, eleventh_lord]

            case "10th_lord_in_6th_8th_or_12th":
                tenth_sign_idx = (lagna_idx + 9) % 12
                tenth_lord = SIGN_LORDS[tenth_sign_idx]
                tenth_lord_house = planet_houses.get(tenth_lord)
                if tenth_lord_house in _DUSTHANAS:
                    matched = True
                    planets_involved = [tenth_lord]

            case "two_planets_within_1_degree":
                planet_list = list(chart.planets.items())
                for i in range(len(planet_list)):
                    for j in range(i + 1, len(planet_list)):
                        p1_name, p1 = planet_list[i]
                        p2_name, p2 = planet_list[j]
                        diff = abs(p1.longitude - p2.longitude)
                        if diff > 180:
                            diff = 360 - diff
                        if (
                            diff < 1.0
                            and p1_name not in ("Rahu", "Ketu")
                            and p2_name not in ("Rahu", "Ketu")
                        ):
                            matched = True
                            planets_involved = [p1_name, p2_name]
                            break
                    if matched:
                        break

        if matched:
            yogas.append(
                DisasterYoga(
                    name=defn["name"],
                    description=defn["description"],
                    severity=defn.get("severity", "moderate"),
                    affected_domains=defn.get("affected_domains", []),
                    planets_involved=planets_involved,
                    source=defn.get("source", "Brihat Samhita"),
                )
            )

    return yogas
