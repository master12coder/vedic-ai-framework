"""Tests for upgraded Varshphal — Tri-pataki Chakra."""

from __future__ import annotations

from daivai_engine.compute.varshphal import compute_tri_pataki, compute_varshphal
from daivai_engine.models.chart import ChartData


class TestTriPatakiChakra:
    def test_tri_pataki_returned_in_varshphal(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        assert "tri_pataki" in result
        assert result["tri_pataki"] is not None

    def test_tri_pataki_has_three_sectors(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        tp = result["tri_pataki"]
        assert "lagna_sector" in tp
        assert "muntha_sector" in tp
        assert "year_lord_sector" in tp

    def test_each_sector_has_trikona_signs(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        tp = result["tri_pataki"]
        for sector_name in ("lagna_sector", "muntha_sector", "year_lord_sector"):
            sector = tp[sector_name]
            assert "trikona_signs" in sector
            assert len(sector["trikona_signs"]) == 3

    def test_trikona_signs_are_valid_signs(self, manish_chart: ChartData) -> None:
        from daivai_engine.constants import SIGNS

        result = compute_varshphal(manish_chart, 2026)
        tp = result["tri_pataki"]
        for sector_name in ("lagna_sector", "muntha_sector", "year_lord_sector"):
            for sign_name in tp[sector_name]["trikona_signs"]:
                assert sign_name in SIGNS, f"Invalid sign: {sign_name}"

    def test_activated_planets_are_valid(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        tp = result["tri_pataki"]
        sr_chart = result["chart"]
        valid_planets = set(sr_chart.planets.keys())
        for sector_name in ("lagna_sector", "muntha_sector", "year_lord_sector"):
            for planet in tp[sector_name]["activated_planets"]:
                assert planet in valid_planets, (
                    f"{sector_name}: planet '{planet}' not in annual chart"
                )

    def test_compute_tri_pataki_standalone(self, manish_chart: ChartData) -> None:
        """Standalone function should work with a chart and muntha sign."""
        sr_result = compute_varshphal(manish_chart, 2026)
        sr_chart = sr_result["chart"]
        muntha = sr_result["muntha_sign"]
        tp = compute_tri_pataki(sr_chart, muntha)
        assert tp["muntha_sector"]["anchor_sign"] == muntha

    def test_sector_has_theme(self, manish_chart: ChartData) -> None:
        result = compute_varshphal(manish_chart, 2026)
        tp = result["tri_pataki"]
        for sector_name in ("lagna_sector", "muntha_sector", "year_lord_sector"):
            assert len(tp[sector_name]["theme"]) > 10

    def test_year_lord_in_sector(self, manish_chart: ChartData) -> None:
        """Year lord sector should have year_lord field."""
        result = compute_varshphal(manish_chart, 2026)
        tp = result["tri_pataki"]
        assert "year_lord" in tp["year_lord_sector"]
        valid_lords = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert tp["year_lord_sector"]["year_lord"] in valid_lords
