"""Tests for Varshphal (annual chart / solar return) computation."""

from __future__ import annotations

from daivai_engine.compute.varshphal import compute_varshphal
from daivai_engine.models.chart import ChartData


class TestVarshphal:
    def test_varshphal_2026_for_manish(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        assert result["year"] == 2026
        assert result["chart"] is not None
        assert result["solar_return_date"]
        assert result["year_lord"]

    def test_solar_return_date_in_march(self, manish_chart: ChartData) -> None:
        """Sun born ~29° Aquarius → returns around March 13-14."""
        result = compute_varshphal(manish_chart, 2026)
        sr_date = result["solar_return_date"]
        # Should be in March (Sun at ~29° Aquarius)
        assert "2026-03" in sr_date

    def test_muntha_sign_calculated(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        # Age 37 in 2026 → 37 % 12 = 1 sign from Mithuna(2) → sign 3 (Karka)
        assert 0 <= result["muntha_sign"] <= 11

    def test_year_lord_valid(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        valid_lords = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert result["year_lord"] in valid_lords

    def test_tajaka_yogas_list(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        assert isinstance(result["tajaka_yogas"], list)

    def test_different_year_different_chart(self, manish_chart: ChartData) -> None:
        r2025 = compute_varshphal(manish_chart, 2025)
        r2026 = compute_varshphal(manish_chart, 2026)
        assert r2025["solar_return_date"] != r2026["solar_return_date"]

    def test_muntha_sign_2026_is_karka(self, manish_chart: ChartData) -> None:
        """2026 Muntha for Manish: age = 2026-1989 = 37.
        muntha = (lagna_sign_index + age) % 12 = (2 + 37) % 12 = 39 % 12 = 3 = Karka.
        """
        result = compute_varshphal(manish_chart, 2026)
        assert result["muntha_sign"] == 3  # Karka (Cancer)

    def test_tajaka_yogas_are_non_empty(self, manish_chart: ChartData) -> None:
        """Annual chart must produce at least some Tajaka yogas (Manaou at minimum)."""
        result = compute_varshphal(manish_chart, 2026)
        assert len(result["tajaka_yogas"]) > 0
