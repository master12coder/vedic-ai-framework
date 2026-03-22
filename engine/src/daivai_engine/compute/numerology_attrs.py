"""Vedic Numerology attribute lookups, Yantra generation, and compatibility.

Handles three independent concerns:
- Planet number attributes (lucky items, personality, gemstone, direction).
- 3x3 magic square (Yantra) generation by scaling the Lo Shu.
- Pairwise compatibility scoring from the 9x9 planetary friendship matrix.
- Compound number (10-52) Chaldean meanings.

All data is loaded from engine/knowledge/numerology_rules.yaml.
Does NOT import from daivai_engine.compute.numerology to avoid circular deps.
"""

from __future__ import annotations

from daivai_engine.exceptions import ValidationError
from daivai_engine.knowledge.loader import load_numerology_rules
from daivai_engine.models.numerology import (
    CompatibilityResult,
    NumberAttributes,
    NumerologyYantra,
)


# ── Lo Shu base square ────────────────────────────────────────────────────────
# Multiply every cell by planet number N to get a magic square
# with magic constant = 15 x N.
#   4  9  2
#   3  5  7
#   8  1  6

_LO_SHU_BASE: list[list[int]] = [
    [4, 9, 2],
    [3, 5, 7],
    [8, 1, 6],
]

_MASTER_NUMBERS: frozenset[int] = frozenset({11, 22, 33})


def _reduce_to_base(n: int) -> int:
    """Reduce master number to its single-digit base (11->2, 22->4, 33->6).

    Used locally so this module stays independent of numerology.py.
    """
    result = n
    while result > 9:
        result = sum(int(d) for d in str(result))
    return result


def generate_yantra(number: int) -> NumerologyYantra:
    """Generate a 3x3 magic square (Yantra) for a planet number.

    Multiplies the classical Lo Shu square by the given number, producing
    a magic square with magic constant = 15 x number.

    Args:
        number: Planet number (1-9).

    Returns:
        NumerologyYantra with 3x3 grid and magic constant.

    Raises:
        ValidationError: If number is not in range 1-9.

    Example:
        generate_yantra(4)
        → [[16,36,8],[12,20,28],[32,4,24]], magic_constant=60
    """
    if not 1 <= number <= 9:
        raise ValidationError(f"Yantra number must be 1-9, got {number}")

    rules = load_numerology_rules()
    planet = str(rules.get("planet_numbers", {}).get(number, "Unknown"))

    grid = [[cell * number for cell in row] for row in _LO_SHU_BASE]
    magic_constant = 15 * number

    return NumerologyYantra(
        number=number,
        planet=planet,
        grid=grid,
        magic_constant=magic_constant,
    )


def compute_compatibility(n1: int, n2: int) -> CompatibilityResult:
    """Compute numerology compatibility between two numbers.

    Scores are based on Vedic planetary friendship (BPHS Chapter 7) and
    loaded from engine/knowledge/numerology_rules.yaml.

    Args:
        n1: First numerology number (1-9).
        n2: Second numerology number (1-9).

    Returns:
        CompatibilityResult with score (0-100) and qualitative category.

    Raises:
        ValidationError: If either number is outside 1-9.
    """
    if not 1 <= n1 <= 9:
        raise ValidationError(f"Number must be 1-9, got {n1}")
    if not 1 <= n2 <= 9:
        raise ValidationError(f"Number must be 1-9, got {n2}")

    rules = load_numerology_rules()
    matrix: dict[int, dict[int, int]] = rules.get("compatibility_matrix", {})
    planets: dict[int, str] = rules.get("planet_numbers", {})
    categories: dict[str, dict] = rules.get("compatibility_categories", {})

    score: int = matrix.get(n1, {}).get(n2, 50)
    planet1 = str(planets.get(n1, "Unknown"))
    planet2 = str(planets.get(n2, "Unknown"))

    category = "Challenging"
    category_hi = "kaThin"
    for cat_key in ["excellent", "good", "moderate", "challenging"]:
        defn = categories.get(cat_key, {})
        if score >= defn.get("min", 0):
            category = defn.get("label", cat_key.title())
            category_hi = defn.get("label_hi", category)
            break

    description = (
        f"{planet1} ({n1}) and {planet2} ({n2}) have {category.lower()} compatibility. "
        f"Score: {score}/100."
    )

    return CompatibilityResult(
        number1=n1,
        number2=n2,
        planet1=planet1,
        planet2=planet2,
        score=score,
        category=category,
        category_hi=category_hi,
        description=description,
    )


def get_number_attributes(number: int) -> NumberAttributes:
    """Load lucky and astrological attributes for a numerology number.

    Args:
        number: Numerology number (1-9). Master numbers are reduced first.

    Returns:
        NumberAttributes with planet, lucky items, and personality traits.

    Raises:
        ValidationError: If number is outside 1-9 (after master reduction).
    """
    base = _reduce_to_base(number) if number in _MASTER_NUMBERS else number

    if not 1 <= base <= 9:
        raise ValidationError(f"Number must be 1-9 (or master 11/22/33), got {number}")

    rules = load_numerology_rules()
    attrs: dict = rules.get("number_attributes", {}).get(base, {})

    return NumberAttributes(
        number=base,
        planet=str(attrs.get("planet", "Unknown")),
        planet_hi=str(attrs.get("planet_hi", "")),
        lucky_days=list(attrs.get("lucky_days", [])),
        lucky_colors=list(attrs.get("lucky_colors", [])),
        lucky_gemstone=str(attrs.get("lucky_gemstone", "")),
        lucky_gemstone_hi=str(attrs.get("lucky_gemstone_hi", "")),
        lucky_direction=str(attrs.get("lucky_direction", "")),
        lucky_direction_hi=str(attrs.get("lucky_direction_hi", "")),
        friendly_numbers=list(attrs.get("friendly_numbers", [])),
        neutral_numbers=list(attrs.get("neutral_numbers", [])),
        enemy_numbers=list(attrs.get("enemy_numbers", [])),
        strengths=list(attrs.get("strengths", [])),
        weaknesses=list(attrs.get("weaknesses", [])),
        deity=str(attrs.get("deity", "")),
        deity_hi=str(attrs.get("deity_hi", "")),
        mantra=str(attrs.get("mantra", "")),
        description=str(attrs.get("description", "")),
    )


def get_compound_number_meaning(compound: int) -> str:
    """Return the Chaldean compound number name and meaning for a value 10-52.

    Args:
        compound: Compound number (10-52).

    Returns:
        Formatted string with name and meaning, or empty string if not found.
    """
    if not 10 <= compound <= 52:
        return ""

    rules = load_numerology_rules()
    defn: dict = rules.get("compound_numbers", {}).get(compound, {})
    if not defn:
        return ""

    return f"{defn.get('name', '')} -- {defn.get('meaning', '')}"


def planet_for_number(number: int) -> str:
    """Return the Vedic planet name for a numerology number (1-9).

    Args:
        number: Reduced numerology number (1-9) or master number.

    Returns:
        Planet name string, e.g. "Sun", "Moon".
    """
    base = _reduce_to_base(number) if number in _MASTER_NUMBERS else number
    rules = load_numerology_rules()
    return str(rules.get("planet_numbers", {}).get(base, "Unknown"))
