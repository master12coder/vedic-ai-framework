"""Main chart computation — Swiss Ephemeris based sidereal chart engine."""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from daivai_engine.compute.ayanamsha import _SIDM, AyanamshaType
from daivai_engine.compute.chart_utils import (
    _check_combustion,
    _get_avastha,
    _get_dignity,
    _house_from_lagna,
    are_conjunct,
    get_house_lord,
    get_nakshatra,
    get_planet_house,
    get_planets_in_house,
    has_aspect,
)
from daivai_engine.compute.datetime_utils import parse_birth_datetime, to_jd
from daivai_engine.compute.geo import resolve_or_manual
from daivai_engine.constants import (
    DEGREES_PER_SIGN,
    FULL_CIRCLE_DEG,
    HALF_CIRCLE_DEG,
    NAKSHATRA_LORDS,
    NAKSHATRAS,
    PLANETS,
    PLANETS_HI,
    SIGN_LORDS,
    SIGNS,
    SIGNS_EN,
    SIGNS_HI,
    STATIONARY_THRESHOLDS,
    SWE_PLANETS,
)
from daivai_engine.models.chart import ChartData, PlanetData


# Re-export chart_utils symbols so existing `from daivai_engine.compute.chart import X` works.
__all__ = [
    "ChartData",
    "PlanetData",
    "_check_combustion",
    "_get_avastha",
    "_get_dignity",
    "_house_from_lagna",
    "are_conjunct",
    "compute_chart",
    "get_house_lord",
    "get_nakshatra",
    "get_planet_house",
    "get_planets_in_house",
    "has_aspect",
]


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
                # Ketu is always 180deg from Rahu
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
