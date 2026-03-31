"""Tajaka composite yoga checks — no-aspect, Moon, and transfer yogas.

Provides: Manaou, Khallasara, Kamboola, Gairi-Kamboola, Musaripha detection.
These use the core aspect primitives from tajaka_helpers.

Sources: Tajaka Neelakanthi (Nilakantha), Dr. B.V. Raman's Varshphal.
"""

from __future__ import annotations

from typing import Any

from daivai_engine.compute.tajaka_helpers import (
    _TAJAKA_ORB,
    _compute_tajaka_aspect,
)
from daivai_engine.models.chart import ChartData, PlanetData


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
