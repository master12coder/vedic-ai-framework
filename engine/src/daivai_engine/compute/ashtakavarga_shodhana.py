"""Ashtakavarga Shodhana (purification/reduction) techniques — BPHS Ch.71.

Implements three classical refinement steps that convert raw Ashtakavarga
bindu tables into usable predictive data:

  1. Trikona Shodhana  — remove the repeated base level within each set of
                         three trine signs (1-5-9, 2-6-10, 3-7-11, 4-8-12).
  2. Ekadhipatya Shodhana — for each pair of signs ruled by the same planet,
                             keep only the stronger or node-occupied sign.
  3. Shodhya Pinda     — weighted totals (Rasi Pinda + Graha Pinda) derived
                         from the Trikona-reduced Bhinnashtakavarga.

Typical usage::

    av = compute_ashtakavarga(chart)
    shodha = compute_shodhana(chart, av)
    pinda = compute_shodhya_pinda(shodha.reduced_bhinna)
"""

from __future__ import annotations

from daivai_engine.constants import GRAHA_GUNAKARA, RASI_GUNAKARA
from daivai_engine.models.ashtakavarga import (
    AshtakavargaResult,
    ShodhanaResult,
    ShodhyaPindaResult,
)
from daivai_engine.models.chart import ChartData


# The 7 planets used in Ashtakavarga (Rahu/Ketu excluded per BPHS).
_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# ---------------------------------------------------------------------------
# Trikona groups — zero-indexed sign triplets that form trine relationships.
# Signs within a group share the same element (Fire/Earth/Air/Water).
# ---------------------------------------------------------------------------
_TRIKONA_GROUPS: list[tuple[int, int, int]] = [
    (0, 4, 8),  # Aries, Leo, Sagittarius  (Fire)
    (1, 5, 9),  # Taurus, Virgo, Capricorn (Earth)
    (2, 6, 10),  # Gemini, Libra, Aquarius  (Air)
    (3, 7, 11),  # Cancer, Scorpio, Pisces   (Water)
]

# ---------------------------------------------------------------------------
# Dual-owned sign pairs for Ekadhipatya Shodhana (0-indexed).
# Each tuple is (sign_a, sign_b) owned by the same planet.
# Single-ruled signs — Cancer(3)=Moon, Leo(4)=Sun — are excluded.
# ---------------------------------------------------------------------------
_DUAL_OWNED_PAIRS: list[tuple[int, int]] = [
    (0, 7),  # Mars   : Aries, Scorpio
    (1, 6),  # Venus  : Taurus, Libra
    (2, 5),  # Mercury: Gemini, Virgo
    (8, 11),  # Jupiter: Sagittarius, Pisces
    (9, 10),  # Saturn : Capricorn, Aquarius
]

# Odd signs in Vedic numbering (1-based): Aries=1, Gemini=3, Leo=5, Libra=7,
# Sagittarius=9, Aquarius=11 — mapped to 0-indexed.
_ODD_SIGNS: frozenset[int] = frozenset({0, 2, 4, 6, 8, 10})


def trikona_shodhana(bindus: list[int]) -> list[int]:
    """Apply Trikona Shodhana to a 12-sign bindu list — BPHS Ch.71.

    For each of the four trikona groups (Aries-Leo-Sagittarius, etc.),
    find the minimum bindu value among the three signs and subtract it
    from all three.  This removes the "base level" that repeats across
    trines, leaving only differential planetary strength.

    Args:
        bindus: 12-element list of bindu values (one per sign, Aries-first).
                All values must be ≥ 0.

    Returns:
        New 12-element list with trikona reduction applied.  Within each
        trikona group the minimum value is guaranteed to be 0.
    """
    result = list(bindus)
    for a, b, c in _TRIKONA_GROUPS:
        minimum = min(result[a], result[b], result[c])
        result[a] -= minimum
        result[b] -= minimum
        result[c] -= minimum
    return result


def ekadhipatya_shodhana(
    sarva: list[int],
    rahu_sign: int,
    ketu_sign: int,
) -> list[int]:
    """Apply Ekadhipatya Shodhana to a 12-sign SAV list — BPHS Ch.71.

    For each pair of signs ruled by the same planet, one sign's value is
    preserved and the other is reduced to zero according to these rules:

    * If exactly one sign in the pair contains Rahu or Ketu, that sign's
      value is kept unchanged; the other becomes 0.
    * If neither sign contains a node and their values differ, the sign
      with more bindus keeps (its value - the other's); the weaker becomes 0.
    * If neither sign contains a node and values are equal, the sign with
      an odd Vedic number (Aries=1, Gemini=3, …, Aquarius=11) keeps its
      value; the even sign becomes 0.

    Single-ruled signs (Cancer = Moon; Leo = Sun) are not touched.

    Args:
        sarva:     12-element SAV list, typically after Trikona Shodhana.
        rahu_sign: 0-indexed sign index occupied by Rahu.
        ketu_sign: 0-indexed sign index occupied by Ketu.

    Returns:
        New 12-element list with Ekadhipatya reduction applied.
    """
    result = list(sarva)
    nodes: frozenset[int] = frozenset({rahu_sign, ketu_sign})

    for a, b in _DUAL_OWNED_PAIRS:
        a_has_node = a in nodes
        b_has_node = b in nodes

        if a_has_node and not b_has_node:
            result[b] = 0
        elif b_has_node and not a_has_node:
            result[a] = 0
        else:
            # Neither (or both) have nodes — compare bindu counts.
            va, vb = result[a], result[b]
            if va > vb:
                result[a] = va - vb
                result[b] = 0
            elif vb > va:
                result[b] = vb - va
                result[a] = 0
            else:
                # Equal values: odd Vedic sign keeps; even becomes 0.
                if a in _ODD_SIGNS:
                    result[b] = 0
                else:
                    result[a] = 0

    return result


def compute_shodhana(
    chart: ChartData,
    av: AshtakavargaResult,
) -> ShodhanaResult:
    """Apply both Shodhana reductions to an AshtakavargaResult.

    Step 1 — Trikona Shodhana on each of the 7 planets' BAV tables.
    Step 2 — Trikona Shodhana on the Sarvashtakavarga.
    Step 3 — Ekadhipatya Shodhana on the trikona-reduced SAV, using the
              birth chart's Rahu and Ketu sign positions.

    Args:
        chart: Fully computed birth chart (Rahu/Ketu positions are read
               from ``chart.planets``).
        av:    Precomputed AshtakavargaResult from
               ``compute_ashtakavarga(chart)``.

    Returns:
        ShodhanaResult containing the reduced Bhinna tables, the
        intermediate trikona-reduced SAV, and the fully reduced SAV.
    """
    # Step 1: Trikona Shodhana on each planet's BAV.
    reduced_bhinna: dict[str, list[int]] = {
        planet: trikona_shodhana(av.bhinna[planet]) for planet in _PLANETS
    }

    # Step 2: Trikona Shodhana on SAV.
    trikona_sarva = trikona_shodhana(av.sarva)

    # Step 3: Ekadhipatya Shodhana on the trikona-reduced SAV.
    rahu_sign = chart.planets["Rahu"].sign_index
    ketu_sign = chart.planets["Ketu"].sign_index
    reduced_sarva = ekadhipatya_shodhana(trikona_sarva, rahu_sign, ketu_sign)

    return ShodhanaResult(
        reduced_bhinna=reduced_bhinna,
        trikona_sarva=trikona_sarva,
        reduced_sarva=reduced_sarva,
    )


def compute_shodhya_pinda(
    reduced_bhinna: dict[str, list[int]],
) -> dict[str, ShodhyaPindaResult]:
    """Compute Shodhya Pinda scores for all 7 planets — BPHS Ch.71.

    For each planet:
      Rasi Pinda  = sum(reduced_bindu[sign] * RASI_GUNAKARA[sign])
      Graha Pinda = GRAHA_GUNAKARA[planet] * sum(reduced_bindu[sign])
      Shodhya Pinda = Rasi Pinda + Graha Pinda

    The Rasi Gunakara weights each sign's contribution by its inherent
    strength; the Graha Gunakara weights the planet's total reduced bindus
    by the planet's own significance.

    Args:
        reduced_bhinna: Per-planet BAV after Trikona Shodhana.  Keys are
                        planet names (Sun … Saturn); values are 12-element
                        lists (Aries-first).

    Returns:
        Dict mapping planet name → ShodhyaPindaResult.
    """
    results: dict[str, ShodhyaPindaResult] = {}
    for planet in _PLANETS:
        bindus = reduced_bhinna[planet]
        rasi_pinda = sum(b * RASI_GUNAKARA[i] for i, b in enumerate(bindus))
        graha_pinda = GRAHA_GUNAKARA[planet] * sum(bindus)
        results[planet] = ShodhyaPindaResult(
            planet=planet,
            rasi_pinda=rasi_pinda,
            graha_pinda=graha_pinda,
            shodhya_pinda=rasi_pinda + graha_pinda,
        )
    return results
