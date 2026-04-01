"""Rashifal scoring engine — transit positions, gochara scores, domain predictions.

Extracted from rashifal.py to comply with the 300-line rule. Contains the
computation logic: Swiss Ephemeris transit lookups, Gochara score table
application, day rating computation, and domain-specific prediction generation.

Source: Phaladeepika Ch.26 (Gochara scores).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import swisseph as swe
import yaml

from daivai_engine.constants import (
    DAY_PLANET,
    DEGREES_PER_SIGN,
    NUM_SIGNS,
    PLANETS,
    SWE_PLANETS,
)


# ── YAML data paths ──────────────────────────────────────────────────────────
_GOCHARA_YAML_PATH = (
    Path(__file__).resolve().parents[5]
    / "engine"
    / "src"
    / "daivai_engine"
    / "knowledge"
    / "gochara_rules.yaml"
)
_MANTRAS_YAML_PATH = (
    Path(__file__).resolve().parents[5]
    / "engine"
    / "src"
    / "daivai_engine"
    / "knowledge"
    / "mantras.yaml"
)

_GOCHARA_DATA: dict[str, Any] | None = None
_MANTRAS_DATA: dict[str, Any] | None = None


def load_gochara() -> dict[str, Any]:
    """Load and cache gochara scores from YAML."""
    global _GOCHARA_DATA
    if _GOCHARA_DATA is None:
        with open(_GOCHARA_YAML_PATH) as f:
            _GOCHARA_DATA = yaml.safe_load(f)
    return _GOCHARA_DATA


def load_mantras() -> dict[str, Any]:
    """Load and cache mantra data from YAML."""
    global _MANTRAS_DATA
    if _MANTRAS_DATA is None:
        with open(_MANTRAS_YAML_PATH) as f:
            _MANTRAS_DATA = yaml.safe_load(f)
    return _MANTRAS_DATA


# ── Planet colors (day lord color for lucky color) ───────────────────────────

_PLANET_COLORS: dict[str, str] = {
    "Sun": "Red",
    "Moon": "White",
    "Mars": "Orange",
    "Mercury": "Green",
    "Jupiter": "Yellow",
    "Venus": "Pink",
    "Saturn": "Blue",
}

# House domains for rashifal categories
CAREER_HOUSES = {10, 6, 2}  # 10th primary, 6th service, 2nd wealth
FINANCE_HOUSES = {2, 11, 5}  # 2nd income, 11th gains, 5th speculation
HEALTH_HOUSES = {1, 6, 8}  # 1st body, 6th disease, 8th longevity
LOVE_HOUSES = {7, 5, 4}  # 7th partner, 5th romance, 4th happiness


# ── Transit position computation ─────────────────────────────────────────────


def get_current_positions(target: date) -> dict[str, int]:
    """Get current sidereal sign index for each planet.

    Uses Swiss Ephemeris with Lahiri ayanamsha, same method as chart.py.

    Returns:
        Dict mapping planet name to 0-based sign index.
    """
    # Julian Day at ~00:00 UTC (approximately sunrise IST for India-centric rashifal)
    hour_frac = 0.0
    jd = swe.julday(target.year, target.month, target.day, hour_frac)

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    positions: dict[str, int] = {}
    for planet_name in PLANETS:
        if planet_name == "Ketu":
            rahu_sign = positions["Rahu"]
            positions["Ketu"] = (rahu_sign + 6) % NUM_SIGNS
            continue

        swe_id = SWE_PLANETS[planet_name]
        result = swe.calc_ut(jd, swe_id, swe.FLG_SIDEREAL)
        lon = result[0][0]
        positions[planet_name] = int(lon / DEGREES_PER_SIGN)

    return positions


# ── Scoring engine ───────────────────────────────────────────────────────────


def house_from_sign(planet_sign: int, base_sign: int) -> int:
    """Compute 1-based house number of planet from base sign.

    House 1 = same sign as base, House 2 = next sign, etc.
    """
    return ((planet_sign - base_sign) % NUM_SIGNS) + 1


def compute_sign_scores(
    sign_index: int,
    positions: dict[str, int],
    gochara_scores: dict[str, list[int]],
) -> dict[str, int]:
    """Compute gochara score for each planet relative to a sign.

    Returns:
        Dict mapping planet name to gochara score (-2 to +2).
    """
    scores: dict[str, int] = {}
    for planet_name, planet_sign in positions.items():
        house = house_from_sign(planet_sign, sign_index)
        planet_scores = gochara_scores.get(planet_name)
        if planet_scores:
            scores[planet_name] = planet_scores[house - 1]
        else:
            scores[planet_name] = 0
    return scores


def day_rating_from_scores(scores: dict[str, int]) -> int:
    """Convert per-planet gochara scores into a 1-10 day rating.

    Weighting: slow movers (Jupiter, Saturn, Rahu, Ketu) carry more weight
    because their transits are more impactful. Fast movers (Moon, Sun, Mercury)
    carry less.
    """
    weights = {
        "Jupiter": 3.0,
        "Saturn": 3.0,
        "Rahu": 2.0,
        "Ketu": 2.0,
        "Mars": 1.5,
        "Venus": 1.5,
        "Sun": 1.0,
        "Moon": 1.0,
        "Mercury": 1.0,
    }
    total_weighted = sum(scores.get(p, 0) * weights.get(p, 1.0) for p in scores)
    total_weight = sum(weights.get(p, 1.0) for p in scores)

    # Normalize: scores range from -2 to +2, so weighted avg is in [-2, 2].
    # Map [-2, 2] -> [1, 10]
    avg = total_weighted / total_weight if total_weight else 0.0
    rating = round((avg + 2) / 4.0 * 9.0 + 1)
    return max(1, min(10, rating))


def domain_prediction(
    positions: dict[str, int],
    sign_index: int,
    domain_houses: set[int],
    gochara_results: dict[str, dict[int, str]],
) -> str:
    """Generate a domain-specific prediction based on house activations.

    Finds planets in the relevant houses and builds a summary from
    gochara result descriptions.
    """
    parts: list[str] = []
    for planet_name, planet_sign in positions.items():
        house = house_from_sign(planet_sign, sign_index)
        if house in domain_houses:
            planet_results = gochara_results.get(planet_name, {})
            desc = planet_results.get(house, "")
            if desc:
                parts.append(desc)

    if not parts:
        return "A stable and routine period. No major transits affecting this area."

    return " ".join(parts[:2])  # Cap at 2 descriptions for conciseness


def pick_remedy(
    scores: dict[str, int],
    mantras: dict[str, Any],
) -> tuple[str, str]:
    """Pick remedy and mantra for the weakest-scoring planet.

    Finds the planet with the lowest gochara score (most unfavorable transit)
    and recommends its mantra as remedy.

    Returns:
        Tuple of (remedy_text, mantra_text).
    """
    # Find worst-scoring planet (prefer slow movers on tie)
    priority = [
        "Saturn",
        "Jupiter",
        "Rahu",
        "Ketu",
        "Mars",
        "Venus",
        "Sun",
        "Moon",
        "Mercury",
    ]
    worst_planet = "Saturn"
    worst_score = 3

    for planet in priority:
        score = scores.get(planet, 0)
        if score < worst_score:
            worst_score = score
            worst_planet = planet

    mantra_data = mantras.get(worst_planet, {})
    mantra_text = mantra_data.get("mantra", f"Om {worst_planet}aya Namaha")

    remedy = (
        f"Chant {worst_planet} mantra {mantra_data.get('count', 11)} times. "
        f"Donate {mantra_data.get('color', 'white').split('/')[0].lower()} items "
        f"on {mantra_data.get('day', worst_planet + 'day')}."
    )

    return remedy, mantra_text


def lucky_color(target: date) -> str:
    """Derive lucky color from the day lord (vara planet)."""
    weekday = target.weekday()
    # Python weekday: 0=Mon, need to map to our DAY_PLANET (0=Sun)
    # Sunday=6 in Python -> 0 in our map
    day_index = (weekday + 1) % 7
    day_planet = DAY_PLANET.get(day_index, "Sun")
    return _PLANET_COLORS.get(day_planet, "White")


def lucky_number(sign_index: int, target: date) -> int:
    """Derive lucky number from sign index and day.

    Uses sign index (1-12) + day-of-month mod, kept in 1-9 range.
    """
    raw = (sign_index + 1 + target.day) % 9
    return raw if raw > 0 else 9
