"""Main chart computation — Swiss Ephemeris based sidereal chart engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import swisseph as swe

from jyotish.utils.constants import (
    SIGNS, SIGNS_EN, SIGNS_HI, PLANETS, PLANETS_HI, SWE_PLANETS,
    SIGN_LORDS, NAKSHATRAS, NAKSHATRA_LORDS, EXALTATION, DEBILITATION,
    OWN_SIGNS, MOOLTRIKONA, COMBUSTION_LIMITS, COMBUSTION_LIMITS_RETROGRADE,
    AVASTHAS, SPECIAL_ASPECTS,
    NUM_NAKSHATRAS, MAX_NAKSHATRA_INDEX, NAKSHATRA_SPAN_DEG,
    PADAS_PER_NAKSHATRA, HALF_CIRCLE_DEG, FULL_CIRCLE_DEG,
    DEFAULT_CONJUNCTION_ORB,
)
from jyotish.utils.datetime_utils import to_jd, parse_birth_datetime
from jyotish.utils.geo import resolve_or_manual, GeoLocation

from jyotish.domain.models.chart import PlanetData, ChartData


def get_nakshatra(lon: float) -> tuple[int, int]:
    """Return (nakshatra_index, pada) from sidereal longitude."""
    nak_index = int(lon / NAKSHATRA_SPAN_DEG)
    if nak_index > MAX_NAKSHATRA_INDEX:
        nak_index = MAX_NAKSHATRA_INDEX
    degree_in_nak = lon - nak_index * NAKSHATRA_SPAN_DEG
    pada = int(degree_in_nak / (NAKSHATRA_SPAN_DEG / PADAS_PER_NAKSHATRA)) + 1
    if pada > PADAS_PER_NAKSHATRA:
        pada = PADAS_PER_NAKSHATRA
    return nak_index, pada


def _get_dignity(planet: str, sign_index: int, degree_in_sign: float) -> str:
    """Determine planet's dignity in a sign."""
    if planet in EXALTATION and EXALTATION[planet] == sign_index:
        return "exalted"
    if planet in DEBILITATION and DEBILITATION[planet] == sign_index:
        return "debilitated"
    if planet in MOOLTRIKONA:
        mt_sign, mt_start, mt_end = MOOLTRIKONA[planet]
        if sign_index == mt_sign and mt_start <= degree_in_sign <= mt_end:
            return "mooltrikona"
    if planet in OWN_SIGNS and sign_index in OWN_SIGNS[planet]:
        return "own"
    return "neutral"


def _get_avastha(degree_in_sign: float, sign_index: int) -> str:
    """Determine planetary age state based on degree in sign."""
    # Odd signs: 0-6 Bala, 6-12 Kumara, 12-18 Yuva, 18-24 Vriddha, 24-30 Mruta
    # Even signs: reversed
    segment = int(degree_in_sign / 6.0)
    if segment > 4:
        segment = 4
    if sign_index % 2 == 0:  # Odd signs (0-indexed even = 1st,3rd,5th... signs)
        return AVASTHAS[segment]
    else:  # Even signs — reverse
        return AVASTHAS[4 - segment]


def _check_combustion(planet: str, planet_lon: float, sun_lon: float, is_retro: bool) -> bool:
    """Check if planet is combust (too close to Sun)."""
    if planet in ("Sun", "Rahu", "Ketu"):
        return False
    limit = COMBUSTION_LIMITS.get(planet)
    if limit is None:
        return False
    if is_retro and planet in COMBUSTION_LIMITS_RETROGRADE:
        limit = COMBUSTION_LIMITS_RETROGRADE[planet]
    diff = abs(planet_lon - sun_lon)
    if diff > 180:
        diff = 360 - diff
    return diff < limit


def _house_from_lagna(planet_sign: int, lagna_sign: int) -> int:
    """Calculate house number (1-12) from lagna sign (whole sign houses)."""
    return ((planet_sign - lagna_sign) % 12) + 1


def compute_chart(
    name: str,
    dob: str,
    tob: str,
    place: str | None = None,
    gender: str = "Male",
    lat: float | None = None,
    lon: float | None = None,
    tz_name: str = "Asia/Kolkata",
) -> ChartData:
    """Compute a complete Vedic birth chart.

    Args:
        name: Full name
        dob: Date of birth as DD/MM/YYYY
        tob: Time of birth as HH:MM
        place: Place name (geocoded automatically)
        gender: Male/Female
        lat: Manual latitude (if place not given)
        lon: Manual longitude (if place not given)
        tz_name: Timezone name (if using manual coordinates)
    """
    # Resolve location
    geo = resolve_or_manual(place=place, lat=lat, lon=lon, tz_name=tz_name)

    # Parse datetime and compute Julian Day
    birth_dt = parse_birth_datetime(dob, tob, geo.timezone_name)
    jd = to_jd(birth_dt)

    # Set Lahiri ayanamsha
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsha = swe.get_ayanamsa(jd)

    # Compute Lagna (Ascendant)
    cusps, ascmc = swe.houses_ex(jd, geo.latitude, geo.longitude, b"W")
    lagna_tropical = ascmc[0]
    lagna_sidereal = (lagna_tropical - ayanamsha) % 360.0
    lagna_sign_index = int(lagna_sidereal / 30.0)
    lagna_degree = lagna_sidereal - lagna_sign_index * 30.0

    chart = ChartData(
        name=name,
        dob=dob,
        tob=tob,
        place=place or f"{geo.latitude},{geo.longitude}",
        gender=gender,
        latitude=geo.latitude,
        longitude=geo.longitude,
        timezone_name=geo.timezone_name,
        julian_day=jd,
        ayanamsha=ayanamsha,
        lagna_longitude=lagna_sidereal,
        lagna_sign_index=lagna_sign_index,
        lagna_sign=SIGNS[lagna_sign_index],
        lagna_sign_en=SIGNS_EN[lagna_sign_index],
        lagna_sign_hi=SIGNS_HI[lagna_sign_index],
        lagna_degree=lagna_degree,
    )

    # Compute Sun first (needed for combustion check)
    sun_result = swe.calc_ut(jd, SWE_PLANETS["Sun"], swe.FLG_SIDEREAL | swe.FLG_SPEED)
    sun_lon = sun_result[0][0]

    # Compute all planets
    for i, planet_name in enumerate(PLANETS):
        if planet_name == "Ketu":
            # Ketu is always 180° from Rahu
            rahu_data = chart.planets["Rahu"]
            ketu_lon = (rahu_data.longitude + HALF_CIRCLE_DEG) % FULL_CIRCLE_DEG
            sign_index = int(ketu_lon / 30.0)
            degree_in_sign = ketu_lon - sign_index * 30.0
            nak_index, pada = get_nakshatra(ketu_lon)
            planet_data = PlanetData(
                name="Ketu",
                name_hi=PLANETS_HI[i],
                longitude=ketu_lon,
                sign_index=sign_index,
                sign=SIGNS[sign_index],
                sign_en=SIGNS_EN[sign_index],
                sign_hi=SIGNS_HI[sign_index],
                degree_in_sign=round(degree_in_sign, 4),
                nakshatra_index=nak_index,
                nakshatra=NAKSHATRAS[nak_index],
                nakshatra_lord=NAKSHATRA_LORDS[nak_index],
                pada=pada,
                house=_house_from_lagna(sign_index, lagna_sign_index),
                is_retrograde=True,  # Ketu always retrograde
                speed=-rahu_data.speed,
                dignity=_get_dignity("Ketu", sign_index, degree_in_sign),
                avastha=_get_avastha(degree_in_sign, sign_index),
                is_combust=False,
                sign_lord=SIGN_LORDS[sign_index],
            )
        else:
            swe_id = SWE_PLANETS[planet_name]
            result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            lon = result[0][0]
            speed = result[0][3]
            is_retro = speed < 0

            sign_index = int(lon / 30.0)
            degree_in_sign = lon - sign_index * 30.0
            nak_index, pada = get_nakshatra(lon)

            if planet_name == "Rahu":
                is_retro = True  # Rahu always retrograde

            planet_data = PlanetData(
                name=planet_name,
                name_hi=PLANETS_HI[i],
                longitude=round(lon, 4),
                sign_index=sign_index,
                sign=SIGNS[sign_index],
                sign_en=SIGNS_EN[sign_index],
                sign_hi=SIGNS_HI[sign_index],
                degree_in_sign=round(degree_in_sign, 4),
                nakshatra_index=nak_index,
                nakshatra=NAKSHATRAS[nak_index],
                nakshatra_lord=NAKSHATRA_LORDS[nak_index],
                pada=pada,
                house=_house_from_lagna(sign_index, lagna_sign_index),
                is_retrograde=is_retro,
                speed=round(speed, 6),
                dignity=_get_dignity(planet_name, sign_index, degree_in_sign),
                avastha=_get_avastha(degree_in_sign, sign_index),
                is_combust=_check_combustion(planet_name, lon, sun_lon, is_retro),
                sign_lord=SIGN_LORDS[sign_index],
            )

        chart.planets[planet_name] = planet_data

    return chart


def get_house_lord(chart: ChartData, house_num: int) -> str:
    """Get the lord of a specific house (whole sign)."""
    sign_index = (chart.lagna_sign_index + house_num - 1) % 12
    return SIGN_LORDS[sign_index]


def get_planets_in_house(chart: ChartData, house_num: int) -> list[PlanetData]:
    """Get all planets in a specific house."""
    return [p for p in chart.planets.values() if p.house == house_num]


def get_planet_house(chart: ChartData, planet_name: str) -> int:
    """Get the house number of a planet."""
    return chart.planets[planet_name].house


def are_conjunct(chart: ChartData, planet1: str, planet2: str, orb: float = DEFAULT_CONJUNCTION_ORB) -> bool:
    """Check if two planets are conjunct (in same sign or within orb)."""
    p1 = chart.planets[planet1]
    p2 = chart.planets[planet2]
    if p1.sign_index == p2.sign_index:
        return True
    diff = abs(p1.longitude - p2.longitude)
    if diff > 180:
        diff = 360 - diff
    return diff <= orb


def has_aspect(chart: ChartData, aspecting_planet: str, target_house: int) -> bool:
    """Check if a planet aspects a given house (including special aspects)."""
    p = chart.planets[aspecting_planet]
    planet_house = p.house

    # Standard 7th aspect
    aspected_house = ((planet_house - 1 + 6) % 12) + 1
    if aspected_house == target_house:
        return True

    # Special aspects
    if aspecting_planet in SPECIAL_ASPECTS:
        for asp in SPECIAL_ASPECTS[aspecting_planet]:
            aspected = ((planet_house - 1 + asp - 1) % 12) + 1
            if aspected == target_house:
                return True

    return False
