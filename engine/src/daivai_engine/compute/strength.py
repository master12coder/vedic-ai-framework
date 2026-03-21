"""Shadbala — six-fold planetary strength computation.

Implements all six components of Shadbala in shashtiyamsas (60ths of a rupa):
Sthana Bala, Dig Bala, Kala Bala, Cheshta Bala, Naisargika Bala, Drik Bala.
Also preserves the backward-compatible ``compute_planet_strengths`` API.
"""

from __future__ import annotations

from daivai_engine.compute.divisional import (
    compute_drekkana_sign,
    compute_dwadashamsha_sign,
    compute_hora_sign,
    compute_navamsha_sign,
    compute_saptamsha_sign,
    compute_trimshamsha_sign,
)
from daivai_engine.constants import (
    ASPECT_STRENGTH_DEFAULT,
    ASPECT_STRENGTHS,
    DEBILITATION,
    EXALTATION,
    EXALTATION_DEGREE,
    KENDRAS,
    MOOLTRIKONA,
    NATURAL_ENEMIES,
    NATURAL_FRIENDS,
    OWN_SIGNS,
    SIGN_LORDS,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.strength import PlanetStrength, ShadbalaResult


# ---------------------------------------------------------------------------
# Fixed constants used across Shadbala components
# ---------------------------------------------------------------------------

# Seven classical planets (Rahu/Ketu excluded from traditional Shadbala)
SHADBALA_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Naisargika Bala (natural strength) — fixed values in shashtiyamsas
# Fractions of 60: Sun=60*7/7, Moon=60*6/7, Mars=60*2/7, Mercury=60*3/7,
# Jupiter=60*4/7, Venus=60*5/7, Saturn=60*1/7  (BPHS Ch.23)
NAISARGIKA: dict[str, float] = {
    "Sun": 60.00,
    "Moon": 51.43,
    "Mars": 17.14,
    "Mercury": 25.71,
    "Jupiter": 34.29,
    "Venus": 42.86,
    "Saturn": 8.57,
}

# Minimum required total Shadbala (shashtiyamsas)
REQUIRED_SHADBALA: dict[str, float] = {
    "Sun": 390.0,
    "Moon": 360.0,
    "Mars": 300.0,
    "Mercury": 420.0,
    "Jupiter": 390.0,
    "Venus": 330.0,
    "Saturn": 300.0,
}

# Dig Bala best houses
_DIG_BEST: dict[str, int] = {
    "Sun": 10,
    "Mars": 10,
    "Jupiter": 1,
    "Mercury": 1,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
}

# Natural benefics and malefics
_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
_MALEFICS = {"Sun", "Mars", "Saturn"}

# Panapara and Apoklima houses for Kendradi Bala
_PANAPARA = {2, 5, 8, 11}
_APOKLIMA = {3, 6, 9, 12}


# ---------------------------------------------------------------------------
# 1. Sthana Bala (positional strength)
# ---------------------------------------------------------------------------


def _uchcha_bala(planet_name: str, longitude: float) -> float:
    """Exaltation strength: max 60 at exact exaltation degree, 0 at debilitation."""
    if planet_name not in EXALTATION or planet_name not in EXALTATION_DEGREE:
        return 30.0  # Neutral for Rahu/Ketu if called

    exalt_sign = EXALTATION[planet_name]
    exalt_deg_in_sign = EXALTATION_DEGREE[planet_name]
    exalt_lon = exalt_sign * 30.0 + exalt_deg_in_sign

    diff = abs(longitude - exalt_lon)
    if diff > 180.0:
        diff = 360.0 - diff

    return (180.0 - diff) / 3.0


# Dignity point table for Saptvargaja Bala (per BPHS Ch.23)
_SAPTVARGAJA_DIGNITY_PTS: dict[str, float] = {
    "exalted": 45.0,
    "own": 30.0,
    "mooltrikona": 22.5,
    "friendly": 15.0,
    "neutral": 7.5,
    "enemy": 3.75,
    "debilitated": 1.875,
}


def _sign_dignity_full(planet_name: str, sign_index: int, deg_in_sign: float) -> str:
    """Extended dignity: exalted/debilitated/mooltrikona/own/friendly/neutral/enemy.

    Falls back to sign lord friendship when the planet has no special dignity.
    """
    basic = _sign_dignity(planet_name, sign_index, deg_in_sign)
    if basic != "neutral":
        return basic
    sign_lord = SIGN_LORDS.get(sign_index)
    if sign_lord is None:
        return "neutral"
    if sign_lord in NATURAL_FRIENDS.get(planet_name, []):
        return "friendly"
    if sign_lord in NATURAL_ENEMIES.get(planet_name, []):
        return "enemy"
    return "neutral"


def _saptvargaja_bala(planet_name: str, longitude: float, sign_index: int) -> float:
    """Saptvargaja Bala across all 7 divisional charts (D1, D2, D3, D7, D9, D12, D30).

    Sums dignity points from each varga per BPHS Ch.23:
      exalted=45, own=30, mooltrikona=22.5, friendly=15,
      neutral=7.5, enemy=3.75, debilitated=1.875
    """
    deg_in_sign = longitude - sign_index * 30.0
    # (sign_index, deg_within_sign) for each varga; use 15.0 (mid-sign) for sub-vargas
    vargas: list[tuple[int, float]] = [
        (sign_index, deg_in_sign),  # D1 — exact degree
        (compute_hora_sign(longitude), 15.0),  # D2
        (compute_drekkana_sign(longitude), 15.0),  # D3
        (compute_saptamsha_sign(longitude), 15.0),  # D7
        (compute_navamsha_sign(longitude), 15.0),  # D9
        (compute_dwadashamsha_sign(longitude), 15.0),  # D12
        (compute_trimshamsha_sign(longitude), 15.0),  # D30
    ]
    total = 0.0
    for varga_sign, varga_deg in vargas:
        dignity = _sign_dignity_full(planet_name, varga_sign, varga_deg)
        total += _SAPTVARGAJA_DIGNITY_PTS.get(dignity, 7.5)
    return total


def _sign_dignity(planet_name: str, sign_index: int, deg_in_sign: float) -> str:
    """Determine planet dignity in a sign (replicates chart.py logic)."""
    if planet_name in EXALTATION and EXALTATION[planet_name] == sign_index:
        return "exalted"
    if planet_name in DEBILITATION and DEBILITATION[planet_name] == sign_index:
        return "debilitated"
    if planet_name in MOOLTRIKONA:
        mt_sign, mt_start, mt_end = MOOLTRIKONA[planet_name]
        if sign_index == mt_sign and mt_start <= deg_in_sign <= mt_end:
            return "mooltrikona"
    if planet_name in OWN_SIGNS and sign_index in OWN_SIGNS[planet_name]:
        return "own"
    return "neutral"


def _ojhayugma_bala(planet_name: str, sign_index: int, longitude: float) -> float:
    """Odd/even Rashi and Navamsha strength (15 each, max 30).

    Female planets (Moon, Venus) prefer even signs (Taurus=1, Cancer=3 …);
    all others prefer odd signs (Aries=0, Gemini=2 …).
    Applies independently to both the Rashi (D1) and Navamsha (D9) positions.
    Source: BPHS Ch.23 Ojhayugmarasyamsa Bala.
    """
    female = {"Moon", "Venus"}
    score = 0.0

    # Rashi component
    is_odd_rashi = sign_index % 2 == 0  # 0-indexed: Aries=0 is odd
    if planet_name in female:
        score += 15.0 if not is_odd_rashi else 0.0
    else:
        score += 15.0 if is_odd_rashi else 0.0

    # Navamsha component
    d9_sign = compute_navamsha_sign(longitude)
    is_odd_navamsha = d9_sign % 2 == 0
    if planet_name in female:
        score += 15.0 if not is_odd_navamsha else 0.0
    else:
        score += 15.0 if is_odd_navamsha else 0.0

    return score


def _kendradi_bala(house: int) -> float:
    """Kendra/Panapara/Apoklima strength."""
    if house in KENDRAS:
        return 60.0
    if house in _PANAPARA:
        return 30.0
    if house in _APOKLIMA:
        return 15.0
    return 15.0


def _drekkana_bala(planet_name: str, longitude: float) -> float:
    """Drekkana Bala based on D3 position.

    Male planets (Sun, Mars, Jupiter) strong in 1st drekkana (0-10 deg),
    neutral planets (Mercury, Saturn) in 2nd drekkana (10-20 deg),
    female planets (Moon, Venus) in 3rd drekkana (20-30 deg).
    """
    sign_index = int(longitude / 30.0)
    deg_in_sign = longitude - sign_index * 30.0

    if deg_in_sign < 10.0:
        drekkana = 1
    elif deg_in_sign < 20.0:
        drekkana = 2
    else:
        drekkana = 3

    male = {"Sun", "Mars", "Jupiter"}
    female = {"Moon", "Venus"}

    if planet_name in male and drekkana == 1:
        return 15.0
    if planet_name in female and drekkana == 3:
        return 15.0
    if planet_name not in male and planet_name not in female and drekkana == 2:
        return 15.0
    return 0.0


def _sthana_bala(chart: ChartData, planet_name: str) -> float:
    """Total Sthana Bala = sum of sub-components."""
    p = chart.planets[planet_name]
    uchcha = _uchcha_bala(planet_name, p.longitude)
    saptvar = _saptvargaja_bala(planet_name, p.longitude, p.sign_index)
    ojha = _ojhayugma_bala(planet_name, p.sign_index, p.longitude)
    kendra = _kendradi_bala(p.house)
    drekk = _drekkana_bala(planet_name, p.longitude)
    return round(uchcha + saptvar + ojha + kendra + drekk, 2)


# ---------------------------------------------------------------------------
# 2. Dig Bala (directional strength)
# ---------------------------------------------------------------------------


def _dig_bala(chart: ChartData, planet_name: str) -> float:
    """Directional strength: 60 at best house, 0 at worst (opposite)."""
    p = chart.planets[planet_name]
    best = _DIG_BEST.get(planet_name, 1)
    # House distance (circular, 1-12)
    dist = abs(p.house - best)
    if dist > 6:
        dist = 12 - dist
    return round(max(0.0, 60.0 * (1.0 - dist / 6.0)), 2)


# ---------------------------------------------------------------------------
# 3. Kala Bala (temporal strength)
# ---------------------------------------------------------------------------

# Chaldean order of planets used for planetary hora computation (BPHS Ch.23 v7)
# Sun=0, Venus=1, Mercury=2, Moon=3, Saturn=4, Jupiter=5, Mars=6
_CHALDEAN_ORDER: list[str] = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
_CHALDEAN_INDEX: dict[str, int] = {p: i for i, p in enumerate(_CHALDEAN_ORDER)}

# Module-level cache so Abda/Masa lords are computed once per chart.
# Key: (dob, tob, timezone_name) → (abda_lord, masa_lord)
_abda_masa_cache: dict[tuple[str, str, str], tuple[str, str]] = {}

# Tribhaga Bala: planet ruling each third of day/night (BPHS Ch.23)
_TRIBHAGA_DAY: dict[int, str] = {1: "Mercury", 2: "Sun", 3: "Saturn"}
_TRIBHAGA_NIGHT: dict[int, str] = {1: "Moon", 2: "Venus", 3: "Mars"}


def _compute_hora_lord(chart: ChartData) -> str:
    """Return the planetary hora lord ruling the birth moment — BPHS Ch.23 v7.

    A planetary hora divides the day (sunrise→sunset) and night (sunset→sunrise)
    each into 12 equal parts.  The first hora of any weekday is ruled by that
    weekday's planet; subsequent horas follow the Chaldean descending order
    (Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars → Sun …).

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

    # Weekday lord → starting Chaldean index for this day's hora sequence
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
        # Night birth (pre-sunrise): previous sunset → today's sunrise
        jd_prev_sunset = compute_sunset(jd_birth - 1.0, lat, lon)
        night_len = jd_sunrise - jd_prev_sunset
        hora_len = night_len / 12.0 if night_len > 0 else 1.0
        elapsed = jd_birth - jd_prev_sunset
        hora_num = min(int(elapsed / hora_len), 11)
        # Night horas begin at the 13th hora of the day sequence
        hora_chaldean = (start_idx + 12 + hora_num) % 7
    else:
        # Night birth (post-sunset): today's sunset → tomorrow's sunrise
        jd_next_sunrise = compute_sunrise(jd_birth + 1.0, lat, lon)
        night_len = jd_next_sunrise - jd_sunset
        hora_len = night_len / 12.0 if night_len > 0 else 1.0
        elapsed = jd_birth - jd_sunset
        hora_num = min(int(elapsed / hora_len), 11)
        hora_chaldean = (start_idx + 12 + hora_num) % 7

    return _CHALDEAN_ORDER[hora_chaldean]


def _tribhaga_bala(chart: ChartData, planet_name: str) -> float:
    """Tribhaga (one-third) Bala — BPHS Ch.23.

    Jupiter always gets 60 virupas. For others, the planet ruling the current
    third of the daytime or nighttime also receives 60 virupas.

    Daytime thirds  (sunrise → sunset):   1st=Mercury, 2nd=Sun, 3rd=Saturn
    Nighttime thirds (sunset → sunrise):  1st=Moon, 2nd=Venus, 3rd=Mars

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
        # Early-morning night birth (previous sunset → today's sunrise)
        jd_prev_sunset = compute_sunset(jd_birth - 1.0, lat, lon)
        night_len = jd_sunrise - jd_prev_sunset
        elapsed = jd_birth - jd_prev_sunset
        third = night_len / 3.0
        part = min(3, int(elapsed / third) + 1) if third > 0 else 1
        lord = _TRIBHAGA_NIGHT[part]
    else:
        # Evening night birth (today's sunset → tomorrow's sunrise)
        jd_next_sunrise = compute_sunrise(jd_birth + 1.0, lat, lon)
        night_len = jd_next_sunrise - jd_sunset
        elapsed = jd_birth - jd_sunset
        third = night_len / 3.0
        part = min(3, int(elapsed / third) + 1) if third > 0 else 1
        lord = _TRIBHAGA_NIGHT[part]

    return 60.0 if planet_name == lord else 0.0


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
    classical Vedic weekday planet (Sun=0 → Sun, Mon=1 → Moon, …).

    Args:
        jd: Julian Day number.
        tz_name: Timezone name for local-time conversion.

    Returns:
        Planet name (e.g., "Sun", "Moon", "Mars", …).
    """
    import pytz

    from daivai_engine.compute.datetime_utils import from_jd
    from daivai_engine.constants import DAY_PLANET

    utc_dt = from_jd(jd)
    local_dt = utc_dt.astimezone(pytz.timezone(tz_name))

    # Python weekday: Mon=0 … Sun=6 → convert to Sun=0 … Sat=6
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
        (abda_lord, masa_lord) — planet names as strings.
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

    # Search ±20 days around April 14 of birth year
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


def _kala_bala(chart: ChartData, planet_name: str) -> float:
    """Temporal strength — 8 sub-components from BPHS Ch.23.

    1. Nathonnatha (60): Day/night birth preference per planet.
    2. Paksha (60): Lunar-fortnight preference (benefics/malefics).
    3. Hora (60): Planetary hour lord at birth.
    4. Vara (45): Weekday lord strength.
    5. Ayana (40/20): Uttarayana / Dakshinayana preference.
    6. Masa (30): Solar month lord receives 30 Virupas.  [BPHS Ch.23 v13-15]
    7. Abda (15): Solar year lord receives 15 Virupas.   [BPHS Ch.23 v16-18]
    8. Tribhaga (60): Planet ruling the current 1/3 of day/night. Jupiter always.

    Source: BPHS Chapter 23.
    """
    moon_lon = chart.planets["Moon"].longitude
    sun_lon = chart.planets["Sun"].longitude

    # 1. Nathonnatha Bala (day/night) — BPHS Ch.23 v1-3
    sun_house = chart.planets["Sun"].house
    is_day_birth = sun_house >= 7  # Sun above horizon
    diurnal = {"Sun", "Jupiter", "Venus"}
    nocturnal = {"Moon", "Mars", "Saturn"}
    if planet_name in diurnal:
        nathonnatha = 60.0 if is_day_birth else 0.0
    elif planet_name in nocturnal:
        nathonnatha = 0.0 if is_day_birth else 60.0
    else:
        nathonnatha = 30.0  # Mercury — always neutral

    # 2. Paksha Bala — BPHS Ch.23 v4-6 (graduated, not binary)
    # Benefics gain strength proportionate to Moon's angular distance from Sun.
    # Formula: moon_sun_arc / 3  (max 60 at full moon, 0 at new moon).
    # Malefics receive the complement.  Source: BPHS Ch.23 v4-6.
    moon_sun_diff = (moon_lon - sun_lon) % 360.0
    if moon_sun_diff > 180.0:
        moon_sun_diff = 360.0 - moon_sun_diff  # Collapse to 0-180 arc
    paksha_strong = moon_sun_diff / 3.0  # 0-60
    if planet_name in _BENEFICS:
        paksha = paksha_strong
    elif planet_name in _MALEFICS:
        paksha = 60.0 - paksha_strong
    else:
        paksha = 30.0

    # 3. Hora Bala (planetary hour) — BPHS Ch.23 v7
    # The planet ruling the actual Chaldean hora at birth gets 60; others get 0.
    hora_lord = _compute_hora_lord(chart)
    hora = 60.0 if planet_name == hora_lord else 0.0

    # 4. Vara Bala (weekday strength) — BPHS Ch.23 v8
    # Only the weekday lord receives 45 virupas; all others receive 0.
    from daivai_engine.compute.datetime_utils import parse_birth_datetime
    from daivai_engine.constants import DAY_PLANET

    birth_dt = parse_birth_datetime(chart.dob, chart.tob, chart.timezone_name)
    weekday = birth_dt.weekday()
    day_idx = (weekday + 1) % 7  # Convert Python Mon=0 to Sun=0 convention
    day_lord = DAY_PLANET.get(day_idx, "Sun")
    vara = 45.0 if planet_name == day_lord else 0.0

    # 5. Ayana Bala — BPHS Ch.23 v9-11
    sun_sign = chart.planets["Sun"].sign_index
    is_uttarayana = sun_sign in (9, 10, 11, 0, 1, 2)  # Capricorn → Gemini
    if planet_name in diurnal:
        ayana = 40.0 if is_uttarayana else 20.0
    elif planet_name in nocturnal:
        ayana = 20.0 if is_uttarayana else 40.0
    else:
        ayana = 30.0

    # 6 & 7. Masa Bala + Abda Bala — BPHS Ch.23 v13-18
    cache_key = (chart.dob, chart.tob, chart.timezone_name)
    if cache_key not in _abda_masa_cache:
        _abda_masa_cache[cache_key] = _compute_abda_masa_lords(chart)
    abda_lord, masa_lord = _abda_masa_cache[cache_key]

    masa = 30.0 if planet_name == masa_lord else 0.0
    abda = 15.0 if planet_name == abda_lord else 0.0

    # 8. Tribhaga Bala — BPHS Ch.23
    tribhaga = _tribhaga_bala(chart, planet_name)

    return round(nathonnatha + paksha + hora + vara + ayana + masa + abda + tribhaga, 2)


# ---------------------------------------------------------------------------
# 4. Cheshta Bala (motional strength)
# ---------------------------------------------------------------------------


def _cheshta_bala(chart: ChartData, planet_name: str) -> float:
    """Motional strength based on speed and retrogression.

    Sun and Moon always get 30 (they do not retrograde).
    Retrograde: 60, Stationary (|speed| < 0.1): 45,
    Direct & fast (|speed| > avg): 30, Direct & slow: 15.
    """
    if planet_name in ("Sun", "Moon"):
        return 30.0

    p = chart.planets[planet_name]

    if p.is_retrograde:
        return 60.0

    speed = abs(p.speed)
    if speed < 0.1:
        return 45.0  # Stationary

    # Average daily speeds for comparison (approximate)
    avg_speeds: dict[str, float] = {
        "Mars": 0.524,
        "Mercury": 1.383,
        "Jupiter": 0.083,
        "Venus": 1.2,
        "Saturn": 0.034,
        "Rahu": 0.053,
        "Ketu": 0.053,
    }
    avg = avg_speeds.get(planet_name, 0.5)
    if speed >= avg:
        return 30.0
    return 15.0


# ---------------------------------------------------------------------------
# 5. Naisargika Bala (natural strength — fixed)
# ---------------------------------------------------------------------------


def _naisargika_bala(planet_name: str) -> float:
    """Fixed natural strength per planet."""
    return NAISARGIKA.get(planet_name, 0.0)


# ---------------------------------------------------------------------------
# 6. Drik Bala (aspectual strength with graduated BPHS percentages)
# ---------------------------------------------------------------------------


def _get_aspect_strength(planet_name: str, planet_house: int, target_house: int) -> float:
    """Return the aspect strength fraction (0.0-1.0) cast by *planet_name*.

    Uses BPHS graduated aspect strengths from ASPECT_STRENGTHS in constants:
      - All planets: 7th house = 1.0 (Poorna Drishti / full aspect)
      - Mars:    4th = 0.75, 8th = 1.0
      - Jupiter: 5th = 0.50, 9th = 1.0
      - Saturn:  3rd = 0.25, 10th = 1.0
      - Rahu/Ketu: 5th = 0.50, 9th = 1.0

    Args:
        planet_name: Name of the aspecting planet.
        planet_house: House (1-12) the planet occupies.
        target_house: House (1-12) being aspected.

    Returns:
        Strength fraction in [0.0, 1.0].
    """
    # "Nth house from planet" — 1-indexed forward count
    which = (target_house - planet_house) % 12 + 1
    strengths = ASPECT_STRENGTHS.get(planet_name, ASPECT_STRENGTH_DEFAULT)
    return strengths.get(which, 0.0)


def _drik_bala(chart: ChartData, planet_name: str) -> float:
    """Aspectual strength using BPHS graduated aspect percentages.

    Benefic aspects: +15 x strength_fraction
    Malefic aspects: -15 x strength_fraction
    """
    p = chart.planets[planet_name]
    target_house = p.house
    score = 0.0

    for other_name in SHADBALA_PLANETS:
        if other_name == planet_name:
            continue
        other = chart.planets[other_name]
        strength = _get_aspect_strength(other_name, other.house, target_house)
        if strength > 0.0:
            if other_name in _BENEFICS:
                score += 15.0 * strength
            elif other_name in _MALEFICS:
                score -= 15.0 * strength

    return round(score, 2)


def _aspects_house(planet_name: str, planet_house: int, target_house: int) -> bool:
    """Return True if planet casts any aspect on target_house.

    Retained for backward compatibility with code that calls this directly.
    """
    return _get_aspect_strength(planet_name, planet_house, target_house) > 0.0


# ---------------------------------------------------------------------------
# Yuddha Bala (planetary war adjustment) — post-processing step
# ---------------------------------------------------------------------------


def _yuddha_bala_adjustments(chart: ChartData) -> dict[str, float]:
    """Return Yuddha Bala virupad adjustments keyed by planet name.

    Per BPHS: when two planets are within 1° of each other they are at war.
    The winner gains strength, the loser loses it (60 virupas each).
    Only Mars, Mercury, Jupiter, Venus, Saturn participate in planetary war.

    Args:
        chart: Computed birth chart.

    Returns:
        Dict mapping planet name → adjustment (positive for winner, negative for loser).
    """
    from daivai_engine.compute.graha_yuddha import detect_planetary_war

    adjustments: dict[str, float] = {}
    for war in detect_planetary_war(chart):
        adjustments[war.winner] = adjustments.get(war.winner, 0.0) + 60.0
        adjustments[war.loser] = adjustments.get(war.loser, 0.0) - 60.0
    return adjustments


# ---------------------------------------------------------------------------
# Main Shadbala computation
# ---------------------------------------------------------------------------


def compute_shadbala(chart: ChartData) -> list[ShadbalaResult]:
    """Compute full six-fold Shadbala for the seven classical planets.

    Returns a list of ShadbalaResult sorted by total (descending), with
    ranks assigned (1 = strongest).
    """
    results: list[ShadbalaResult] = []
    yuddha_adj = _yuddha_bala_adjustments(chart)

    for planet_name in SHADBALA_PLANETS:
        sb = _sthana_bala(chart, planet_name)
        db = _dig_bala(chart, planet_name)
        kb = _kala_bala(chart, planet_name)
        cb = _cheshta_bala(chart, planet_name)
        nb = _naisargika_bala(planet_name)
        drk = _drik_bala(chart, planet_name)
        yb = yuddha_adj.get(planet_name, 0.0)
        total = round(sb + db + kb + cb + nb + drk + yb, 2)
        req = REQUIRED_SHADBALA[planet_name]
        ratio = round(total / req, 3) if req > 0 else 0.0

        results.append(
            ShadbalaResult(
                planet=planet_name,
                sthana_bala=sb,
                dig_bala=db,
                kala_bala=kb,
                cheshta_bala=cb,
                naisargika_bala=nb,
                drik_bala=drk,
                yuddha_bala=yb,
                total=total,
                required=req,
                ratio=ratio,
                is_strong=ratio >= 1.0,
                rank=0,
            )
        )

    # Assign ranks by total descending
    results.sort(key=lambda r: r.total, reverse=True)
    for i, r in enumerate(results):
        r.rank = i + 1

    return results


# ---------------------------------------------------------------------------
# Backward-compatible API (used by interpreter / formatter)
# ---------------------------------------------------------------------------


def compute_planet_strengths(chart: ChartData) -> list[PlanetStrength]:
    """Compute relative strengths for all planets (backward-compatible).

    Wraps the full Shadbala for the 7 classical planets and adds simplified
    entries for Rahu and Ketu to maintain API compatibility.
    """
    shadbala = compute_shadbala(chart)
    strengths: list[PlanetStrength] = []

    # Build a lookup for ratio-based normalization
    max_total = max(r.total for r in shadbala) if shadbala else 1.0

    for r in shadbala:
        # Normalize to 0-1 range for backward compatibility
        norm_sthana = min(1.0, r.sthana_bala / 180.0)
        norm_dig = min(1.0, r.dig_bala / 60.0)
        norm_kala = min(1.0, r.kala_bala / 120.0)
        total_rel = min(1.0, r.total / max_total) if max_total > 0 else 0.0

        strengths.append(
            PlanetStrength(
                planet=r.planet,
                sthana_bala=round(norm_sthana, 3),
                dig_bala=round(norm_dig, 3),
                kala_bala=round(norm_kala, 3),
                total_relative=round(total_rel, 3),
                rank=0,
                is_strong=r.is_strong,
            )
        )

    # Add simplified entries for Rahu and Ketu
    for node_name in ("Rahu", "Ketu"):
        if node_name in chart.planets:
            p = chart.planets[node_name]
            dignity_scores = {
                "exalted": 1.0,
                "mooltrikona": 0.85,
                "own": 0.75,
                "neutral": 0.4,
                "debilitated": 0.1,
            }
            sb = dignity_scores.get(p.dignity, 0.4)
            # Simplified dig/kala for nodes
            db = 0.5
            kb = 0.5
            total_rel = sb * 0.5 + db * 0.25 + kb * 0.25
            strengths.append(
                PlanetStrength(
                    planet=node_name,
                    sthana_bala=round(sb, 3),
                    dig_bala=round(db, 3),
                    kala_bala=round(kb, 3),
                    total_relative=round(total_rel, 3),
                    rank=0,
                    is_strong=total_rel >= 0.55,
                )
            )

    # Assign ranks by total_relative descending
    strengths.sort(key=lambda s: s.total_relative, reverse=True)
    for i, s in enumerate(strengths):
        s.rank = i + 1

    return strengths


def get_strongest_planet(chart: ChartData) -> str:
    """Return the name of the strongest planet in the chart."""
    strengths = compute_planet_strengths(chart)
    return strengths[0].planet


def get_weakest_planet(chart: ChartData) -> str:
    """Return the name of the weakest planet in the chart."""
    strengths = compute_planet_strengths(chart)
    return strengths[-1].planet
