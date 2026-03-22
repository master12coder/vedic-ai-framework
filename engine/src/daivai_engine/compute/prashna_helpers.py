"""Prashna helper functions: hora, swara, arudha, moon checks."""

from __future__ import annotations

from datetime import datetime

from daivai_engine.constants import SIGN_LORDS
from daivai_engine.models.chart import ChartData


# Question type → relevant house
_QUESTION_HOUSES: dict[str, int] = {
    "general": 1,
    "health": 1,
    "wealth": 2,
    "siblings": 3,
    "property": 4,
    "mother": 4,
    "education": 5,
    "children": 5,
    "enemies": 6,
    "disease": 6,
    "marriage": 7,
    "partnership": 7,
    "longevity": 8,
    "inheritance": 8,
    "fortune": 9,
    "father": 9,
    "career": 10,
    "status": 10,
    "gains": 11,
    "income": 11,
    "loss": 12,
    "travel": 12,
    "spirituality": 12,
}

# Hora sequence: Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars (repeating)
_HORA_LORDS: list[str] = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]

# Day index (0=Sunday) → hora lord for hour 1
_DAY_HORA_START: dict[int, int] = {0: 0, 1: 3, 2: 6, 3: 2, 4: 5, 5: 1, 6: 4}


def _is_moon_waxing(moon_lon: float, sun_lon: float) -> bool:
    """True if Moon is waxing (between new moon and full moon)."""
    diff = (moon_lon - sun_lon) % 360.0
    return diff < 180.0


def _compute_arudha(chart: ChartData, house_num: int) -> int:
    """Compute Arudha Pada for a given house.

    Algorithm (Jaimini / Prashna Marga):
    1. Count signs from house to its lord (= N)
    2. Count N signs from the lord
    3. If result = house itself or 7th from house → use 10th from house

    Source: Prashna Marga Ch.2, Jaimini Upadesha Sutras.
    """
    house_sign = (chart.lagna_sign_index + house_num - 1) % 12
    lord_name = SIGN_LORDS[house_sign]
    lord_sign = chart.planets[lord_name].sign_index

    # Count from house to lord
    dist = ((lord_sign - house_sign) % 12) + 1
    # Count same from lord
    arudha = (lord_sign + dist - 1) % 12

    # Exception: arudha in own house or 7th from it → use 10th from house
    seventh = (house_sign + 6) % 12
    if arudha in (house_sign, seventh):
        arudha = (house_sign + 9) % 12

    return int(arudha)


def _compute_hora_lord(dt: datetime) -> str:
    """Compute the Hora lord for a given datetime.

    Each hora (planetary hour) is 1 hour long. The first hora of the day
    is ruled by the day lord. The sequence then follows:
    Sun → Venus → Mercury → Moon → Saturn → Jupiter → Mars → Sun → ...

    Source: Prashna Marga Ch.3.
    """
    # Get day of week (0=Sunday)
    weekday = (dt.weekday() + 1) % 7  # Python Mon=0 → Sun=0 in our mapping
    hour_of_day = dt.hour  # 0-23

    start_idx = _DAY_HORA_START.get(weekday, 0)
    hora_idx = (start_idx + hour_of_day) % 7
    return _HORA_LORDS[hora_idx]


def _compute_swara(dt: datetime) -> str:
    """Compute the active Swara (breath) at the question time.

    Classical Swara Shastra (Prashna Marga Ch.5):
    - Ida (Moon/left nostril): active for first 60 ghatika after sunrise,
      then alternates. Simplification: even hours from midnight = Ida.
    - Pingala (Sun/right nostril): odd hours = Pingala.
    - Sushumna: transition period — indicates no strong direction.

    Returns: 'ida' (Moon-breath, favorable for passive/stable questions)
             'pingala' (Sun-breath, favorable for active/aggressive questions)
             'sushumna' (transition, indeterminate)

    Source: Swara Vigyana / Prashna Marga Ch.5.
    """
    hour = dt.hour
    minute = dt.minute

    # Transition at each hour boundary (±2 minutes = Sushumna)
    if minute <= 2 or minute >= 58:
        return "sushumna"

    # Even hours (0, 2, 4, ...) = Ida (Moon); odd hours = Pingala (Sun)
    if hour % 2 == 0:
        return "ida"
    return "pingala"
