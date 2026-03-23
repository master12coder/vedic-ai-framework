"""Tests for Varsha Pravesh (Solar Return) with Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from daivai_engine.compute.varsha_pravesh import (
    MunthaResult,
    VarshaPraveshResult,
    compute_varsha_pravesh,
    get_muntha_annual,
    nakshatra_balance,
)
from daivai_engine.models.chart import ChartData


class TestVarshaPraveshResult:
    def test_returns_pydantic_model(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert isinstance(result, VarshaPraveshResult)

    def test_year_field_matches_requested(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.year == 2026

    def test_solar_return_in_march_for_manish(self, manish_chart: ChartData) -> None:
        """Manish born 13/03/1989 — solar return must be in March."""
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert "2026-03" in result.solar_return_datetime

    def test_solar_return_jd_is_positive_float(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.solar_return_jd > 2_400_000  # Any modern Julian Day

    def test_natal_sun_longitude_valid(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert 0.0 <= result.natal_sun_longitude < 360.0

    def test_annual_chart_present(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.annual_chart is not None
        assert "Sun" in result.annual_chart.planets
        assert "Moon" in result.annual_chart.planets

    def test_year_lord_is_valid_planet(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert result.year_lord in valid

    def test_year_lord_hi_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert len(result.year_lord_hi) > 0

    def test_year_day_name_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.year_day_name in {
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        }

    def test_panchavargiya_bala_has_five_keys(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        bala = result.panchavargiya_bala
        assert set(bala.keys()) == {
            "janma_rasi_bala",
            "hora_bala",
            "weekday_bala",
            "masa_bala",
            "abda_bala",
        }

    def test_panchavargiya_values_are_valid(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        valid_values = {"strong", "moderate", "weak"}
        for v in result.panchavargiya_bala.values():
            assert v in valid_values

    def test_abda_bala_always_strong(self, manish_chart: ChartData) -> None:
        """Year lord always has full Abda Bala by definition."""
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.panchavargiya_bala["abda_bala"] == "strong"

    def test_weekday_bala_always_strong(self, manish_chart: ChartData) -> None:
        """Year lord always has weekday bala (it IS the weekday lord)."""
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.panchavargiya_bala["weekday_bala"] == "strong"

    def test_different_years_produce_different_jds(self, manish_chart: ChartData) -> None:
        r2025 = compute_varsha_pravesh(manish_chart, 2025)
        r2026 = compute_varsha_pravesh(manish_chart, 2026)
        assert r2025.solar_return_jd != r2026.solar_return_jd

    def test_model_is_frozen(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        with pytest.raises(ValidationError):
            result.year = 9999  # type: ignore[misc]


class TestMunthaResult:
    def test_muntha_is_pydantic_model(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert isinstance(result.muntha, MunthaResult)

    def test_muntha_sign_2026_is_karka(self, manish_chart: ChartData) -> None:
        """2026: age = 37, lagna = Mithuna (2). Muntha = (2+37)%12 = 3 = Karka."""
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert result.muntha.sign_index == 3
        assert result.muntha.sign_en == "Cancer"

    def test_muntha_lord_is_valid(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert result.muntha.lord in valid

    def test_muntha_house_from_lagna_valid(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert 1 <= result.muntha.house_from_lagna <= 12

    def test_muntha_description_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_varsha_pravesh(manish_chart, 2026)
        assert len(result.muntha.description) > 20

    def test_get_muntha_annual_standalone(self, manish_chart: ChartData) -> None:
        muntha = get_muntha_annual(manish_chart, 2026)
        assert isinstance(muntha, MunthaResult)
        assert muntha.sign_index == 3

    def test_muntha_advances_each_year(self, manish_chart: ChartData) -> None:
        m2026 = get_muntha_annual(manish_chart, 2026)
        m2027 = get_muntha_annual(manish_chart, 2027)
        assert (m2027.sign_index - m2026.sign_index) % 12 == 1


class TestNakshatraBalance:
    def test_balance_at_start_of_nakshatra_is_one(self) -> None:
        """Moon exactly at start of nakshatra → full balance remaining."""
        lon = 0.0  # Ashwini start
        assert abs(nakshatra_balance(lon) - 1.0) < 1e-6

    def test_balance_at_end_of_nakshatra_is_near_zero(self) -> None:
        """Moon at end of nakshatra → balance ≈ 0."""
        nak_span = 360.0 / 27.0
        lon = nak_span - 0.001
        assert nakshatra_balance(lon) < 0.01

    def test_balance_midpoint_is_half(self) -> None:
        nak_span = 360.0 / 27.0
        lon = nak_span / 2.0  # Mid-nakshatra
        assert abs(nakshatra_balance(lon) - 0.5) < 0.01
