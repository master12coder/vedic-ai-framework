"""Test KP sub-lord calculations."""

import pytest
from jyotish.compute.kp import get_kp_position, compute_kp_positions, get_significators
from jyotish.utils.constants import DASHA_SEQUENCE


class TestKPSubLord:
    def test_kp_returns_valid_lords(self):
        """All lords should be from the dasha sequence."""
        nak_lord, sub_lord, ss_lord = get_kp_position(0.0)
        assert nak_lord in DASHA_SEQUENCE
        assert sub_lord in DASHA_SEQUENCE
        assert ss_lord in DASHA_SEQUENCE

    def test_kp_at_zero_degrees(self):
        """0° Aries = Ashwini = Ketu nakshatra."""
        nak_lord, _, _ = get_kp_position(0.0)
        assert nak_lord == "Ketu"  # Ashwini is ruled by Ketu

    def test_kp_at_rohini(self):
        """10° Taurus = Rohini = Moon nakshatra."""
        nak_lord, _, _ = get_kp_position(40.0)  # 10° Taurus
        assert nak_lord == "Moon"

    def test_kp_positions_all_planets(self, manish_chart):
        positions = compute_kp_positions(manish_chart)
        assert len(positions) == 9
        for pos in positions:
            assert pos.nakshatra_lord in DASHA_SEQUENCE
            assert pos.sub_lord in DASHA_SEQUENCE
            assert pos.sub_sub_lord in DASHA_SEQUENCE

    def test_kp_full_zodiac_coverage(self):
        """KP should return valid results for all 360 degrees."""
        for deg in range(0, 360):
            nak_lord, sub_lord, ss_lord = get_kp_position(float(deg))
            assert nak_lord in DASHA_SEQUENCE
            assert sub_lord in DASHA_SEQUENCE

    def test_significators(self, manish_chart):
        sig = get_significators(manish_chart, "Jupiter")
        assert "occupies" in sig
        assert "owns" in sig
        assert "star_lord_houses" in sig
        assert len(sig["occupies"]) == 1
