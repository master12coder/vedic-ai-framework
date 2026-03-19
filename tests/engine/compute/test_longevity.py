"""Tests for longevity (Ayurdaya) computation."""

from __future__ import annotations

from daivai_engine.compute.longevity import compute_longevity
from daivai_engine.models.chart import ChartData


class TestLongevity:
    def test_returns_result(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.pindayu_years > 0

    def test_valid_category(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.category in ("alpayu", "madhyayu", "poornayu")

    def test_breakdown_has_seven_planets(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert len(result.breakdown) == 7

    def test_years_under_120(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.pindayu_years <= 120.0

    def test_hindi_category(self, manish_chart: ChartData) -> None:
        result = compute_longevity(manish_chart)
        assert result.category_hi in ("अल्पायु", "मध्यायु", "पूर्णायु")
