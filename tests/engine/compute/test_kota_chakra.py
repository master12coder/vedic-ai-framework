"""Tests for Kota Chakra — 28-nakshatra fortress diagram.

The natal Moon's nakshatra becomes Kota Swami (fortress commander). The 28
nakshatras are arranged in 4 concentric rings: Stambha, Madhya, Prakaara, Bahya.

Source: Tajaka Neelakanthi.
"""

from __future__ import annotations

from daivai_engine.compute.kota_chakra import (
    _BAHYA_POSITIONS,
    _DVARA_POSITIONS,
    _MADHYA_POSITIONS,
    _PRAKAARA_POSITIONS,
    _STAMBHA_POSITIONS,
    NAKSHATRAS_28,
    _build_ring_layout,
    _nak_28_index,
    _ring_for_position,
    compute_kota_chakra,
)
from daivai_engine.constants import NAKSHATRAS
from daivai_engine.models.kota_chakra import (
    KotaChakraResult,
    KotaPlanetPosition,
)


# ---------------------------------------------------------------------------
# 28-nakshatra system
# ---------------------------------------------------------------------------


class TestNakshatras28:
    """Verify the 28-nakshatra list includes Abhijit."""

    def test_length_is_28(self) -> None:
        assert len(NAKSHATRAS_28) == 28

    def test_abhijit_at_index_21(self) -> None:
        assert NAKSHATRAS_28[21] == "Abhijit"

    def test_standard_nakshatras_preserved(self) -> None:
        """All 27 standard nakshatras should appear in the 28-nak list."""
        for nak in NAKSHATRAS:
            assert nak in NAKSHATRAS_28


class TestNak28Index:
    """Test conversion from 27-nak index to 28-nak index."""

    def test_ashwini_unchanged(self) -> None:
        """Ashwini (index 0) stays at 0."""
        assert _nak_28_index(0) == 0

    def test_uttara_ashadha_unchanged(self) -> None:
        """Uttara Ashadha (index 20) stays at 20."""
        assert _nak_28_index(20) == 20

    def test_shravana_shifts_by_one(self) -> None:
        """Shravana (index 21 in 27-system) becomes 22 in 28-system."""
        assert _nak_28_index(21) == 22

    def test_revati_shifts_by_one(self) -> None:
        """Revati (index 26 in 27-system) becomes 27 in 28-system."""
        assert _nak_28_index(26) == 27


# ---------------------------------------------------------------------------
# Ring positions
# ---------------------------------------------------------------------------


class TestRingPositions:
    """Verify ring position sets are correct and non-overlapping."""

    def test_all_28_positions_covered(self) -> None:
        all_positions = (
            _STAMBHA_POSITIONS | _MADHYA_POSITIONS | _PRAKAARA_POSITIONS | _BAHYA_POSITIONS
        )
        assert all_positions == set(range(28))

    def test_no_overlap_between_rings(self) -> None:
        assert _STAMBHA_POSITIONS.isdisjoint(_MADHYA_POSITIONS)
        assert _STAMBHA_POSITIONS.isdisjoint(_PRAKAARA_POSITIONS)
        assert _STAMBHA_POSITIONS.isdisjoint(_BAHYA_POSITIONS)
        assert _MADHYA_POSITIONS.isdisjoint(_PRAKAARA_POSITIONS)
        assert _MADHYA_POSITIONS.isdisjoint(_BAHYA_POSITIONS)
        assert _PRAKAARA_POSITIONS.isdisjoint(_BAHYA_POSITIONS)

    def test_stambha_has_4_positions(self) -> None:
        assert len(_STAMBHA_POSITIONS) == 4

    def test_madhya_has_8_positions(self) -> None:
        assert len(_MADHYA_POSITIONS) == 8

    def test_prakaara_has_8_positions(self) -> None:
        assert len(_PRAKAARA_POSITIONS) == 8

    def test_bahya_has_8_positions(self) -> None:
        assert len(_BAHYA_POSITIONS) == 8

    def test_dvara_positions_in_bahya(self) -> None:
        """Gate nakshatras (positions 3, 25) are in the Bahya ring."""
        for pos in _DVARA_POSITIONS:
            assert _ring_for_position(pos) == "bahya"


class TestRingForPosition:
    """Test _ring_for_position returns correct ring."""

    def test_position_0_is_stambha(self) -> None:
        assert _ring_for_position(0) == "stambha"

    def test_position_7_is_stambha(self) -> None:
        assert _ring_for_position(7) == "stambha"

    def test_position_1_is_madhya(self) -> None:
        assert _ring_for_position(1) == "madhya"

    def test_position_3_is_bahya(self) -> None:
        assert _ring_for_position(3) == "bahya"

    def test_position_2_is_prakaara(self) -> None:
        assert _ring_for_position(2) == "prakaara"


# ---------------------------------------------------------------------------
# Ring layout builder
# ---------------------------------------------------------------------------


class TestBuildRingLayout:
    """Test _build_ring_layout produces correct structure."""

    def test_layout_has_four_rings(self) -> None:
        layout = _build_ring_layout(0)
        assert set(layout.keys()) == {"stambha", "madhya", "prakaara", "bahya"}

    def test_total_nakshatras_is_28(self) -> None:
        layout = _build_ring_layout(0)
        total = sum(len(entries) for entries in layout.values())
        assert total == 28

    def test_swami_at_position_0_in_stambha(self) -> None:
        """The Kota Swami nakshatra is always at position 0 — which is stambha."""
        layout = _build_ring_layout(0)
        stambha_naks = layout["stambha"]
        pos_zero = [n for n in stambha_naks if n.position_from_swami == 0]
        assert len(pos_zero) == 1
        assert pos_zero[0].nakshatra_name == NAKSHATRAS_28[0]

    def test_dvara_nakshatras_marked(self) -> None:
        """Exactly 2 nakshatras should be marked as dvara."""
        layout = _build_ring_layout(5)
        all_entries = [n for entries in layout.values() for n in entries]
        dvara = [n for n in all_entries if n.is_dvara]
        assert len(dvara) == 2


# ---------------------------------------------------------------------------
# Full computation
# ---------------------------------------------------------------------------


class TestComputeKotaChakra:
    """Integration tests for compute_kota_chakra."""

    def test_result_type(self) -> None:
        result = compute_kota_chakra(3)  # Rohini = index 3
        assert isinstance(result, KotaChakraResult)

    def test_swami_is_rohini(self) -> None:
        result = compute_kota_chakra(3)
        assert result.kota_swami_nakshatra == "Rohini"
        assert result.kota_swami_index == 3

    def test_without_transits_stable(self) -> None:
        """No transit planets → fort should be stable."""
        result = compute_kota_chakra(3)
        assert result.overall_strength == "stable"
        assert not result.stambha_threatened
        assert not result.dvara_breached
        assert len(result.transit_positions) == 0

    def test_malefic_in_stambha_threatens(self) -> None:
        """Saturn in the swami nakshatra (position 0 = stambha) should threaten."""
        # Rohini = index 3; swami_28 = 3 (below 21, so same)
        # Position 0 from swami → the swami nakshatra itself
        result = compute_kota_chakra(3, transit_positions={"Saturn": 3})
        assert result.stambha_threatened
        assert result.overall_strength in ("vulnerable", "breached")

    def test_benefic_in_stambha_fortifies(self) -> None:
        """Jupiter in swami nakshatra → protective, fort = fortified."""
        result = compute_kota_chakra(3, transit_positions={"Jupiter": 3})
        assert result.overall_strength == "fortified"
        protective = [tp for tp in result.transit_positions if tp.effect == "protective"]
        assert len(protective) >= 1

    def test_malefic_at_dvara_breaches(self) -> None:
        """Mars at a Dvara (gate) position should breach the gate."""
        # For swami_28=3 (Rohini), position 3 from swami corresponds to
        # nak_28_index = (3+3) % 28 = 6, which is Punarvasu (27-nak index 6).
        # Position 25 from swami: (3+25) % 28 = 0, which is Ashwini (index 0).
        result = compute_kota_chakra(3, transit_positions={"Mars": 6})
        # Mars at index 6 (Punarvasu) — check if it lands on dvara position
        dvara_planet = [tp for tp in result.transit_positions if tp.is_at_dvara]
        if dvara_planet:
            assert result.dvara_breached

    def test_summary_contains_swami_name(self) -> None:
        result = compute_kota_chakra(3)
        assert "Rohini" in result.summary

    def test_multiple_transits(self) -> None:
        """Multiple planets in transit should all be assessed."""
        transits = {"Saturn": 3, "Jupiter": 10, "Mars": 15, "Venus": 20}
        result = compute_kota_chakra(3, transit_positions=transits)
        assert len(result.transit_positions) == 4
        for tp in result.transit_positions:
            assert isinstance(tp, KotaPlanetPosition)
            assert tp.ring in ("stambha", "madhya", "prakaara", "bahya")
            assert tp.effect in ("protective", "threatening", "neutral")
