"""Test all 16+ varga chart computations."""

import pytest

from daivai_engine.compute.divisional import (
    VARGA_FUNCTIONS,
    compute_dasamsha_sign,
    compute_drekkana_sign,
    compute_hora_sign,
    compute_navamsha_sign,
    compute_varga,
    get_vargottam_planets,
)
from daivai_engine.compute.divisional_extended import compute_shashtyamsha_sign


class TestVargaCharts:
    def test_navamsha_valid_range(self):
        """Navamsha sign should be 0-11 for any longitude."""
        for lon in [0, 30, 90, 180, 270, 359.9]:
            result = compute_navamsha_sign(lon)
            assert 0 <= result <= 11, f"Invalid D9 for {lon}°: {result}"

    def test_dasamsha_valid_range(self):
        for lon in [0, 45, 120, 240, 355]:
            result = compute_dasamsha_sign(lon)
            assert 0 <= result <= 11

    def test_hora_only_leo_or_cancer(self):
        """D2 should always return Leo (4) or Cancer (3)."""
        for lon in range(0, 360, 5):
            result = compute_hora_sign(float(lon))
            assert result in (3, 4), f"D2 at {lon}° = {result}, expected 3 or 4"

    def test_drekkana_valid(self):
        for lon in [0, 15, 29, 30, 100, 350]:
            result = compute_drekkana_sign(float(lon))
            assert 0 <= result <= 11

    def test_all_16_vargas_available(self):
        expected = {
            "D2",
            "D3",
            "D4",
            "D5",
            "D6",
            "D7",
            "D9",
            "D10",
            "D12",
            "D16",
            "D20",
            "D24",
            "D27",
            "D30",
            "D40",
            "D45",
            "D60",
        }
        assert expected == set(VARGA_FUNCTIONS.keys())

    def test_compute_varga_d9(self, manish_chart):
        result = compute_varga(manish_chart, "D9")
        assert len(result) == 9
        for pos in result:
            assert 0 <= pos.divisional_sign_index <= 11

    def test_compute_varga_all(self, manish_chart):
        """All varga charts should produce valid results."""
        for varga_name in VARGA_FUNCTIONS:
            result = compute_varga(manish_chart, varga_name)
            assert len(result) == 9, f"{varga_name} returned {len(result)} planets"
            for pos in result:
                assert 0 <= pos.divisional_sign_index <= 11, (
                    f"{varga_name} {pos.planet}: invalid sign {pos.divisional_sign_index}"
                )

    def test_unknown_varga_raises(self, manish_chart):
        with pytest.raises(ValueError, match="Unknown varga"):
            compute_varga(manish_chart, "D99")

    def test_vargottam_planets(self, manish_chart):
        vp = get_vargottam_planets(manish_chart)
        assert isinstance(vp, list)
        for p in vp:
            assert p in [
                "Sun",
                "Moon",
                "Mars",
                "Mercury",
                "Jupiter",
                "Venus",
                "Saturn",
                "Rahu",
                "Ketu",
            ]

    def test_d60_odd_sign_starts_from_aries(self) -> None:
        """D60: odd signs (Aries, Gemini, ...) count from Aries — BPHS Ch.8."""
        # Aries is sign_index 0 (odd sign). Part 0 (0-0.5°) → Aries (0).
        assert compute_shashtyamsha_sign(0.1) == 0  # Aries, first part → Aries

    def test_d60_even_sign_starts_from_libra(self) -> None:
        """D60: even signs (Taurus, Cancer, ...) count from Libra — BPHS Ch.8."""
        # Taurus is sign_index 1 (even sign). Part 0 (30-30.5°) → Libra (6).
        assert compute_shashtyamsha_sign(30.1) == 6  # Taurus, first part → Libra

    def test_d60_valid_range(self) -> None:
        """D60 sign must be 0-11 for any longitude."""
        for lon in range(0, 360, 3):
            result = compute_shashtyamsha_sign(float(lon))
            assert 0 <= result <= 11, f"D60 at {lon}°: {result}"
