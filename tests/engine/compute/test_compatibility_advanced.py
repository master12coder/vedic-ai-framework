"""Tests for advanced compatibility — Mangal Dosha, Nadi Dosha."""

from __future__ import annotations

from daivai_engine.compute.compatibility_advanced import (
    analyze_nadi_dosha,
    compute_mangal_dosha_detailed,
)
from daivai_engine.models.chart import ChartData


class TestMangalDoshaDetailed:
    def test_returns_result(self, manish_chart: ChartData) -> None:
        result = compute_mangal_dosha_detailed(manish_chart)
        assert isinstance(result.is_present, bool)
        assert 0 <= result.severity <= 10

    def test_net_effect_valid(self, manish_chart: ChartData) -> None:
        result = compute_mangal_dosha_detailed(manish_chart)
        valid = {"none", "cancelled", "mild", "moderate", "severe"}
        assert result.net_effect in valid

    def test_cancellations_list(self, manish_chart: ChartData) -> None:
        result = compute_mangal_dosha_detailed(manish_chart)
        assert isinstance(result.cancellations, list)


class TestNadiDosha:
    def test_same_chart_has_dosha(self, manish_chart: ChartData) -> None:
        """Same person's chart compared with itself should have Nadi dosha."""
        result = analyze_nadi_dosha(manish_chart, manish_chart)
        assert result.is_present  # Same nadi = dosha

    def test_different_charts(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = analyze_nadi_dosha(manish_chart, sample_chart)
        # May or may not have dosha, just verify structure
        assert result.person1_nadi in ("Aadi", "Madhya", "Antya")
        assert result.person2_nadi in ("Aadi", "Madhya", "Antya")

    def test_severity_valid(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = analyze_nadi_dosha(manish_chart, sample_chart)
        assert result.net_severity in ("none", "mild", "severe")
