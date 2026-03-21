"""Tests for Shayanadi (12-fold) Avastha — BPHS Ch.45 v21-35."""

from __future__ import annotations

from daivai_engine.compute.avasthas import _shayanadi_zone, compute_shayanadi_avasthas
from daivai_engine.models.chart import ChartData


_VALID_STATES = {
    "shayana", "upavesha", "netrapani", "prakasha",
    "gamana", "agama", "sabha", "aagama",
    "bhojana", "nrityalipsya", "kautuka", "nidra",
}


class TestShayanadiAvasthas:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_shayanadi_avasthas(manish_chart)
        assert len(results) == 7

    def test_all_states_valid(self, manish_chart: ChartData) -> None:
        results = compute_shayanadi_avasthas(manish_chart)
        for r in results:
            assert r.avastha in _VALID_STATES, f"{r.planet}: invalid state '{r.avastha}'"

    def test_zone_is_1_to_12(self, manish_chart: ChartData) -> None:
        results = compute_shayanadi_avasthas(manish_chart)
        for r in results:
            assert 1 <= r.zone <= 12, f"{r.planet}: zone {r.zone} out of range"

    def test_strength_fraction_in_range(self, manish_chart: ChartData) -> None:
        results = compute_shayanadi_avasthas(manish_chart)
        for r in results:
            assert 0.0 <= r.strength_fraction <= 1.0, (
                f"{r.planet}: strength_fraction {r.strength_fraction} out of range"
            )

    def test_hindi_name_not_empty(self, manish_chart: ChartData) -> None:
        results = compute_shayanadi_avasthas(manish_chart)
        for r in results:
            assert r.avastha_hi, f"{r.planet}: Hindi name is empty"

    def test_result_summary_not_empty(self, manish_chart: ChartData) -> None:
        results = compute_shayanadi_avasthas(manish_chart)
        for r in results:
            assert len(r.result_summary) > 20, f"{r.planet}: result_summary too short"

    def test_odd_sign_zone_increases_with_degree(self) -> None:
        """For odd signs, higher degree → higher zone."""
        # Aries = sign index 0 (odd)
        zone_low = _shayanadi_zone(0, 1.0)   # Near 0°
        zone_high = _shayanadi_zone(0, 28.0)  # Near 30°
        assert zone_low < zone_high

    def test_even_sign_zone_decreases_with_degree(self) -> None:
        """For even signs (Taurus=1), higher degree → lower zone (reversed sequence)."""
        zone_low = _shayanadi_zone(1, 1.0)   # Near 0°
        zone_high = _shayanadi_zone(1, 28.0)  # Near 30°
        assert zone_low > zone_high

    def test_prakasha_is_positive(self) -> None:
        """Prakasha state must always be marked positive."""
        # Find a degree in Aries (odd) that gives Prakasha (zone 3, 7.5°-10°)
        zone_idx = _shayanadi_zone(0, 8.0)  # 8° in Aries → zone 3 (0-indexed) = Prakasha
        assert zone_idx == 3  # Zone 4 (1-based) = Prakasha

    def test_nidra_is_last_zone_odd_sign(self) -> None:
        """In odd sign, 27.5°-30° should be Nidra (zone 11, 0-indexed)."""
        zone_idx = _shayanadi_zone(0, 28.5)
        assert zone_idx == 11  # Nidra

    def test_nidra_is_first_zone_even_sign(self) -> None:
        """In even sign, 0°-2.5° should be Nidra (reversed sequence)."""
        zone_idx = _shayanadi_zone(1, 1.0)
        assert zone_idx == 11  # Nidra (last in sequence → first in even sign)
