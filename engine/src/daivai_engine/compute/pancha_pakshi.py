"""Pancha Pakshi Shastra - Tamil 5-bird timing system computation.

Each day/night is divided into 5 equal Yamas (~2.4 hours each).
Birds are assigned to Yamas by a fixed sequence determined by current paksha.
Within each Yama, 5 sub-periods repeat the same bird rotation.

Key computation:
  1. Birth bird   = Moon's nakshatra x birth paksha (fixed for a person)
  2. Daily Yamas  = current paksha x day/night x precise sunrise/sunset
  3. Sub-periods  = Yama bird position -> 5 equal sub-divisions

Source: Classical Tamil Siddha tradition, Prasnamarga.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from daivai_engine.compute.datetime_utils import (
    compute_sunrise,
    compute_sunset,
    from_jd,
    parse_birth_datetime,
    to_jd,
)
from daivai_engine.constants import NAKSHATRAS
from daivai_engine.models.pancha_pakshi import (
    ACTIVITY_STRENGTH,
    Activity,
    Bird,
    PanchaPakshiDay,
    PanchaPakshiPeriod,
    PanchaPakshiResult,
)


_DATA_FILE = Path(__file__).parent.parent / "knowledge" / "pancha_pakshi_rules.yaml"


def _load_rules() -> dict:  # type: ignore[type-arg]
    """Load Pancha Pakshi rules from YAML (module-level cache)."""
    with _DATA_FILE.open() as f:
        return yaml.safe_load(f)  # type: ignore[no-any-return]


_RULES = _load_rules()

# Build lookup tables: YAML uses lowercase strings; enums use Title case.
_NAKSHATRA_BIRD: dict[str, dict[int, Bird]] = {
    paksha.capitalize(): {i: Bird(name.capitalize()) for i, name in enumerate(bird_list)}
    for paksha, bird_list in _RULES["nakshatra_bird_mapping"].items()
}

_ACTIVITY_SEQ: list[Activity] = [Activity(a.capitalize()) for a in _RULES["activity_sequence"]]

_YAMA_SEQS: dict[str, list[Bird]] = {
    key: [Bird(b.capitalize()) for b in seq] for key, seq in _RULES["yama_sequences"].items()
}


def get_birth_bird(nakshatra_index: int, birth_paksha: str) -> Bird:
    """Return birth bird from Moon's nakshatra index and birth paksha.

    Args:
        nakshatra_index: 0-26 (0=Ashwini … 26=Revati), from ChartData.
        birth_paksha: "Shukla" (waxing) or "Krishna" (waning) at time of birth.

    Source: Prasnamarga; Nakshatras 0-4=Vulture, 5-10=Owl, 11-15=Crow,
            16-21=Cock, 22-26=Peacock in Shukla. Reversed in Krishna.
    """
    return _NAKSHATRA_BIRD[birth_paksha][nakshatra_index]


def get_yama_sequence(paksha: str, is_day: bool) -> list[Bird]:
    """Return the ordered 5-bird sequence for a given paksha and day/night.

    Args:
        paksha: "Shukla" or "Krishna" (current paksha on query date).
        is_day: True for daytime (sunrise→sunset), False for nighttime.
    """
    key = f"{paksha.lower()}_{'day' if is_day else 'night'}"
    return list(_YAMA_SEQS[key])


def _sunrise_sunset(query_dt: datetime, lat: float, lon: float) -> tuple[datetime, datetime]:
    """Compute sunrise and sunset UTC datetimes for query_dt's UTC calendar date.

    Always uses noon UTC of the query date as the search anchor, ensuring
    correct sunrise/sunset regardless of query time within the day.
    """
    utc_dt = query_dt.astimezone(UTC)
    noon_utc = utc_dt.replace(hour=12, minute=0, second=0, microsecond=0)
    jd_noon = to_jd(noon_utc)
    return from_jd(compute_sunrise(jd_noon, lat, lon)), from_jd(compute_sunset(jd_noon, lat, lon))


def _build_periods(
    start: datetime,
    end: datetime,
    sequence: list[Bird],
    is_day: bool,
) -> list[PanchaPakshiPeriod]:
    """Build 5 equal Yama periods from start to end time.

    Activity follows position: Yama 1=Rule, 2=Eat, 3=Walk, 4=Sleep, 5=Die.
    """
    total_secs = (end - start).total_seconds()
    yama_secs = total_secs / 5.0
    return [
        PanchaPakshiPeriod(
            yama_index=i + 1,
            bird=sequence[i],
            activity=_ACTIVITY_SEQ[i],
            strength=ACTIVITY_STRENGTH[_ACTIVITY_SEQ[i]],
            start_time=start + timedelta(seconds=i * yama_secs),
            end_time=start + timedelta(seconds=(i + 1) * yama_secs),
            is_daytime=is_day,
        )
        for i in range(5)
    ]


def _find_period(periods: list[PanchaPakshiPeriod], dt: datetime) -> PanchaPakshiPeriod:
    """Find the Yama period that contains dt; returns last period if at boundary."""
    for period in periods:
        if period.start_time <= dt < period.end_time:
            return period
    return periods[-1]


def _find_sub_period(
    period: PanchaPakshiPeriod,
    sequence: list[Bird],
    dt: datetime,
) -> tuple[Bird, Activity, float, datetime, datetime, int]:
    """Find current sub-period within a Yama at time dt.

    Sub-birds rotate from the Yama's bird through the full sequence.
    Position i → activity _ACTIVITY_SEQ[i] (same Rule/Eat/Walk/Sleep/Die cycle).

    Returns:
        (bird, activity, strength, sub_start, sub_end, 1-based sub_index)
    """
    start_idx = sequence.index(period.bird)
    total_secs = (period.end_time - period.start_time).total_seconds()
    sub_secs = total_secs / 5.0
    for i in range(5):
        sub_start = period.start_time + timedelta(seconds=i * sub_secs)
        sub_end = period.start_time + timedelta(seconds=(i + 1) * sub_secs)
        if sub_start <= dt < sub_end or i == 4:  # i==4: catch last sub-period
            bird = sequence[(start_idx + i) % 5]
            act = _ACTIVITY_SEQ[i]
            return bird, act, ACTIVITY_STRENGTH[act], sub_start, sub_end, i + 1
    # Unreachable; satisfies type checker
    return sequence[start_idx], _ACTIVITY_SEQ[0], 1.0, period.start_time, period.end_time, 1


def _birth_bird_activity_in_yama(
    birth_bird: Bird,
    yama_bird: Bird,
    sequence: list[Bird],
) -> tuple[Activity, float]:
    """Return the activity and strength of birth_bird in this Yama's sub-sequence.

    Each Yama's sub-rotation starts at the Yama's main bird and covers all 5 birds
    exactly once. The birth bird's sub-position determines its activity.

    Mathematical property: since all Yama sequences start with Vulture at position 0,
    a birth bird at sequence position p gets sub-position (p - yama_pos + 5) % 5.
    """
    start_idx = sequence.index(yama_bird)
    for i in range(5):
        if sequence[(start_idx + i) % 5] == birth_bird:
            act = _ACTIVITY_SEQ[i]
            return act, ACTIVITY_STRENGTH[act]
    return _ACTIVITY_SEQ[0], 1.0  # Unreachable


def compute_pancha_pakshi(
    birth_nakshatra_index: int,
    birth_paksha: str,
    query_dt: datetime,
    current_paksha: str,
    lat: float,
    lon: float,
) -> PanchaPakshiResult:
    """Compute Pancha Pakshi state for a given moment.

    Args:
        birth_nakshatra_index: 0-26 (Moon's nakshatra at birth, 0=Ashwini).
        birth_paksha: "Shukla" or "Krishna" (paksha at time of birth).
        query_dt: Timezone-aware datetime for the moment to analyse.
        current_paksha: "Shukla" or "Krishna" (current moon phase at query).
        lat: Observer latitude.
        lon: Observer longitude.

    Returns:
        PanchaPakshiResult with current Yama state and birth bird's activity.
    """
    birth_bird = get_birth_bird(birth_nakshatra_index, birth_paksha)
    birth_nak = NAKSHATRAS[birth_nakshatra_index]
    sunrise, sunset = _sunrise_sunset(query_dt, lat, lon)
    is_day = sunrise <= query_dt < sunset
    sequence = get_yama_sequence(current_paksha, is_day)

    if is_day:
        periods = _build_periods(sunrise, sunset, sequence, is_day=True)
    elif query_dt >= sunset:
        # Evening night: today's sunset → tomorrow's sunrise
        next_noon = sunrise.replace(hour=12) + timedelta(days=1)
        next_sunrise = from_jd(compute_sunrise(to_jd(next_noon), lat, lon))
        periods = _build_periods(sunset, next_sunrise, sequence, is_day=False)
    else:
        # Pre-dawn night: yesterday's sunset → today's sunrise
        prev_noon = sunrise.replace(hour=12) - timedelta(days=1)
        prev_sunset = from_jd(compute_sunset(to_jd(prev_noon), lat, lon))
        periods = _build_periods(prev_sunset, sunrise, sequence, is_day=False)

    period = _find_period(periods, query_dt)
    sub_bird, sub_act, sub_str, sub_start, sub_end, sub_idx = _find_sub_period(
        period, sequence, query_dt
    )
    bb_act, bb_str = _birth_bird_activity_in_yama(birth_bird, period.bird, sequence)

    return PanchaPakshiResult(
        birth_bird=birth_bird,
        birth_nakshatra=birth_nak,
        birth_nakshatra_index=birth_nakshatra_index,
        birth_paksha=birth_paksha,
        query_dt=query_dt,
        is_daytime=is_day,
        current_paksha=current_paksha,
        current_bird=period.bird,
        current_activity=period.activity,
        current_strength=period.strength,
        period_start=period.start_time,
        period_end=period.end_time,
        yama_index=period.yama_index,
        sub_bird=sub_bird,
        sub_activity=sub_act,
        sub_strength=sub_str,
        sub_period_start=sub_start,
        sub_period_end=sub_end,
        sub_index=sub_idx,
        birth_bird_activity=bb_act,
        birth_bird_strength=bb_str,
    )


def compute_pancha_pakshi_day(
    birth_nakshatra_index: int,
    birth_paksha: str,
    date_str: str,
    current_paksha: str,
    lat: float,
    lon: float,
    tz_name: str = "Asia/Kolkata",
) -> PanchaPakshiDay:
    """Compute complete Pancha Pakshi breakdown for a full day.

    Args:
        birth_nakshatra_index: 0-26 (Moon's nakshatra at birth, 0=Ashwini).
        birth_paksha: "Shukla" or "Krishna" (paksha at time of birth).
        date_str: Date as DD/MM/YYYY.
        current_paksha: "Shukla" or "Krishna" for this day.
        lat: Observer latitude.
        lon: Observer longitude.
        tz_name: Timezone name for interpreting date_str (default Asia/Kolkata).

    Returns:
        PanchaPakshiDay with 5 day Yamas + 5 night Yamas.
    """
    birth_bird = get_birth_bird(birth_nakshatra_index, birth_paksha)
    noon_dt = parse_birth_datetime(date_str, "12:00", tz_name)
    sunrise, sunset = _sunrise_sunset(noon_dt, lat, lon)

    # Night ends at next day's sunrise
    next_noon_utc = noon_dt.astimezone(UTC).replace(hour=12) + timedelta(days=1)
    next_sunrise = from_jd(compute_sunrise(to_jd(next_noon_utc), lat, lon))

    day_seq = get_yama_sequence(current_paksha, is_day=True)
    night_seq = get_yama_sequence(current_paksha, is_day=False)
    day_periods = _build_periods(sunrise, sunset, day_seq, is_day=True)
    night_periods = _build_periods(sunset, next_sunrise, night_seq, is_day=False)

    parts = date_str.split("/")
    date_fmt = f"{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"

    return PanchaPakshiDay(
        date=date_fmt,
        sunrise=sunrise,
        sunset=sunset,
        paksha=current_paksha,
        birth_bird=birth_bird,
        day_periods=day_periods,
        night_periods=night_periods,
    )
