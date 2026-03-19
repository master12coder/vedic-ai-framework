"""Tests for Ishta-Kashta Phala computation."""

from __future__ import annotations

from daivai_engine.compute.ishta_kashta import compute_ishta_kashta
from daivai_engine.compute.strength import compute_shadbala
from daivai_engine.models.chart import ChartData


class TestIshtaKashta:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        sb = compute_shadbala(manish_chart)
        results = compute_ishta_kashta(manish_chart, sb)
        assert len(results) == 7

    def test_ishta_kashta_non_negative(self, manish_chart: ChartData) -> None:
        sb = compute_shadbala(manish_chart)
        results = compute_ishta_kashta(manish_chart, sb)
        for ik in results:
            assert ik.ishta_phala >= 0.0
            assert ik.kashta_phala >= 0.0

    def test_moon_strongly_benefic_for_manish(self, manish_chart: ChartData) -> None:
        """Moon exalted = high Uchcha Bala = strongly benefic."""
        sb = compute_shadbala(manish_chart)
        results = compute_ishta_kashta(manish_chart, sb)
        moon = next(ik for ik in results if ik.planet == "Moon")
        assert moon.net_effect > 0
        assert moon.classification == "strongly_benefic"

    def test_valid_classifications(self, manish_chart: ChartData) -> None:
        valid = {
            "strongly_benefic",
            "mildly_benefic",
            "neutral",
            "mildly_malefic",
            "strongly_malefic",
        }
        sb = compute_shadbala(manish_chart)
        results = compute_ishta_kashta(manish_chart, sb)
        for ik in results:
            assert ik.classification in valid
