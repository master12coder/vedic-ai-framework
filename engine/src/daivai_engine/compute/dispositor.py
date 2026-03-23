"""Dispositor tree computation — trace sign lordship chains for all planets.

The dispositor of a planet is the lord of the sign it occupies. Following
each planet's dispositor chain reveals the ultimate "ruler" of the chart
(final dispositor) and any mutual reception (parivartana) pairs.

Rahu and Ketu do not own signs in the classical system; they are traced
through their sign lords but never serve as terminal dispositors.

Source: BPHS Ch.13, Phaladeepika Ch.2.
"""

from __future__ import annotations

from daivai_engine.constants import OWN_SIGNS, SIGN_LORDS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dispositor import (
    DispositorLink,
    DispositorTree,
    MutualReception,
    PlanetDispositorChain,
)


# Planets that can serve as final dispositors (classical lords only)
_CLASSICAL_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}

# Rahu/Ketu are traced but never terminate a chain as final dispositors
_SHADOW_PLANETS = {"Rahu", "Ketu"}


def _get_dispositor(planet_name: str, chart: ChartData) -> DispositorLink:
    """Return the dispositor link for a single planet.

    Args:
        planet_name: Name of the planet (e.g. "Mars").
        chart: Computed birth chart.

    Returns:
        DispositorLink with the planet, its sign, and its dispositor.
    """
    planet_data = chart.planets[planet_name]
    sign_idx = planet_data.sign_index
    dispositor = SIGN_LORDS[sign_idx]
    return DispositorLink(planet=planet_name, sign_index=sign_idx, dispositor=dispositor)


def _is_in_own_sign(planet_name: str, chart: ChartData) -> bool:
    """Check if a planet is in one of its own signs.

    Args:
        planet_name: Planet name.
        chart: Computed birth chart.

    Returns:
        True if the planet occupies one of its own signs.
    """
    if planet_name not in chart.planets:
        return False
    sign_idx = chart.planets[planet_name].sign_index
    own = OWN_SIGNS.get(planet_name, [])
    return sign_idx in own


def _trace_chain(planet_name: str, chart: ChartData) -> PlanetDispositorChain:
    """Trace the dispositor chain for a single planet.

    Follows: planet -> dispositor -> dispositor's dispositor -> ...
    Terminates when a planet in its own sign is reached (self-loop)
    or when a previously visited planet is encountered (mutual loop).

    Args:
        planet_name: Starting planet.
        chart: Computed birth chart.

    Returns:
        PlanetDispositorChain with the full chain and terminus.
    """
    chain: list[str] = [planet_name]
    visited: set[str] = {planet_name}
    current = planet_name
    is_loop = False

    while True:
        link = _get_dispositor(current, chart)
        next_planet = link.dispositor

        # Terminal: dispositor is in its own sign
        if _is_in_own_sign(next_planet, chart):
            if next_planet not in visited:
                chain.append(next_planet)
            elif next_planet != current:
                # Loop back to a visited planet
                is_loop = True
            return PlanetDispositorChain(
                planet=planet_name,
                chain=chain,
                final_dispositor=next_planet,
                chain_length=len(chain) - 1,
                is_in_loop=is_loop,
            )

        # Loop detection: already visited this planet
        if next_planet in visited:
            is_loop = True
            return PlanetDispositorChain(
                planet=planet_name,
                chain=chain,
                final_dispositor=next_planet,
                chain_length=len(chain) - 1,
                is_in_loop=is_loop,
            )

        chain.append(next_planet)
        visited.add(next_planet)
        current = next_planet


def _find_mutual_receptions(chart: ChartData) -> list[MutualReception]:
    """Find all mutual reception (parivartana) pairs in the chart.

    A mutual reception exists when planet A is in a sign owned by planet B
    and planet B is in a sign owned by planet A.

    Args:
        chart: Computed birth chart.

    Returns:
        List of MutualReception pairs (no duplicates).
    """
    receptions: list[MutualReception] = []
    seen_pairs: set[tuple[str, str]] = set()
    planets = [p for p in chart.planets if p in _CLASSICAL_PLANETS]

    for planet_a in planets:
        sign_a = chart.planets[planet_a].sign_index
        lord_of_a_sign = SIGN_LORDS[sign_a]

        if lord_of_a_sign == planet_a:
            continue  # Planet in own sign, not a mutual reception

        planet_b = lord_of_a_sign
        if planet_b not in chart.planets or planet_b not in _CLASSICAL_PLANETS:
            continue

        sign_b = chart.planets[planet_b].sign_index
        lord_of_b_sign = SIGN_LORDS[sign_b]

        if lord_of_b_sign == planet_a:
            sorted_pair = sorted([planet_a, planet_b])
            pair_key: tuple[str, str] = (sorted_pair[0], sorted_pair[1])
            if pair_key not in seen_pairs:
                seen_pairs.add(pair_key)
                receptions.append(
                    MutualReception(
                        planet_a=planet_a,
                        planet_b=planet_b,
                        sign_a=sign_a,
                        sign_b=sign_b,
                    )
                )

    return receptions


def _build_summary(
    final_dispositors: list[str],
    mutual_receptions: list[MutualReception],
    has_single: bool,
) -> str:
    """Build a human-readable summary of the dispositor structure.

    Args:
        final_dispositors: List of unique final dispositors.
        mutual_receptions: Mutual reception pairs.
        has_single: True if all chains converge to a single planet.

    Returns:
        Summary string.
    """
    parts: list[str] = []

    if has_single:
        parts.append(
            f"Single final dispositor: {final_dispositors[0]} — "
            f"this planet ultimately rules the entire chart."
        )
    else:
        parts.append(
            f"Multiple final dispositors: {', '.join(final_dispositors)}. "
            f"No single planet dominates the chart."
        )

    if mutual_receptions:
        pairs = [f"{mr.planet_a}-{mr.planet_b}" for mr in mutual_receptions]
        parts.append(f"Mutual receptions (parivartana): {', '.join(pairs)}.")

    return " ".join(parts)


def compute_dispositor_tree(chart: ChartData) -> DispositorTree:
    """Compute the full dispositor tree for all planets in a chart.

    Traces the dispositor chain for each planet, identifies mutual receptions,
    and determines whether a single final dispositor rules the chart.

    Source: BPHS Ch.13, Phaladeepika Ch.2.

    Args:
        chart: A fully computed birth chart with all planetary positions.

    Returns:
        DispositorTree with chains, final dispositors, and mutual receptions.
    """
    chains: dict[str, PlanetDispositorChain] = {}

    for planet_name in chart.planets:
        chains[planet_name] = _trace_chain(planet_name, chart)

    # Collect unique final dispositors (classical planets only)
    final_set: set[str] = set()
    for chain in chains.values():
        fd = chain.final_dispositor
        if fd in _CLASSICAL_PLANETS:
            final_set.add(fd)

    final_dispositors = sorted(final_set)
    mutual_receptions = _find_mutual_receptions(chart)
    has_single = len(final_dispositors) == 1

    summary = _build_summary(final_dispositors, mutual_receptions, has_single)

    return DispositorTree(
        chains=chains,
        final_dispositors=final_dispositors,
        mutual_receptions=mutual_receptions,
        has_single_final_dispositor=has_single,
        summary=summary,
    )
