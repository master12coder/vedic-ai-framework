"""Panchang computation — Tithi, Nakshatra, Yoga, Karana, Vara, Rahu Kaal."""

from __future__ import annotations

from datetime import datetime

import swisseph as swe

from jyotish.utils.constants import (
    TITHI_NAMES, NAKSHATRAS, PANCHANG_YOGA_NAMES, KARANA_NAMES,
    DAY_NAMES, DAY_NAMES_HI, DAY_PLANET, RAHU_KAAL_SLOT,
    YAMAGHANDA_SLOT, GULIKA_SLOT,
)
from jyotish.utils.datetime_utils import (
    to_jd, compute_sunrise, compute_sunset, from_jd, parse_birth_datetime,
)
from jyotish.domain.models.panchang import PanchangData


def compute_panchang(
    date_str: str,
    lat: float,
    lon: float,
    tz_name: str = "Asia/Kolkata",
    place: str = "",
) -> PanchangData:
    """Compute Panchang for a given date and location.

    Args:
        date_str: Date as DD/MM/YYYY
        lat: Latitude
        lon: Longitude
        tz_name: Timezone name
        place: Place name for display
    """
    # Parse date at noon local time
    dt = parse_birth_datetime(date_str, "12:00", tz_name)
    jd = to_jd(dt)

    # Set Lahiri ayanamsha
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Vara (day of week)
    day_index = dt.weekday()
    # Python weekday: Mon=0..Sun=6 -> convert to our system Sun=0..Sat=6
    day_map = {6: 0, 0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6}
    vara_index = day_map[day_index]

    # Compute Sun and Moon positions (sidereal)
    sun_result = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
    moon_result = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
    sun_lon = sun_result[0][0]
    moon_lon = moon_result[0][0]

    # Tithi: angular distance of Moon from Sun / 12
    moon_sun_diff = (moon_lon - sun_lon) % 360.0
    tithi_index = int(moon_sun_diff / 12.0)
    if tithi_index > 29:
        tithi_index = 29
    paksha = "Shukla" if tithi_index < 15 else "Krishna"

    # Nakshatra: Moon's position / 13.3333
    nak_span = 360.0 / 27.0
    nakshatra_index = int(moon_lon / nak_span)
    if nakshatra_index > 26:
        nakshatra_index = 26

    # Yoga (Panchang): (Sun + Moon longitude) / 13.3333
    yoga_lon = (sun_lon + moon_lon) % 360.0
    yoga_index = int(yoga_lon / nak_span)
    if yoga_index > 26:
        yoga_index = 26

    # Karana: half-tithi
    karana_raw = int(moon_sun_diff / 6.0)
    if karana_raw <= 0:
        karana_index = 10  # Kimstughna (first karana)
    elif karana_raw >= 57:
        # Last 4 fixed karanas
        karana_index = 7 + (karana_raw - 57)
        if karana_index > 10:
            karana_index = 10
    else:
        karana_index = (karana_raw - 1) % 7

    # Sunrise/Sunset
    try:
        sunrise_jd = compute_sunrise(jd, lat, lon)
        sunset_jd = compute_sunset(jd, lat, lon)
        sunrise_dt = from_jd(sunrise_jd)
        sunset_dt = from_jd(sunset_jd)

        import pytz
        tz = pytz.timezone(tz_name)
        sunrise_local = sunrise_dt.astimezone(tz)
        sunset_local = sunset_dt.astimezone(tz)
        sunrise_str = sunrise_local.strftime("%H:%M")
        sunset_str = sunset_local.strftime("%H:%M")

        # Rahu Kaal, Yamaghanda, Gulika
        daylight_minutes = (sunset_jd - sunrise_jd) * 24 * 60
        slot_minutes = daylight_minutes / 8

        def _slot_time(slot_num: int) -> str:
            start_min = (slot_num - 1) * slot_minutes
            end_min = slot_num * slot_minutes
            from datetime import timedelta
            start_t = sunrise_local + timedelta(minutes=start_min)
            end_t = sunrise_local + timedelta(minutes=end_min)
            return f"{start_t.strftime('%H:%M')} - {end_t.strftime('%H:%M')}"

        rahu_kaal = _slot_time(RAHU_KAAL_SLOT[vara_index])
        yamaghanda = _slot_time(YAMAGHANDA_SLOT[vara_index])
        gulika = _slot_time(GULIKA_SLOT[vara_index])
    except Exception:
        sunrise_str = "N/A"
        sunset_str = "N/A"
        rahu_kaal = "N/A"
        yamaghanda = "N/A"
        gulika = "N/A"

    return PanchangData(
        date=date_str,
        place=place or f"{lat},{lon}",
        latitude=lat,
        longitude=lon,
        vara=DAY_NAMES[vara_index],
        vara_hi=DAY_NAMES_HI[vara_index],
        vara_planet=DAY_PLANET[vara_index],
        tithi_index=tithi_index,
        tithi_name=TITHI_NAMES[tithi_index],
        paksha=paksha,
        nakshatra_index=nakshatra_index,
        nakshatra_name=NAKSHATRAS[nakshatra_index],
        yoga_index=yoga_index,
        yoga_name=PANCHANG_YOGA_NAMES[yoga_index],
        karana_index=karana_index,
        karana_name=KARANA_NAMES[karana_index],
        sunrise=sunrise_str,
        sunset=sunset_str,
        rahu_kaal=rahu_kaal,
        yamaghanda=yamaghanda,
        gulika=gulika,
    )
