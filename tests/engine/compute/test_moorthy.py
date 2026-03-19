"""Tests for Moorthy Nirnaya (transit quality) classification."""

from __future__ import annotations

from daivai_engine.compute.moorthy import classify_transit_moorthy
from daivai_engine.models.chart import ChartData


class TestMoorthyNirnaya:
    def test_classification_valid(self, manish_chart: ChartData) -> None:
        jup = manish_chart.planets["Jupiter"]
        m = classify_transit_moorthy(manish_chart, "Jupiter", jup.sign_index)
        assert m.classification in ("swarna", "rajata", "tamra", "loha")

    def test_hindi_classification(self, manish_chart: ChartData) -> None:
        jup = manish_chart.planets["Jupiter"]
        m = classify_transit_moorthy(manish_chart, "Jupiter", jup.sign_index)
        valid_hi = {"स्वर्ण", "रजत", "ताम्र", "लोह"}
        assert m.classification_hi in valid_hi

    def test_bindus_non_negative(self, manish_chart: ChartData) -> None:
        for sign in range(12):
            m = classify_transit_moorthy(manish_chart, "Saturn", sign)
            assert m.bindus >= 0

    def test_swarna_for_high_bindu_sign(self, manish_chart: ChartData) -> None:
        """Find a sign with 30+ SAV bindus and verify it's swarna."""
        from daivai_engine.compute.ashtakavarga import compute_ashtakavarga

        avk = compute_ashtakavarga(manish_chart)
        high_sign = None
        for i, b in enumerate(avk.sarva):
            if b >= 30:
                high_sign = i
                break
        if high_sign is not None:
            m = classify_transit_moorthy(manish_chart, "Jupiter", high_sign)
            assert m.classification == "swarna"
