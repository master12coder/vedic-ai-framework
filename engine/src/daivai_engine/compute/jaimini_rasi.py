"""Jaimini sign-based (Rashi Drishti) aspects."""

from __future__ import annotations


# Sign modalities (0-indexed sign → modality)
# Movable (Chara): Aries(0), Cancer(3), Libra(6), Capricorn(9)
# Fixed (Sthira): Taurus(1), Leo(4), Scorpio(7), Aquarius(10)
# Dual (Dwiswabhava): Gemini(2), Virgo(5), Sagittarius(8), Pisces(11)
MOVABLE_SIGNS: set[int] = {0, 3, 6, 9}
FIXED_SIGNS: set[int] = {1, 4, 7, 10}
DUAL_SIGNS: set[int] = {2, 5, 8, 11}

# Number of signs in the zodiac
NUM_SIGNS: int = 12


def _get_sign_modality(sign_index: int) -> str:
    """Return the modality of a sign: 'movable', 'fixed', or 'dual'.

    Args:
        sign_index: Sign index (0-11).

    Returns:
        Modality string.
    """
    if sign_index in MOVABLE_SIGNS:
        return "movable"
    if sign_index in FIXED_SIGNS:
        return "fixed"
    return "dual"


def get_jaimini_aspects(sign_index: int) -> list[int]:
    """Compute which signs a given sign aspects in the Jaimini system.

    Jaimini aspects are sign-based (rashi drishti), not planet-based:
    - Movable signs aspect all fixed signs EXCEPT the one adjacent to them.
    - Fixed signs aspect all movable signs EXCEPT the one adjacent to them.
    - Dual signs aspect all other dual signs.

    Args:
        sign_index: The aspecting sign (0-11).

    Returns:
        List of sign indices (0-11) that are aspected.

    Raises:
        ValueError: If sign_index is not in range 0-11.
    """
    if not 0 <= sign_index < NUM_SIGNS:
        raise ValueError(f"Invalid sign index: {sign_index}. Must be 0-11.")

    modality = _get_sign_modality(sign_index)

    if modality == "movable":
        # Aspect all fixed signs except the adjacent one (next sign)
        adjacent_fixed = (sign_index + 1) % NUM_SIGNS
        return [s for s in FIXED_SIGNS if s != adjacent_fixed]

    if modality == "fixed":
        # Aspect all movable signs except the adjacent one (previous sign)
        adjacent_movable = (sign_index - 1) % NUM_SIGNS
        return [s for s in MOVABLE_SIGNS if s != adjacent_movable]

    # Dual signs aspect all other dual signs
    return [s for s in DUAL_SIGNS if s != sign_index]
