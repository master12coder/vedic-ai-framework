"""Tests for Upapada Lagna computation."""

from __future__ import annotations

from daivai_engine.compute.upapada import compute_upapada_lagna
from daivai_engine.models.chart import ChartData


class TestUpapada:
    def test_upapada_for_manish(self, manish_chart: ChartData) -> None:
        up = compute_upapada_lagna(manish_chart)
        assert 0 <= up.sign_index <= 11
        assert up.lord  # Non-empty lord name
        assert up.sign_hi  # Non-empty Hindi sign
        assert up.sign_en  # Non-empty English sign

    def test_upapada_lord_identified(self, manish_chart: ChartData) -> None:
        up = compute_upapada_lagna(manish_chart)
        valid_lords = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert up.lord in valid_lords

    def test_marriage_indication_valid(self, manish_chart: ChartData) -> None:
        up = compute_upapada_lagna(manish_chart)
        valid = {"favorable", "delayed", "challenging"}
        assert up.marriage_indication in valid

    def test_lord_house_in_range(self, manish_chart: ChartData) -> None:
        up = compute_upapada_lagna(manish_chart)
        assert 1 <= up.lord_house <= 12

    def test_different_chart_produces_different_upapada(
        self, manish_chart: ChartData, sample_chart: ChartData
    ) -> None:
        """Two different charts should likely have different upapdas."""
        up1 = compute_upapada_lagna(manish_chart)
        up2 = compute_upapada_lagna(sample_chart)
        # At least sign or lord should differ (not guaranteed but very likely)
        assert up1.sign_index != up2.sign_index or up1.lord != up2.lord
