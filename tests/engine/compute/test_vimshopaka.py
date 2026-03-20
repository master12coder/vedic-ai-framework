"""Tests for Vimshopaka Bala computation."""

from __future__ import annotations

from daivai_engine.compute.vimshopaka import compute_vimshopaka_bala
from daivai_engine.models.chart import ChartData


class TestVimshopakaBala:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        assert len(results) == 7

    def test_shodashavarga_score_bounded(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.shodashavarga_score <= 20.0

    def test_saptvarga_score_bounded(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.saptvarga_score <= 20.0

    def test_dashavarga_score_bounded(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.dashavarga_score <= 20.0

    def test_shadvarga_score_bounded(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.shadvarga_score <= 10.0

    def test_percentage_between_0_and_100(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert 0.0 <= v.percentage <= 100.0

    def test_dignity_map_has_all_16_vargas(self, manish_chart: ChartData) -> None:
        expected = {"D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
                    "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"}
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            assert expected.issubset(v.dignity_in_each.keys())

    def test_dignity_values_valid(self, manish_chart: ChartData) -> None:
        valid = {"exalted", "mooltrikona", "own", "friend", "neutral", "enemy", "debilitated"}
        results = compute_vimshopaka_bala(manish_chart)
        for v in results:
            for varga, dig in v.dignity_in_each.items():
                assert dig in valid, f"{v.planet} in {varga}: unexpected dignity '{dig}'"

    def test_moon_exalted_in_d1(self, manish_chart: ChartData) -> None:
        """Moon is exalted in Taurus (D1) for Manish's chart."""
        results = compute_vimshopaka_bala(manish_chart)
        moon = next(v for v in results if v.planet == "Moon")
        assert moon.dignity_in_each["D1"] == "exalted"

    def test_sorted_descending(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        scores = [v.shodashavarga_score for v in results]
        assert scores == sorted(scores, reverse=True)

    def test_all_planets_present(self, manish_chart: ChartData) -> None:
        results = compute_vimshopaka_bala(manish_chart)
        names = {v.planet for v in results}
        assert names == {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
