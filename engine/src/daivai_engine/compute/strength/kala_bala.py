"""Kala Bala (temporal strength) — component of Shadbala.

Covers: Nathonnatha, Paksha, Hora, Vara, Ayana, Masa, Abda, Tribhaga.
Source: BPHS Chapter 23.
"""

from __future__ import annotations

from daivai_engine.compute.strength.kala_bala_helpers import (
    _BENEFICS,
    _CHALDEAN_ORDER,  # noqa: F401 — re-export for backward compat
    _MALEFICS,
    _abda_masa_cache,
    _compute_abda_masa_lords,
    _compute_hora_lord,
    _find_solar_ingress,  # noqa: F401 — re-export for backward compat
    _jd_to_day_planet,  # noqa: F401 — re-export for backward compat
    _tribhaga_bala,
)
from daivai_engine.models.chart import ChartData


def compute_kala_bala(chart: ChartData, planet_name: str) -> float:
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
