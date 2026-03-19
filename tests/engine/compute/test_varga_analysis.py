"""Tests for divisional chart analysis — D7, D4, D24, D10."""

from __future__ import annotations

from daivai_engine.compute.varga_analysis import (
    analyze_d4_property,
    analyze_d7_children,
    analyze_d10_career,
    analyze_d24_education,
)
from daivai_engine.models.chart import ChartData


class TestD7Children:
    def test_returns_analysis(self, manish_chart: ChartData) -> None:
        result = analyze_d7_children(manish_chart)
        assert result.varga == "D7"
        assert result.karaka == "Jupiter"

    def test_has_findings(self, manish_chart: ChartData) -> None:
        result = analyze_d7_children(manish_chart)
        assert len(result.key_findings) >= 1

    def test_strength_valid(self, manish_chart: ChartData) -> None:
        result = analyze_d7_children(manish_chart)
        assert result.strength in ("strong", "moderate", "weak")


class TestD4Property:
    def test_returns_analysis(self, manish_chart: ChartData) -> None:
        result = analyze_d4_property(manish_chart)
        assert result.varga == "D4"
        assert result.karaka == "Mars"


class TestD24Education:
    def test_returns_analysis(self, manish_chart: ChartData) -> None:
        result = analyze_d24_education(manish_chart)
        assert result.varga == "D24"
        assert "Mercury" in result.karaka


class TestD10Career:
    def test_returns_analysis(self, manish_chart: ChartData) -> None:
        result = analyze_d10_career(manish_chart)
        assert result.varga == "D10"
        assert "Sun" in result.karaka
