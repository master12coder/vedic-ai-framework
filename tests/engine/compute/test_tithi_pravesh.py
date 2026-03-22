"""Tests for Tithi Pravesh (Lunar Return / Tithi Return) computation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.tithi_pravesh import (
    TithiPraveshResult,
    compute_annual_tithi_pravesh,
    compute_tithi_pravesh,
    natal_tithi_number,
)
from daivai_engine.models.chart import ChartData


class TestTithiPraveshResult:
    def test_returns_pydantic_model(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert isinstance(result, TithiPraveshResult)

    def test_year_and_month_fields(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 5)
        assert result.year == 2026
        assert result.month == 5
        assert result.month_name == "May"

    def test_tithi_pravesh_datetime_format(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert "2026-03" in result.tithi_pravesh_datetime
        assert "UTC" in result.tithi_pravesh_datetime

    def test_jd_is_positive(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert result.tithi_pravesh_jd > 2_400_000

    def test_natal_tithi_arc_is_0_to_360(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert 0.0 <= result.natal_tithi_arc < 360.0

    def test_natal_tithi_number_range(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert 1 <= result.natal_tithi_number <= 30

    def test_natal_tithi_name_contains_paksha(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert "Shukla" in result.natal_tithi_name or "Krishna" in result.natal_tithi_name

    def test_natal_paksha_is_valid(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert result.natal_paksha in ("Shukla", "Krishna")

    def test_shukla_when_tithi_le_15(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        if result.natal_tithi_number <= 15:
            assert result.natal_paksha == "Shukla"
        else:
            assert result.natal_paksha == "Krishna"

    def test_annual_chart_is_present(self, manish_chart: ChartData) -> None:
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert result.annual_chart is not None
        assert "Sun" in result.annual_chart.planets

    def test_different_months_different_jds(self, manish_chart: ChartData) -> None:
        r3 = compute_tithi_pravesh(manish_chart, 2026, 3)
        r4 = compute_tithi_pravesh(manish_chart, 2026, 4)
        assert r3.tithi_pravesh_jd != r4.tithi_pravesh_jd

    def test_natal_tithi_consistent_across_months(self, manish_chart: ChartData) -> None:
        """Same natal tithi number in all months for the same chart."""
        r3 = compute_tithi_pravesh(manish_chart, 2026, 3)
        r6 = compute_tithi_pravesh(manish_chart, 2026, 6)
        assert r3.natal_tithi_number == r6.natal_tithi_number


class TestNatalTithiNumber:
    def test_returns_integer_1_to_30(self, manish_chart: ChartData) -> None:
        num = natal_tithi_number(manish_chart)
        assert 1 <= num <= 30

    def test_consistent_with_pravesh_result(self, manish_chart: ChartData) -> None:
        num = natal_tithi_number(manish_chart)
        result = compute_tithi_pravesh(manish_chart, 2026, 3)
        assert num == result.natal_tithi_number


class TestAnnualTithiPravesh:
    def test_returns_12_results(self, manish_chart: ChartData) -> None:
        results = compute_annual_tithi_pravesh(manish_chart, 2026)
        assert len(results) == 12

    def test_months_are_sequential(self, manish_chart: ChartData) -> None:
        results = compute_annual_tithi_pravesh(manish_chart, 2026)
        for i, r in enumerate(results):
            assert r.month == i + 1

    def test_all_have_same_natal_arc(self, manish_chart: ChartData) -> None:
        results = compute_annual_tithi_pravesh(manish_chart, 2026)
        arcs = {r.natal_tithi_arc for r in results}
        assert len(arcs) == 1  # Same natal arc across all months

    def test_all_jds_distinct(self, manish_chart: ChartData) -> None:
        results = compute_annual_tithi_pravesh(manish_chart, 2026)
        jds = [r.tithi_pravesh_jd for r in results]
        assert len(set(jds)) == 12  # All unique

    @pytest.mark.slow
    def test_all_charts_have_valid_lagnas(self, manish_chart: ChartData) -> None:
        results = compute_annual_tithi_pravesh(manish_chart, 2026)
        for r in results:
            assert 0 <= r.annual_chart.lagna_sign_index <= 11
