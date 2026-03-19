"""Tests for Vimshopaka Bala computation."""

from __future__ import annotations

from daivai_engine.compute.vimshopaka import compute_vimshopaka_bala
from daivai_engine.models.chart import ChartData


class TestVimshopakaBala:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        assert len(results) == 7

    def test_score_between_0_and_20(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.shodashavarga_score <= 20.0

    def test_percentage_between_0_and_100(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.percentage <= 100.0

    def test_moon_strongest_for_manish(self, manish_chart: ChartData) -> None:
        """Moon exalted in D1 should score highly."""
        results = compute_vimshopaka_bala(manish_chart)
        # Results are sorted descending by score
        assert results[0].planet == "Moon"

    def test_dignity_map_has_d1_and_d9(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert "D1" in v.dignity_in_each
            assert "D9" in v.dignity_in_each

    def test_sorted_descending(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        scores = [v.shodashavarga_score for v in results]
        assert scores == sorted(scores, reverse=True)
