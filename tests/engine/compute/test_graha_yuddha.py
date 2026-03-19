"""Tests for graha yuddha (planetary war) detection."""

from __future__ import annotations

from daivai_engine.compute.graha_yuddha import detect_planetary_war
from daivai_engine.models.chart import ChartData


class TestGrahaYuddha:
    def test_manish_chart_has_mars_jupiter_war(self, manish_chart: ChartData) -> None:
        """Mars and Jupiter are within 1 degree in Manish's chart."""
        wars = detect_planetary_war(manish_chart)
        assert len(wars) >= 1
        pair_names = {(w.planet1, w.planet2) for w in wars}
        assert ("Mars", "Jupiter") in pair_names or ("Jupiter", "Mars") in pair_names

    def test_war_has_winner_and_loser(self, manish_chart: ChartData) -> None:
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert w.winner in (w.planet1, w.planet2)
            assert w.loser in (w.planet1, w.planet2)
            assert w.winner != w.loser

    def test_separation_under_one_degree(self, manish_chart: ChartData) -> None:
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert w.separation_degrees <= 1.0

    def test_affected_houses_not_empty(self, manish_chart: ChartData) -> None:
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert len(w.affected_houses) > 0

    def test_no_sun_moon_in_war(self, manish_chart: ChartData) -> None:
        """Sun and Moon should never participate in planetary war."""
        wars = detect_planetary_war(manish_chart)
        for w in wars:
            assert w.planet1 not in ("Sun", "Moon", "Rahu", "Ketu")
            assert w.planet2 not in ("Sun", "Moon", "Rahu", "Ketu")
