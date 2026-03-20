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
from daivai_engine.compute.vedha import check_vedha
from daivai_engine.models.chart import ChartData


# Gochara base scores per planet per house from Moon
# (from transit_rules.yaml — encoded here for runtime use)
_GOCHARA_SCORES: dict[str, dict[int, int]] = {
    "Saturn": {
        1: -1,
        2: -1,
        3: +1,
        4: -1,
        5: -1,
        6: +1,
        7: -1,
        8: -2,
        9: -1,
        10: -1,
        11: +2,
        12: -1,
    },
    "Jupiter": {
        1: -1,
        2: +1,
        3: -1,
        4: -1,
        5: +2,
        6: -1,
        7: +1,
        8: -1,
        9: +2,
        10: -1,
        11: +2,
        12: -1,
    },
    "Mars": {1: -1, 2: -1, 3: +2, 4: -1, 5: -1, 6: +2, 7: -1, 8: -2, 9: -1, 10: -1, 11: +2, 12: -1},
    "Sun": {1: -1, 2: -1, 3: +2, 4: -1, 5: -1, 6: +2, 7: -1, 8: -2, 9: -1, 10: +2, 11: +2, 12: -1},
    "Moon": {1: +1, 2: -1, 3: +1, 4: -1, 5: -1, 6: +1, 7: +2, 8: -1, 9: -1, 10: +2, 11: +2, 12: -1},
    "Mercury": {
        1: -1,
        2: +2,
        3: -1,
        4: +1,
        5: -1,
        6: +2,
        7: -1,
        8: +1,
        9: -1,
        10: +2,
        11: +2,
        12: -1,
    },
    "Venus": {
        1: +1,
        2: +2,
        3: +1,
        4: +2,
        5: +2,
        6: -1,
        7: -1,
        8: +1,
        9: +2,
        10: -1,
        11: +2,
        12: +2,
    },
    "Rahu": {1: -1, 2: -1, 3: +1, 4: -1, 5: -1, 6: +1, 7: -1, 8: -2, 9: -1, 10: +1, 11: +2, 12: -1},
    "Ketu": {1: -1, 2: -1, 3: +1, 4: -1, 5: -1, 6: +1, 7: -1, 8: -2, 9: -1, 10: +1, 11: +2, 12: +1},
}

# Ashtakavarga bindu → score modifier
_BINDU_MODIFIERS: list[tuple[range, int]] = [
    (range(0, 2), -2),  # 0-1 bindus: very unfavorable
    (range(2, 4), -1),  # 2-3 bindus: unfavorable
    (range(4, 5), 0),  # 4 bindus:   neutral
    (range(5, 7), +1),  # 5-6 bindus: favorable
    (range(7, 9), +2),  # 7-8 bindus: very favorable
]

_SCORE_LABELS: dict[int, str] = {
    -4: "Very unfavorable",
    -3: "Unfavorable",
    -2: "Unfavorable",
    -1: "Slightly unfavorable",
    0: "Neutral",
    1: "Slightly favorable",
    2: "Favorable",
    3: "Favorable",
    4: "Very favorable",
}


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
    descriptions: dict[str, dict[int, str]] = {
        "Saturn": {
            1: "Obstacles, health issues (Sade Sati peak)",
            2: "Financial strain (Sade Sati setting)",
            3: "Success, valour",
            4: "Mental distress, property issues",
            5: "Children issues, mind disturbance",
            6: "Victory over enemies",
            7: "Travel, relationship strain",
            8: "Health crises, major losses",
            9: "Obstacles in fortune",
            10: "Career setbacks (Kantak Shani)",
            11: "Gains, prosperity",
            12: "Expenses, losses (Sade Sati rising)",
        },
        "Jupiter": {
            1: "Restlessness, loss of wealth",
            2: "Financial gains, family happiness",
            3: "Obstacles in journeys",
            4: "Property disputes",
            5: "Children's blessings, spiritual growth",
            6: "Health issues, enemy troubles",
            7: "Marriage prospects, partnerships",
            8: "Hidden troubles",
            9: "Fortune, guru blessings",
            10: "Career stagnation",
            11: "Excellent gains, aspirations fulfilled",
            12: "Expenditure, spiritual retreat",
        },
        "Mars": {
            1: "Accidents, fever, conflicts",
            2: "Financial losses, quarrels",
            3: "Courage, victory over enemies",
            4: "Property disputes, domestic conflict",
            5: "Children troubles, stomach issues",
            6: "Victory over enemies, good health",
            7: "Marital discord",
            8: "Accidents, surgeries",
            9: "Father's troubles, loss of fortune",
            10: "Career conflicts",
            11: "Gains, competitive success",
            12: "Secret enemies, expenses",
        },
        "Sun": {
            1: "Health issues, low energy",
            2: "Financial losses, family disputes",
            3: "Courage, good health",
            4: "Mental agitation",
            5: "Children troubles, loss of respect",
            6: "Victory over enemies, government favor",
            7: "Marital tension",
            8: "Health crises, fever",
            9: "Father's troubles, loss of fortune",
            10: "Career success, leadership",
            11: "Financial gains, ambitions fulfilled",
            12: "Eye problems, expenses",
        },
        "Moon": {
            1: "Good health, mental clarity",
            2: "Financial fluctuation",
            3: "Mental strength, travel success",
            4: "Mental unease",
            5: "Worries about children",
            6: "Good health, victory",
            7: "Good relationships, social ease",
            8: "Mental depression",
            9: "Obstacles in fortune",
            10: "Career success, recognition",
            11: "Financial gains, popularity",
            12: "Expenditure, fatigue",
        },
        "Mercury": {
            1: "Mental restlessness",
            2: "Financial gains, eloquent speech",
            3: "Sibling issues",
            4: "Property benefits, harmony",
            5: "Intellectual restlessness",
            6: "Victory through intellect",
            7: "Communication breakdowns",
            8: "Occult knowledge, research",
            9: "Travel delays",
            10: "Career success through communication",
            11: "Gains through intellect",
            12: "Mental confusion, expenses",
        },
        "Venus": {
            1: "Attractiveness, comfort",
            2: "Wealth gains, luxury",
            3: "Pleasant journeys, artistic success",
            4: "Domestic happiness, property gains",
            5: "Romance, children's blessings",
            6: "Relationship disputes",
            7: "Marital difficulties",
            8: "Inheritance, sensual pleasures",
            9: "Fortune, spiritual comfort",
            10: "Career not favored",
            11: "Excellent gains, luxury",
            12: "Pleasures in privacy, spiritual comfort",
        },
        "Rahu": {
            1: "Mental confusion, illusions",
            2: "Financial irregularities",
            3: "Unconventional courage",
            4: "Domestic upheaval",
            5: "Obsessive thinking, speculation",
            6: "Enemies overcome through shrewdness",
            7: "Unusual partnerships",
            8: "Hidden enemies, sudden crises",
            9: "Religious confusion",
            10: "Unconventional career success",
            11: "Material gains, large aspirations",
            12: "Hidden expenditure, fears",
        },
        "Ketu": {
            1: "Spiritual seeking, identity dissolution",
            2: "Financial losses, family detachment",
            3: "Spiritual journeys, isolation",
            4: "Domestic detachment",
            5: "Past-life karma surfacing",
            6: "Enemies subdued through karma",
            7: "Relationship detachment",
            8: "Occult experiences, transformation",
            9: "Guru detachment, dharmic questioning",
            10: "Career through spirituality",
            11: "Spiritual gains, renunciation",
            12: "Moksha inclinations, liberation",
        },
    }
    planet_map = descriptions.get(planet, {})
    return planet_map.get(house, f"{planet} in house {house} from Moon")
