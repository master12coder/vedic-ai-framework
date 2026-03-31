"""Kala Bala helper functions — sub-component computations.

Individual sub-bala computations used by compute_kala_bala:
Hora lord, Tribhaga, Abda/Masa lords, solar ingress, weekday mapping.
Source: BPHS Chapter 23.
"""

from __future__ import annotations

from daivai_engine.models.chart import ChartData


# Natural benefics and malefics sets used in kala bala
_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
_MALEFICS = {"Sun", "Mars", "Saturn"}

# Chaldean order of planets used for planetary hora computation (BPHS Ch.23 v7)
# Sun=0, Venus=1, Mercury=2, Moon=3, Saturn=4, Jupiter=5, Mars=6
_CHALDEAN_ORDER: list[str] = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
_CHALDEAN_INDEX: dict[str, int] = {p: i for i, p in enumerate(_CHALDEAN_ORDER)}

# Module-level cache so Abda/Masa lords are computed once per chart.
# Key: (dob, tob, timezone_name) -> (abda_lord, masa_lord)
_abda_masa_cache: dict[tuple[str, str, str], tuple[str, str]] = {}

# Tribhaga Bala: planet ruling each third of day/night (BPHS Ch.23)
_TRIBHAGA_DAY: dict[int, str] = {1: "Mercury", 2: "Sun", 3: "Saturn"}
_TRIBHAGA_NIGHT: dict[int, str] = {1: "Moon", 2: "Venus", 3: "Mars"}


def _find_solar_ingress(target_sign: int, jd_near: float) -> float:
    """Find the JD when the Sun entered *target_sign*, searching backward.

    Uses a two-phase approach: step back day-by-day until the Sun is in the
    prior sign, then binary-search for the precise ingress moment.

    Args:
        target_sign: Sign index (0-11) the Sun is currently in.
        jd_near: Julian Day near or after the ingress.

    Returns:
        Julian Day of solar ingress into target_sign.
    """
    import swisseph as swe

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Step backward by whole days until Sun is in prior sign (max 35 days)
    jd_prev = jd_near
    for _ in range(36):
        jd_prev -= 1.0
        lon = swe.calc_ut(jd_prev, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        if int(lon / 30.0) != target_sign:
            break

    # Binary search for ingress moment (within ~1 second accuracy)
    lo, hi = jd_prev, jd_prev + 2.0
    for _ in range(50):
        mid = (lo + hi) / 2.0
        lon_mid = swe.calc_ut(mid, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        if int(lon_mid / 30.0) == target_sign:
            hi = mid
        else:
            lo = mid

    return (lo + hi) / 2.0


def _jd_to_day_planet(jd: float, tz_name: str) -> str:
    """Return the planet ruling the weekday corresponding to *jd*.

    Converts the Julian Day to local time and maps Mon-Sun to the
    classical Vedic weekday planet (Sun=0 -> Sun, Mon=1 -> Moon, ...).

    Args:
        jd: Julian Day number.
        tz_name: Timezone name for local-time conversion.

    Returns:
        Planet name (e.g., "Sun", "Moon", "Mars", ...).
    """
    import pytz

    from daivai_engine.compute.datetime_utils import from_jd
    from daivai_engine.constants import DAY_PLANET

    utc_dt = from_jd(jd)
    local_dt = utc_dt.astimezone(pytz.timezone(tz_name))

    # Python weekday: Mon=0 ... Sun=6 -> convert to Sun=0 ... Sat=6
    py_wd = local_dt.weekday()
    sun_zero = {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 0}
    return DAY_PLANET[sun_zero[py_wd]]


def _compute_abda_masa_lords(chart: ChartData) -> tuple[str, str]:
    """Compute the Abda Lord (year) and Masa Lord (month) for Kala Bala.

    Abda Lord:  Planet ruling the weekday of Sun's entry into Aries (Mesha
                Sankranti) in the birth year. Receives 15 Virupas.
    Masa Lord:  Planet ruling the weekday of Sun's entry into its current
                sign at birth (start of the solar month). Receives 30 Virupas.

    Source: BPHS Chapter 23, v13-18.

    Returns:
        (abda_lord, masa_lord) -- planet names as strings.
    """
    from datetime import datetime

    import pytz
    import swisseph as swe

    from daivai_engine.compute.datetime_utils import parse_birth_datetime, to_jd

    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    jd_birth = to_jd(birth_dt)

    # 1. Masa Lord: find when Sun entered its current sign
    sun_sign = chart.planets["Sun"].sign_index
    jd_masa = _find_solar_ingress(sun_sign, jd_birth)
    masa_lord = _jd_to_day_planet(jd_masa, chart.timezone_name)

    # 2. Abda Lord: find Mesha Sankranti (Sun enters Aries, sign 0) in
    # the birth year. Sidereal Mesha Sankranti falls around April 13-15.
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    tz = pytz.timezone(chart.timezone_name)

    # Search +-20 days around April 14 of birth year
    jd_april14 = to_jd(tz.localize(datetime(birth_dt.year, 4, 14, 12, 0)))
    jd_abda = jd_birth  # fallback

    for delta in range(-20, 21):
        jd_try = jd_april14 + delta
        lon_try = swe.calc_ut(jd_try, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        if int(lon_try / 30.0) == 0:  # Sun is in Aries
            jd_abda = _find_solar_ingress(0, jd_try)
            break

    abda_lord = _jd_to_day_planet(jd_abda, chart.timezone_name)
    return abda_lord, masa_lord


def _compute_hora_lord(chart: ChartData) -> str:
    """Return the planetary hora lord ruling the birth moment -- BPHS Ch.23 v7.

    A planetary hora divides the day (sunrise->sunset) and night (sunset->sunrise)
    each into 12 equal parts.  The first hora of any weekday is ruled by that
    weekday's planet; subsequent horas follow the Chaldean descending order
    (Sun -> Venus -> Mercury -> Moon -> Saturn -> Jupiter -> Mars -> Sun ...).

    Args:
        chart: Computed birth chart with julian_day, latitude, longitude.

    Returns:
        Name of the hora lord at the moment of birth.
    """
    from daivai_engine.compute.datetime_utils import (
        compute_sunrise,
        compute_sunset,
        parse_birth_datetime,
    )
    from daivai_engine.constants import DAY_PLANET

    jd_birth = chart.julian_day
    lat, lon = chart.latitude, chart.longitude

    jd_sunrise = compute_sunrise(jd_birth, lat, lon)
    jd_sunset = compute_sunset(jd_birth, lat, lon)

    # Weekday lord -> starting Chaldean index for this day's hora sequence
    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    weekday = birth_dt.weekday()
    day_idx = (weekday + 1) % 7  # Convert Python Mon=0 to Sun=0 convention
    day_lord = DAY_PLANET.get(day_idx, "Sun")
    start_idx = _CHALDEAN_INDEX[day_lord]

    if jd_sunrise <= jd_birth <= jd_sunset:
        # Daytime birth: 12 equal horas from sunrise to sunset
        day_len = jd_sunset - jd_sunrise
        hora_len = day_len / 12.0 if day_len > 0 else 1.0
        elapsed = jd_birth - jd_sunrise
        hora_num = min(int(elapsed / hora_len), 11)  # 0-indexed, clamp to 11
        hora_chaldean = (start_idx + hora_num) % 7
    elif jd_birth < jd_sunrise:
        # Night birth (pre-sunrise): previous sunset -> today's sunrise
        jd_prev_sunset = compute_sunset(jd_birth - 1.0, lat, lon)
        night_len = jd_sunrise - jd_prev_sunset
        hora_len = night_len / 12.0 if night_len > 0 else 1.0
        elapsed = jd_birth - jd_prev_sunset
        hora_num = min(int(elapsed / hora_len), 11)
        # Night horas begin at the 13th hora of the day sequence
        hora_chaldean = (start_idx + 12 + hora_num) % 7
    else:
        # Night birth (post-sunset): today's sunset -> tomorrow's sunrise
        jd_next_sunrise = compute_sunrise(jd_birth + 1.0, lat, lon)
        night_len = jd_next_sunrise - jd_sunset
        hora_len = night_len / 12.0 if night_len > 0 else 1.0
        elapsed = jd_birth - jd_sunset
        hora_num = min(int(elapsed / hora_len), 11)
        hora_chaldean = (start_idx + 12 + hora_num) % 7

    return _CHALDEAN_ORDER[hora_chaldean]


def _tribhaga_bala(chart: ChartData, planet_name: str) -> float:
    """Tribhaga (one-third) Bala -- BPHS Ch.23.

    Jupiter always gets 60 virupas. For others, the planet ruling the current
    third of the daytime or nighttime also receives 60 virupas.

    Daytime thirds  (sunrise -> sunset):   1st=Mercury, 2nd=Sun, 3rd=Saturn
    Nighttime thirds (sunset -> sunrise):  1st=Moon, 2nd=Venus, 3rd=Mars

    Args:
        chart: Computed birth chart (needs julian_day, latitude, longitude).
        planet_name: Classical planet name.

    Returns:
        60.0 if planet is the Tribhaga lord or is Jupiter; else 0.0.
    """
    from daivai_engine.compute.datetime_utils import compute_sunrise, compute_sunset

    if planet_name == "Jupiter":
        return 60.0

    jd_birth = chart.julian_day
    lat, lon = chart.latitude, chart.longitude

    jd_sunrise = compute_sunrise(jd_birth, lat, lon)
    jd_sunset = compute_sunset(jd_birth, lat, lon)

    if jd_sunrise <= jd_birth <= jd_sunset:
        # Daytime birth
        day_len = jd_sunset - jd_sunrise
        third = day_len / 3.0
        elapsed = jd_birth - jd_sunrise
        part = min(3, int(elapsed / third) + 1) if third > 0 else 1
        lord = _TRIBHAGA_DAY[part]
    elif jd_birth < jd_sunrise:
        # Early-morning night birth (previous sunset -> today's sunrise)
        jd_prev_sunset = compute_sunset(jd_birth - 1.0, lat, lon)
        night_len = jd_sunrise - jd_prev_sunset
        elapsed = jd_birth - jd_prev_sunset
        third = night_len / 3.0
        part = min(3, int(elapsed / third) + 1) if third > 0 else 1
        lord = _TRIBHAGA_NIGHT[part]
    else:
        # Evening night birth (today's sunset -> tomorrow's sunrise)
        jd_next_sunrise = compute_sunrise(jd_birth + 1.0, lat, lon)
        night_len = jd_next_sunrise - jd_sunset
        elapsed = jd_birth - jd_sunset
        third = night_len / 3.0
        part = min(3, int(elapsed / third) + 1) if third > 0 else 1
        lord = _TRIBHAGA_NIGHT[part]

    return 60.0 if planet_name == lord else 0.0
