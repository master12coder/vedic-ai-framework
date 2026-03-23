"""Main chart computation — Swiss Ephemeris based sidereal chart engine."""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from daivai_engine.compute.ayanamsha import _SIDM, AyanamshaType
from daivai_engine.compute.datetime_utils import parse_birth_datetime, to_jd
from daivai_engine.compute.geo import resolve_or_manual
from daivai_engine.constants import (
    AVASTHAS,
    CAZIMI_LIMIT,
    COMBUSTION_LIMITS,
    COMBUSTION_LIMITS_RETROGRADE,
    DEBILITATION,
    DEFAULT_CONJUNCTION_ORB,
    DEGREES_PER_SIGN,
    EXALTATION,
    FULL_CIRCLE_DEG,
    HALF_CIRCLE_DEG,
    MAX_NAKSHATRA_INDEX,
    MOOLTRIKONA,
    NAKSHATRA_LORDS,
    NAKSHATRA_SPAN_DEG,
    NAKSHATRAS,
    OWN_SIGNS,
    PADAS_PER_NAKSHATRA,
    PLANETS,
    PLANETS_HI,
    SIGN_LORDS,
    SIGNS,
    SIGNS_EN,
    SIGNS_HI,
    SPECIAL_ASPECTS,
    STATIONARY_THRESHOLDS,
    SWE_PLANETS,
)
from daivai_engine.models.chart import ChartData, PlanetData


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


def _check_combustion(
    planet: str, planet_lon: float, sun_lon: float, is_retro: bool
) -> tuple[bool, bool]:
    """Check combustion and cazimi status for a planet.

    Returns:
        Tuple of (is_combust, is_cazimi).
        - is_cazimi: within CAZIMI_LIMIT (17') of Sun — extremely powerful
        - is_combust: within combustion limit but outside cazimi — weakened
        A cazimi planet is NOT combust (is_combust=False when is_cazimi=True).

    Source: Saravali Ch.4; Phaladeepika Ch.2 v.6.
    """
    if planet in ("Sun", "Rahu", "Ketu"):
        return False, False
    limit = COMBUSTION_LIMITS.get(planet)
    if limit is None:
        return False, False
    if is_retro and planet in COMBUSTION_LIMITS_RETROGRADE:
        limit = COMBUSTION_LIMITS_RETROGRADE[planet]
    diff = abs(planet_lon - sun_lon)
    if diff > 180:
        diff = 360 - diff
    if diff < CAZIMI_LIMIT:
        return False, True  # Cazimi — in heart of Sun, not weakened
    return diff < limit, False


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
    ayanamsha_type: AyanamshaType = AyanamshaType.LAHIRI,
) -> ChartData:
    """Compute a complete Vedic birth chart.

    Args:
        name: Full name.
        dob: Date of birth as DD/MM/YYYY.
        tob: Time of birth as HH:MM or HH:MM:SS.
        place: Place name (geocoded automatically via Nominatim).
        gender: Male/Female.
        lat: Manual latitude in decimal degrees (if place not given).
        lon: Manual longitude in decimal degrees (if place not given).
        tz_name: IANA timezone name used when lat/lon given manually.
        ayanamsha_type: Sidereal zodiac correction system. Defaults to Lahiri
            (Indian government standard). Use AyanamshaType.KRISHNAMURTI for
            KP system calculations.

    Returns:
        Fully computed ChartData with all 9 planets, lagna, and metadata.
    """
    # Parse the birth date to use as the DST-accurate reference date for
    # timezone UTC offset computation (avoids systematic 1-hour error for
    # summer births in DST-affected timezones).
    day_str, month_str, year_str = dob.split("/")
    ref_date = datetime(int(year_str), int(month_str), int(day_str), 12, 0)

    # Resolve location (ref_date ensures DST-accurate utc_offset_hours field)
    geo = resolve_or_manual(place=place, lat=lat, lon=lon, tz_name=tz_name, ref_date=ref_date)

    # Parse datetime and compute Julian Day
    birth_dt = parse_birth_datetime(dob, tob, geo.timezone_name)
    jd = to_jd(birth_dt)

    # Set ayanamsha — defaults to Lahiri (swe.SIDM_LAHIRI).
    # AyanamshaType.KRISHNAMURTI must be used for KP calculations.
    # IMPORTANT: swe.set_sid_mode() is a global C-library call that affects ALL
    # subsequent swe.calc_ut(FLG_SIDEREAL) calls in this process. The try/finally
    # below restores Lahiri after ALL planetary computations so that other modules
    # relying on Lahiri as the implicit default are not silently corrupted.
    swe.set_sid_mode(_SIDM[ayanamsha_type])
    try:
        ayanamsha = swe.get_ayanamsa(jd)

        # Compute Lagna (Ascendant): houses_ex returns tropical ASC; subtract ayanamsha manually.
        _cusps, ascmc = swe.houses_ex(jd, geo.latitude, geo.longitude, b"W")
        lagna_tropical = ascmc[0]
        lagna_sidereal = (lagna_tropical - ayanamsha) % FULL_CIRCLE_DEG
        lagna_sign_index = int(lagna_sidereal / DEGREES_PER_SIGN)
        lagna_degree = lagna_sidereal - lagna_sign_index * DEGREES_PER_SIGN

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
                sign_index = int(ketu_lon / DEGREES_PER_SIGN)
                degree_in_sign = ketu_lon - sign_index * DEGREES_PER_SIGN
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
                    is_cazimi=False,
                    sign_lord=SIGN_LORDS[sign_index],
                )
            else:
                swe_id = SWE_PLANETS[planet_name]
                result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL | swe.FLG_SPEED)
                lon = result[0][0]
                speed = result[0][3]
                is_retro = speed < 0

                sign_index = int(lon / DEGREES_PER_SIGN)
                degree_in_sign = lon - sign_index * DEGREES_PER_SIGN
                nak_index, pada = get_nakshatra(lon)

                if planet_name == "Rahu":
                    is_retro = True  # Rahu always retrograde

                is_combust, is_cazimi = _check_combustion(planet_name, lon, sun_lon, is_retro)

                # Stationary detection: planet near zero speed = at direct/retrograde station.
                # Rahu/Ketu nodes and the Sun never station in the classical Vedic sense.
                threshold = STATIONARY_THRESHOLDS.get(planet_name)
                is_stationary = (
                    threshold is not None
                    and abs(speed) < threshold
                    and planet_name not in ("Sun", "Moon", "Rahu", "Ketu")
                )

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
                    is_stationary=is_stationary,
                    dignity=_get_dignity(planet_name, sign_index, degree_in_sign),
                    avastha=_get_avastha(degree_in_sign, sign_index),
                    is_combust=is_combust,
                    is_cazimi=is_cazimi,
                    sign_lord=SIGN_LORDS[sign_index],
                )

            chart.planets[planet_name] = planet_data

        return chart
    finally:
        # Restore Lahiri as the process-wide default after any non-Lahiri computation.
        if ayanamsha_type != AyanamshaType.LAHIRI:
            swe.set_sid_mode(swe.SIDM_LAHIRI)


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


def are_conjunct(
    chart: ChartData, planet1: str, planet2: str, orb: float = DEFAULT_CONJUNCTION_ORB
) -> bool:
    """Check if two planets are conjunct (in same sign or within orb)."""
    p1 = chart.planets[planet1]
    p2 = chart.planets[planet2]
    if p1.sign_index == p2.sign_index:
        return True
    diff = abs(p1.longitude - p2.longitude)
    if diff > HALF_CIRCLE_DEG:
        diff = FULL_CIRCLE_DEG - diff
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
