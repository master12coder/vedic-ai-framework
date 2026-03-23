"""Transit event finder — sign ingress, stations, exact aspects.

Uses Swiss Ephemeris with binary search to locate the precise moments
of planetary transit events: sign ingress, retrograde/direct stations,
and exact aspects to natal positions.

Source: Surya Siddhanta (astronomical computation principles).
"""

from __future__ import annotations

from daivai_engine.compute.transit_finder_utils import (
    ASPECT_NAMES,
    BINARY_PRECISION,
    NO_RETROGRADE,
    angular_diff,
    jd_to_datetime,
    nakshatra_of,
    round_lon,
    sidereal_lon,
    sidereal_speed,
    sign_of,
    step_size,
)
from daivai_engine.constants import (
    SIGNS,
    SIGNS_EN,
)
from daivai_engine.models.transit_finder import (
    AspectEvent,
    IngressEvent,
    StationEvent,
)


# ── Backward-compatible aliases (used by eclipse_natal and tests) ──────────
_nakshatra_of = nakshatra_of
_sign_of = sign_of


# ── Public API ───────────────────────────────────────────────────────────────


def find_ingress(
    planet: str,
    target_sign: int,
    start_jd: float,
    end_jd: float,
) -> list[IngressEvent]:
    """Find all moments when *planet* enters *target_sign* in the period.

    Handles retrograde ingress (planet enters, retrogrades out, enters again).
    Uses day-stepping with binary search to ~1.4-minute precision.

    Args:
        planet: Planet name (e.g. "Saturn").
        target_sign: Sign index 0-11 (0=Aries).
        start_jd: Start Julian Day.
        end_jd: End Julian Day.

    Returns:
        List of IngressEvent sorted chronologically.

    Source: Surya Siddhanta — sign boundaries at 30-degree intervals.
    """
    events: list[IngressEvent] = []
    step = step_size(planet)
    jd = start_jd
    prev_sign = sign_of(sidereal_lon(jd, planet))

    while jd < end_jd:
        next_jd = min(jd + step, end_jd)
        cur_sign = sign_of(sidereal_lon(next_jd, planet))

        if cur_sign == target_sign and prev_sign != target_sign:
            # Binary search for exact crossing
            lo, hi = jd, next_jd
            while (hi - lo) > BINARY_PRECISION:
                mid = (lo + hi) / 2.0
                if sign_of(sidereal_lon(mid, planet)) == target_sign:
                    hi = mid
                else:
                    lo = mid

            exact_jd = hi
            lon = sidereal_lon(exact_jd, planet)
            dt = jd_to_datetime(exact_jd)

            events.append(
                IngressEvent(
                    planet=planet,
                    event_type="ingress",
                    date=dt,
                    julian_day=round(exact_jd, 6),
                    longitude=round_lon(lon),
                    sign_index=target_sign,
                    sign=SIGNS[target_sign],
                    description=f"{planet} enters {SIGNS_EN[target_sign]}",
                    target_sign_index=target_sign,
                    target_sign=SIGNS_EN[target_sign],
                )
            )

        prev_sign = cur_sign
        jd = next_jd

    return events


def find_stations(
    planet: str,
    start_jd: float,
    end_jd: float,
) -> list[StationEvent]:
    """Find retrograde and direct stations for *planet* in the period.

    Sun and Moon never go retrograde — returns empty list for them.

    Args:
        planet: Planet name.
        start_jd: Start Julian Day.
        end_jd: End Julian Day.

    Returns:
        List of StationEvent sorted chronologically.

    Source: Surya Siddhanta — stations where daily motion = 0.
    """
    if planet in NO_RETROGRADE:
        return []

    events: list[StationEvent] = []
    step = step_size(planet)
    jd = start_jd
    prev_speed = sidereal_speed(jd, planet)

    while jd < end_jd:
        next_jd = min(jd + step, end_jd)
        cur_speed = sidereal_speed(next_jd, planet)

        if prev_speed * cur_speed < 0:
            # Speed sign change detected — binary search for zero crossing
            lo, hi = jd, next_jd
            lo_speed = prev_speed
            while (hi - lo) > BINARY_PRECISION:
                mid = (lo + hi) / 2.0
                mid_speed = sidereal_speed(mid, planet)
                if lo_speed * mid_speed < 0:
                    hi = mid
                else:
                    lo = mid
                    lo_speed = mid_speed

            exact_jd = (lo + hi) / 2.0
            lon = sidereal_lon(exact_jd, planet)
            si = sign_of(lon)
            dt = jd_to_datetime(exact_jd)

            # positive->negative = retrograde station; negative->positive = direct
            if prev_speed > 0 and cur_speed < 0:
                event_type = "station_retrograde"
                desc = f"{planet} stations retrograde at {round(lon, 2)} deg in {SIGNS_EN[si]}"
            else:
                event_type = "station_direct"
                desc = f"{planet} stations direct at {round(lon, 2)} deg in {SIGNS_EN[si]}"

            events.append(
                StationEvent(
                    planet=planet,
                    event_type=event_type,
                    date=dt,
                    julian_day=round(exact_jd, 6),
                    longitude=round_lon(lon),
                    sign_index=si,
                    sign=SIGNS[si],
                    description=desc,
                    speed_before=round(prev_speed, 6),
                    speed_after=round(cur_speed, 6),
                )
            )

        prev_speed = cur_speed
        jd = next_jd

    return events


def find_exact_aspect(
    planet: str,
    natal_lon: float,
    aspect_degrees: float,
    start_jd: float,
    end_jd: float,
) -> list[AspectEvent]:
    """Find exact aspect hits of transiting *planet* to *natal_lon*.

    Args:
        planet: Transiting planet name.
        natal_lon: Natal sidereal longitude being aspected.
        aspect_degrees: 0=conjunction, 60=sextile, 90=square, 120=trine, 180=opposition.
        start_jd: Start Julian Day.
        end_jd: End Julian Day.

    Returns:
        List of AspectEvent sorted chronologically.

    Source: BPHS Ch.26 — standard Parashari aspect degrees.
    """
    from daivai_engine.constants import FULL_CIRCLE_DEG

    target = (natal_lon + aspect_degrees) % FULL_CIRCLE_DEG
    events: list[AspectEvent] = []
    step = step_size(planet)
    jd = start_jd
    prev_diff = angular_diff(sidereal_lon(jd, planet), target)

    while jd < end_jd:
        next_jd = min(jd + step, end_jd)
        cur_diff = angular_diff(sidereal_lon(next_jd, planet), target)

        # Zero crossing of the angular difference = exact aspect
        if prev_diff * cur_diff < 0 and abs(prev_diff) < 30 and abs(cur_diff) < 30:
            lo, hi = jd, next_jd
            lo_diff = prev_diff
            while (hi - lo) > BINARY_PRECISION:
                mid = (lo + hi) / 2.0
                mid_diff = angular_diff(sidereal_lon(mid, planet), target)
                if lo_diff * mid_diff < 0:
                    hi = mid
                else:
                    lo = mid
                    lo_diff = mid_diff

            exact_jd = (lo + hi) / 2.0
            lon = sidereal_lon(exact_jd, planet)
            si = sign_of(lon)
            dt = jd_to_datetime(exact_jd)
            orb = abs(angular_diff(lon, target))
            aspect_name = ASPECT_NAMES.get(aspect_degrees, f"{aspect_degrees}deg")

            events.append(
                AspectEvent(
                    planet=planet,
                    event_type="exact_aspect",
                    date=dt,
                    julian_day=round(exact_jd, 6),
                    longitude=round_lon(lon),
                    sign_index=si,
                    sign=SIGNS[si],
                    description=(
                        f"{planet} exact {aspect_name} to natal {round(natal_lon, 2)} deg"
                    ),
                    natal_longitude=round(natal_lon, 4),
                    aspect_type=aspect_name,
                    orb=round(orb, 4),
                )
            )

        prev_diff = cur_diff
        jd = next_jd

    return events
