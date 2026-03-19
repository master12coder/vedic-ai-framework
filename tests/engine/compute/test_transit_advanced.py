"""Tests for advanced transit analysis."""

from __future__ import annotations

from daivai_engine.compute.transit_advanced import (
    compute_jupiter_transit,
    compute_rahu_ketu_transit,
    compute_sadesati_detailed,
)
from daivai_engine.models.chart import ChartData


class TestSadesatiDetailed:
    def test_returns_result(self, manish_chart: ChartData) -> None:
        result = compute_sadesati_detailed(manish_chart)
        assert isinstance(result.is_active, bool)

    def test_phase_valid(self, manish_chart: ChartData) -> None:
        result = compute_sadesati_detailed(manish_chart)
        if result.is_active:
            assert result.phase in (1, 2, 3)
        else:
            assert result.phase is None

    def test_intensity_valid(self, manish_chart: ChartData) -> None:
        result = compute_sadesati_detailed(manish_chart)
        assert result.intensity in ("none", "mild", "moderate", "severe")


class TestJupiterTransit:
    def test_returns_result(self, manish_chart: ChartData) -> None:
        result = compute_jupiter_transit(manish_chart)
        assert 1 <= result.transit_house_from_moon <= 12

    def test_favorable_flag(self, manish_chart: ChartData) -> None:
        result = compute_jupiter_transit(manish_chart)
        assert isinstance(result.is_favorable, bool)


class TestRahuKetuTransit:
    def test_returns_result(self, manish_chart: ChartData) -> None:
        result = compute_rahu_ketu_transit(manish_chart)
        assert 1 <= result.rahu_house_from_moon <= 12
        assert 1 <= result.ketu_house_from_moon <= 12

    def test_karmic_focus(self, manish_chart: ChartData) -> None:
        result = compute_rahu_ketu_transit(manish_chart)
        assert len(result.karmic_focus) > 10
