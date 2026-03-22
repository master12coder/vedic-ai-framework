"""Transit scoring — Gochara results with Ashtakavarga and Vedha modifiers.

Combines three layers:
1. Gochara result: inherent favorability of the transit house from natal Moon
2. Ashtakavarga modifier: bindu count in the transiting sign
3. Vedha modifier: beneficial transits are cancelled when a natal planet
   occupies the vedha house

Source: Phaladeepika Ch.26, BPHS transit chapter.
"""

from __future__ import annotations

from pydantic import BaseModel

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.transit_scoring_tables import (
    _BINDU_MODIFIERS,
    _GOCHARA_DESCRIPTIONS,
    _GOCHARA_SCORES,
    _SCORE_LABELS,
)
from daivai_engine.compute.vedha import check_vedha
from daivai_engine.models.chart import ChartData


class TransitScore(BaseModel):
    """Scored transit result for a single planet."""

    planet: str
    transit_sign_index: int
    house_from_moon: int  # 1-12
    gochara_score: int  # Raw gochara result (-2 to +2)
    bindu_count: int  # Ashtakavarga bindus in transit sign
    bindu_modifier: int  # Ashtakavarga modifier (-2 to +2)
    vedha_active: bool  # Whether vedha blocks beneficial effect
    final_score: int  # Combined score (may be 0 if vedha blocks benefit)
    label: str  # Human-readable label
    description: str  # Gochara result description


def compute_transit_scores(
    chart: ChartData,
    transit_sign_map: dict[str, int],
) -> list[TransitScore]:
    """Compute scored transit results for all planets.

    Combines gochara (house-from-Moon) result with Ashtakavarga bindu
    count and Vedha obstruction.

    Args:
        chart: Natal birth chart.
        transit_sign_map: Dict mapping planet name to current transit
            sign index (0-11). E.g. {"Saturn": 3, "Jupiter": 7, ...}

    Returns:
        List of TransitScore, one per planet, sorted by final_score descending.
    """
    moon_sign = chart.planets["Moon"].sign_index
    ak_result = compute_ashtakavarga(chart)

    # Build BAV lookup: planet -> list[int] of 12 bindu counts by sign
    bav_by_planet: dict[str, list[int]] = ak_result.bhinna

    scores: list[TransitScore] = []
    for planet_name, transit_sign in transit_sign_map.items():
        house_from_moon = ((transit_sign - moon_sign) % 12) + 1
        gochara = _GOCHARA_SCORES.get(planet_name, {}).get(house_from_moon, 0)

        # Ashtakavarga bindus (Rahu/Ketu not in BAV tables — use 4 as neutral)
        if planet_name in bav_by_planet:
            bindus = bav_by_planet[planet_name][transit_sign]
        else:
            bindus = 4

        bindu_mod = _get_bindu_modifier(bindus)

        # Vedha check: only apply to beneficial gochara positions
        vedha_active = False
        if gochara > 0:
            vedha_points = check_vedha(chart, planet_name, transit_sign)
            if vedha_points and vedha_points[0].is_blocked:
                vedha_active = True

        # Final score: if vedha blocks benefit, score = 0; otherwise combined
        if vedha_active:
            final = 0
        else:
            final = max(-4, min(4, gochara + bindu_mod))

        label = _SCORE_LABELS.get(final, "Neutral")
        description = _get_gochara_description(planet_name, house_from_moon)

        scores.append(
            TransitScore(
                planet=planet_name,
                transit_sign_index=transit_sign,
                house_from_moon=house_from_moon,
                gochara_score=gochara,
                bindu_count=bindus,
                bindu_modifier=bindu_mod,
                vedha_active=vedha_active,
                final_score=final,
                label=label,
                description=description,
            )
        )

    scores.sort(key=lambda x: x.final_score, reverse=True)
    return scores


def _get_bindu_modifier(bindus: int) -> int:
    """Map bindu count to score modifier."""
    for rng, mod in _BINDU_MODIFIERS:
        if bindus in rng:
            return mod
    return 0


def _get_gochara_description(planet: str, house: int) -> str:
    """Short human-readable description of gochara result."""
    planet_map = _GOCHARA_DESCRIPTIONS.get(planet, {})
    return planet_map.get(house, f"{planet} in house {house} from Moon")
