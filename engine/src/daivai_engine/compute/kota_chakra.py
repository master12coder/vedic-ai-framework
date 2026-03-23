"""Kota Chakra — 28-nakshatra fortress diagram for transit analysis.

Kota Chakra arranges 28 nakshatras (27 standard + Abhijit) in 4 concentric
rings around the natal Moon's nakshatra (Kota Swami). Transiting malefics
in inner rings threaten the fort; benefics in inner rings protect it.

Ring assignment from Kota Swami (position 0):
  Stambha (core):  positions 0, 7, 14, 21  (every 7th)
  Madhya (middle): positions 1, 6, 8, 13, 15, 20, 22, 27
  Prakaara (wall): positions 2, 5, 9, 12, 16, 19, 23, 26
  Bahya (outer):   positions 3, 4, 10, 11, 17, 18, 24, 25

Dvara (gate) nakshatras: positions 3 and 25.

Source: Tajaka Neelakanthi.
"""

from __future__ import annotations

from daivai_engine.constants import NAKSHATRAS
from daivai_engine.models.kota_chakra import (
    KotaChakraResult,
    KotaNakshatra,
    KotaPlanetPosition,
)


# ── Kota Chakra Layout Constants ─────────────────────────────────────────────

# 28 nakshatras: standard 27 + Abhijit inserted between Uttara Ashadha and Shravana
NAKSHATRAS_28: list[str] = [
    *NAKSHATRAS[:21],  # Ashwini through Uttara Ashadha (indices 0-20)
    "Abhijit",  # index 21 — between Uttara Ashadha and Shravana
    *NAKSHATRAS[21:],  # Shravana through Revati (indices 22-27)
]

# Ring assignment by position from Swami
_STAMBHA_POSITIONS = {0, 7, 14, 21}
_MADHYA_POSITIONS = {1, 6, 8, 13, 15, 20, 22, 27}
_PRAKAARA_POSITIONS = {2, 5, 9, 12, 16, 19, 23, 26}
_BAHYA_POSITIONS = {3, 4, 10, 11, 17, 18, 24, 25}

# Gate (Dvara) positions
_DVARA_POSITIONS = {3, 25}

# Natural benefics and malefics
_NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
_NATURAL_MALEFICS = {"Saturn", "Mars", "Rahu", "Ketu", "Sun"}


def _ring_for_position(pos: int) -> str:
    """Return the ring name for a given position from Swami.

    Args:
        pos: Position index (0-27) from the Kota Swami nakshatra.

    Returns:
        Ring name: 'stambha', 'madhya', 'prakaara', or 'bahya'.
    """
    if pos in _STAMBHA_POSITIONS:
        return "stambha"
    if pos in _MADHYA_POSITIONS:
        return "madhya"
    if pos in _PRAKAARA_POSITIONS:
        return "prakaara"
    return "bahya"


def _nak_28_index(nak_27_index: int) -> int:
    """Convert a standard 27-nakshatra index to the 28-nakshatra index.

    Abhijit is inserted at index 21 (between Uttara Ashadha=20 and Shravana).

    Args:
        nak_27_index: Standard nakshatra index (0-26).

    Returns:
        Corresponding index in the 28-nakshatra system (0-27).
    """
    if nak_27_index <= 20:
        return nak_27_index
    # Shravana (21 in 27-system) becomes 22 in 28-system, etc.
    return nak_27_index + 1


def _build_ring_layout(
    swami_28_index: int,
) -> dict[str, list[KotaNakshatra]]:
    """Build the 4-ring layout starting from the Kota Swami nakshatra.

    Args:
        swami_28_index: Index of the Swami nakshatra in the 28-nak system.

    Returns:
        Dictionary mapping ring name to list of KotaNakshatra in that ring.
    """
    layout: dict[str, list[KotaNakshatra]] = {
        "stambha": [],
        "madhya": [],
        "prakaara": [],
        "bahya": [],
    }

    for pos in range(28):
        nak_idx_28 = (swami_28_index + pos) % 28
        nak_name = NAKSHATRAS_28[nak_idx_28]
        ring = _ring_for_position(pos)
        is_dvara = pos in _DVARA_POSITIONS

        # Map back to 27-nak index (Abhijit gets special index 27)
        if nak_name == "Abhijit":
            nak_index_standard = 27
        else:
            nak_index_standard = NAKSHATRAS.index(nak_name)

        entry = KotaNakshatra(
            nakshatra_index=nak_index_standard,
            nakshatra_name=nak_name,
            ring=ring,
            is_dvara=is_dvara,
            position_from_swami=pos,
        )
        layout[ring].append(entry)

    return layout


def _assess_planet_effect(planet: str, ring: str, is_dvara: bool) -> str:
    """Determine a planet's effect based on its nature and ring placement.

    Args:
        planet: Planet name.
        ring: The ring the planet occupies.
        is_dvara: Whether the planet is at a gate nakshatra.

    Returns:
        Effect string: 'protective', 'threatening', or 'neutral'.
    """
    is_benefic = planet in _NATURAL_BENEFICS
    is_malefic = planet in _NATURAL_MALEFICS

    if is_malefic and ring in ("stambha", "madhya"):
        return "threatening"
    if is_malefic and is_dvara:
        return "threatening"
    if is_benefic and ring in ("stambha", "madhya"):
        return "protective"
    if is_benefic and is_dvara:
        return "protective"
    return "neutral"


def compute_kota_chakra(
    natal_moon_nak_index: int,
    transit_positions: dict[str, int] | None = None,
) -> KotaChakraResult:
    """Compute the Kota Chakra fortress diagram and assess transit impacts.

    The natal Moon's nakshatra becomes the Kota Swami (fortress commander).
    If transit_positions is not provided, only the layout is returned with
    empty transit analysis.

    Args:
        natal_moon_nak_index: Standard nakshatra index (0-26) of natal Moon.
        transit_positions: Optional dict of planet → nakshatra index (0-26)
            for transiting planets. If None, transit analysis is skipped.

    Returns:
        KotaChakraResult with fortress layout and transit assessment.
    """
    swami_name = NAKSHATRAS[natal_moon_nak_index]
    swami_28 = _nak_28_index(natal_moon_nak_index)

    # Build ring layout
    ring_layout = _build_ring_layout(swami_28)

    # Build a lookup: 28-nak-index → (ring, is_dvara)
    nak_to_ring: dict[int, tuple[str, bool]] = {}
    for ring_name, entries in ring_layout.items():
        for entry in entries:
            # Store by 28-system index
            nak_28_idx = (swami_28 + entry.position_from_swami) % 28
            nak_to_ring[nak_28_idx] = (ring_name, entry.is_dvara)

    # Assess transit planets
    transit_results: list[KotaPlanetPosition] = []
    stambha_threatened = False
    dvara_breached = False

    if transit_positions:
        for planet, nak_27_idx in transit_positions.items():
            nak_28_idx = _nak_28_index(nak_27_idx)
            ring_name, is_dvara = nak_to_ring.get(nak_28_idx, ("bahya", False))
            is_benefic = planet in _NATURAL_BENEFICS
            effect = _assess_planet_effect(planet, ring_name, is_dvara)

            transit_results.append(
                KotaPlanetPosition(
                    planet=planet,
                    nakshatra_name=NAKSHATRAS_28[nak_28_idx],
                    ring=ring_name,
                    is_at_dvara=is_dvara,
                    is_benefic=is_benefic,
                    effect=effect,
                )
            )

            if effect == "threatening" and ring_name == "stambha":
                stambha_threatened = True
            if effect == "threatening" and is_dvara:
                dvara_breached = True

    # Overall strength assessment
    if stambha_threatened and dvara_breached:
        overall = "breached"
    elif stambha_threatened or dvara_breached:
        overall = "vulnerable"
    elif any(tp.effect == "protective" and tp.ring == "stambha" for tp in transit_results):
        overall = "fortified"
    else:
        overall = "stable"

    # Summary
    threat_planets = [tp.planet for tp in transit_results if tp.effect == "threatening"]
    protect_planets = [tp.planet for tp in transit_results if tp.effect == "protective"]
    summary = (
        f"Kota Swami: {swami_name}. "
        f"Fort: {overall}. "
        f"Threats: {', '.join(threat_planets) if threat_planets else 'None'}. "
        f"Protection: {', '.join(protect_planets) if protect_planets else 'None'}."
    )

    return KotaChakraResult(
        kota_swami_nakshatra=swami_name,
        kota_swami_index=natal_moon_nak_index,
        ring_layout=ring_layout,
        transit_positions=transit_results,
        stambha_threatened=stambha_threatened,
        dvara_breached=dvara_breached,
        overall_strength=overall,
        summary=summary,
    )
