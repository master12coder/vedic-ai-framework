"""Tests for Deeptadi and Lajjitadi avastha computations."""

from __future__ import annotations

from daivai_engine.compute.avasthas import (
    compute_deeptadi_avasthas,
    compute_lajjitadi_avasthas,
)
from daivai_engine.models.chart import ChartData


class TestDeeptadiAvasthas:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_deeptadi_avasthas(manish_chart)
        assert len(results) == 7  # 7 classical planets

    def test_moon_is_deepta_for_manish(self, manish_chart: ChartData) -> None:
        """Moon exalted in Taurus = Deepta (brilliant) state."""
        results = compute_deeptadi_avasthas(manish_chart)
        moon = next(r for r in results if r.planet == "Moon")
        assert moon.avastha == "deepta"
        assert moon.strength_multiplier == 1.5

    def test_venus_is_vikala_for_manish(self, manish_chart: ChartData) -> None:
        """Venus combust = Vikala (crippled) state."""
        results = compute_deeptadi_avasthas(manish_chart)
        venus = next(r for r in results if r.planet == "Venus")
        assert venus.avastha == "vikala"
        assert venus.strength_multiplier == 0.25

    def test_all_have_hindi_names(self, manish_chart: ChartData) -> None:
        results = compute_deeptadi_avasthas(manish_chart)
        for r in results:
            assert r.avastha_hi  # Non-empty Hindi name

    def test_multiplier_in_range(self, manish_chart: ChartData) -> None:
        results = compute_deeptadi_avasthas(manish_chart)
        for r in results:
            assert 0.0 <= r.strength_multiplier <= 1.5


class TestLajjitadiAvasthas:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_lajjitadi_avasthas(manish_chart)
        assert len(results) == 7

    def test_moon_is_garvita_for_manish(self, manish_chart: ChartData) -> None:
        """Moon exalted = Garvita (proud) state."""
        results = compute_lajjitadi_avasthas(manish_chart)
        moon = next(r for r in results if r.planet == "Moon")
        assert moon.avastha == "garvita"
        assert moon.is_positive is True

    def test_all_have_valid_states(self, manish_chart: ChartData) -> None:
        valid = {"lajjita", "garvita", "kshudhita", "trushita", "mudita", "kshobhita"}
        results = compute_lajjitadi_avasthas(manish_chart)
        for r in results:
            assert r.avastha in valid
