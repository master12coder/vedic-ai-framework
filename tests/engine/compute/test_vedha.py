"""Tests for Vedha (transit obstruction) detection."""

from __future__ import annotations

from daivai_engine.compute.vedha import check_vedha
from daivai_engine.models.chart import ChartData


class TestVedha:
    def test_vedha_returns_results(self, manish_chart: ChartData) -> None:
        """Check vedha for Saturn's natal position."""
        sat = manish_chart.planets["Saturn"]
        results = check_vedha(manish_chart, "Saturn", sat.sign_index)
        # May be empty if transit house is 7 or 11 (no vedha)
        assert isinstance(results, list)

    def test_vedha_has_correct_structure(self, manish_chart: ChartData) -> None:
        sat = manish_chart.planets["Saturn"]
        results = check_vedha(manish_chart, "Saturn", sat.sign_index)
        for v in results:
            assert 1 <= v.benefic_house <= 12
            assert 1 <= v.vedha_house <= 12
            assert isinstance(v.is_blocked, bool)

    def test_no_vedha_for_house_7_and_11(self, manish_chart: ChartData) -> None:
        """Houses 7 and 11 have no vedha pair."""
        moon = manish_chart.planets["Moon"]
        # Transit to house 7 from Moon
        transit_sign = (moon.sign_index + 6) % 12
        results = check_vedha(manish_chart, "Jupiter", transit_sign)
        assert len(results) == 0
