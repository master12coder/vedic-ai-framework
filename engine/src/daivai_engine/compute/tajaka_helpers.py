"""Tajaka yoga helper functions — aspect computation and special yogas.

Provides: aspect computation, fast/slow determination, mutual reception,
Nakta (light transfer), Radda (blocking), Musaripha (transfer),
Manaou/Khallasara (no-aspect), Kamboola/Gairi-Kamboola (Moon yogas).

Sources: Tajaka Neelakanthi (Nilakantha), Dr. B.V. Raman's Varshphal.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.models.chart import ChartData, PlanetData


# Aspect distances in signs for Tajaka (sign-to-sign counting, 1-based)
_TAJAKA_ASPECT_SIGNS: set[int] = {1, 3, 4, 5, 7}

# Orb in degrees for Tajaka aspects
_TAJAKA_ORB: float = 5.0

# Planets ordered slowest to fastest (for fast/slow determination)
_SPEED_ORDER = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]


class _TajakaYogaProtocol:
    """Forward reference to avoid circular import — matched by TajakaYoga in tajaka_yogas."""

    name: str
    name_hi: str
    fast_planet: str
    slow_planet: str
    aspect_type: str
    orb: float
    is_applying: bool
    is_positive: bool
    description: str


def _compute_tajaka_aspect(
    p1: PlanetData,
    p2: PlanetData,
) -> tuple[str, float, bool] | None:
    """Compute Tajaka aspect between two planets.

    Returns (aspect_type, orb_degrees, is_applying) or None if no aspect.
    is_applying = True if p1 is moving toward exact aspect with p2.
    """
    sign_diff = abs(p1.sign_index - p2.sign_index)
    if sign_diff > 6:
        sign_diff = 12 - sign_diff

    aspect_map = {0: "conjunction", 2: "sextile", 3: "square", 4: "trine", 6: "opposition"}
    if sign_diff not in aspect_map:
        return None

    aspect_type = aspect_map[sign_diff]

    lon_diff = p1.longitude - p2.longitude
    while lon_diff > 180:
        lon_diff -= 360
    while lon_diff < -180:
        lon_diff += 360

    exact_diffs = {
        "conjunction": 0.0,
        "sextile": 60.0,
        "square": 90.0,
        "trine": 120.0,
        "opposition": 180.0,
    }
    exact = exact_diffs[aspect_type]
    orb = min(abs(abs(lon_diff) - exact), abs(360 - abs(lon_diff) - exact))

    if orb > _TAJAKA_ORB:
        return None

    is_applying = _is_applying(p1, p2, aspect_type, lon_diff)
    return aspect_type, round(orb, 2), is_applying


def _is_applying(
    p1: PlanetData,
    p2: PlanetData,
    aspect_type: str,
    lon_diff: float,
) -> bool:
    """Determine if p1 is applying to p2 for the given aspect."""
    if aspect_type == "conjunction":
        return lon_diff < 0 and p1.speed > p2.speed
    return p1.speed > 0 and abs(lon_diff) < (
        {"sextile": 60.0, "square": 90.0, "trine": 120.0, "opposition": 180.0}.get(aspect_type, 0.0)
    )


def _fast_slow(
    n1: str, p1: PlanetData, n2: str, p2: PlanetData
) -> tuple[str | None, str | None, PlanetData | None, PlanetData | None]:
    """Determine which of two planets is faster and which is slower."""
    try:
        idx1 = _SPEED_ORDER.index(n1)
        idx2 = _SPEED_ORDER.index(n2)
    except ValueError:
        return None, None, None, None

    if idx1 > idx2:
        return n1, n2, p1, p2
    return n2, n1, p2, p1


def _is_mutual_reception(n1: str, p1: PlanetData, n2: str, p2: PlanetData) -> bool:
    """Check if two planets are in mutual reception (each in the other's sign)."""
    return p1.sign_lord == n2 and p2.sign_lord == n1


def _check_nakta(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    moon: PlanetData,
) -> dict | None:
    """Check Nakta — Moon transfers light between fast and slow planets.

    Returns a TajakaYoga-compatible dict or None.
    """
    moon_to_slow = _compute_tajaka_aspect(moon, slow)
    fast_to_moon = _compute_tajaka_aspect(fast, moon)

    if moon_to_slow and moon_to_slow[2] and fast_to_moon and fast_to_moon[2]:
        return dict(
            name="Nakta",
            name_hi="नक्त",
            fast_planet=fast_name,
            slow_planet=slow_name,
            aspect_type="transfer_via_moon",
            orb=round((moon_to_slow[1] + fast_to_moon[1]) / 2, 2),
            is_applying=True,
            is_positive=True,
            description=(
                f"Moon transfers light from {fast_name} to {slow_name} — "
                "Nakta: indirect connection through Moon; results come via intermediary."
            ),
        )
    return None


def _find_blocking_planet(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
) -> str | None:
    """Find a planet that blocks the fast→slow applying aspect (Radda)."""
    for name, planet in chart.planets.items():
        if name in (fast_name, slow_name):
            continue
        f_lon = fast.longitude
        s_lon = slow.longitude
        p_lon = planet.longitude
        if _is_between_longitudes(f_lon, s_lon, p_lon):
            return name
    return None


def _is_between_longitudes(start: float, end: float, point: float) -> bool:
    """Check if point is between start and end on the zodiac circle."""
    if start <= end:
        return start < point < end
    return point > start or point < end


def check_no_aspect_yogas(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    yoga_class: type,
) -> list:
    """Check yogas that occur when no aspect exists between the pair.

    Args:
        yoga_class: The TajakaYoga class (passed in to avoid circular import).
    """
    results = []

    # 12. Manaou — no aspect connection
    results.append(
        yoga_class(
            name="Manaou",
            name_hi="मनाउ",
            fast_planet=fast_name,
            slow_planet=slow_name,
            aspect_type="none",
            orb=0.0,
            is_applying=False,
            is_positive=False,
            description=(
                f"{fast_name} and {slow_name} have no Tajaka aspect — "
                "Manaou: no connection; matters signified will not manifest."
            ),
        )
    )

    # 13. Khallasara — fast planet past slow with no new aspect forming
    if fast.degree_in_sign > slow.degree_in_sign and fast.speed > slow.speed:
        results.append(
            yoga_class(
                name="Khallasara",
                name_hi="खल्लासार",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type="none",
                orb=0.0,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} has overtaken {slow_name} with no aspect — "
                    "Khallasara: opportunity passed; no new application forming."
                ),
            )
        )

    return results


def check_moon_yogas(chart: ChartData, yogas: list, yoga_class: type) -> None:
    """Check Kamboola and Gairi-Kamboola (Moon-specific yogas).

    Args:
        yoga_class: The TajakaYoga class (passed in to avoid circular import).
    """
    moon = chart.planets.get("Moon")
    if not moon:
        return

    for name, planet in chart.planets.items():
        if name == "Moon":
            continue
        aspect = _compute_tajaka_aspect(moon, planet)
        if aspect is None:
            continue
        aspect_type, orb, is_applying = aspect

        # 14. Kamboola — Moon applying to another planet
        if is_applying:
            yogas.append(
                yoga_class(
                    name="Kamboola",
                    name_hi="कम्बूल",
                    fast_planet="Moon",
                    slow_planet=name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=True,
                    is_positive=True,
                    description=(
                        f"Moon applying {aspect_type} to {name} "
                        f"(orb {orb:.1f}°) — Kamboola: Moon empowers the application; "
                        "swift results through emotional/mental alignment."
                    ),
                )
            )

        # 15. Gairi-Kamboola — Moon separating from another planet
        if not is_applying and orb <= _TAJAKA_ORB:
            yogas.append(
                yoga_class(
                    name="Gairi-Kamboola",
                    name_hi="गैरी-कम्बूल",
                    fast_planet="Moon",
                    slow_planet=name,
                    aspect_type=aspect_type,
                    orb=orb,
                    is_applying=False,
                    is_positive=False,
                    description=(
                        f"Moon separating from {aspect_type} to {name} — "
                        "Gairi-Kamboola: matter initiated through Moon has passed its peak."
                    ),
                )
            )


def check_musaripha(
    fast_name: str,
    fast: PlanetData,
    slow_name: str,
    slow: PlanetData,
    chart: ChartData,
    yoga_class: type,
) -> Any | None:
    """16. Musaripha — fast planet separating from one and applying to another.

    Args:
        yoga_class: The TajakaYoga class (passed in to avoid circular import).
    """
    for other_name, other in chart.planets.items():
        if other_name in (fast_name, slow_name):
            continue
        other_asp = _compute_tajaka_aspect(fast, other)
        if other_asp and other_asp[2]:
            return yoga_class(
                name="Musaripha",
                name_hi="मुसारिफा",
                fast_planet=fast_name,
                slow_planet=slow_name,
                aspect_type="transfer",
                orb=0.0,
                is_applying=False,
                is_positive=False,
                description=(
                    f"{fast_name} separating from {slow_name} and applying to {other_name} — "
                    "Musaripha: energy transfers from old matter to new."
                ),
            )
    return None
