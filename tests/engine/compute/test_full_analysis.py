"""Tests for the full chart analysis — all computations in one call."""

from __future__ import annotations

from daivai_engine.compute.full_analysis import compute_full_analysis
from daivai_engine.models.chart import ChartData


def _lordship(chart: ChartData) -> dict:
    from daivai_products.interpret.context import build_lordship_context

    return build_lordship_context(chart.lagna_sign)


class TestFullChartAnalysis:
    def test_core_fields(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart, lordship_context=_lordship(manish_chart))
        assert a.version == "3.0"
        assert len(a.mahadashas) == 9
        assert len(a.shadbala) == 7
        assert len(a.gandanta) == 9
        assert len(a.double_transit) == 12

    def test_new_modules(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert len(a.narayana_dasha) == 12
        assert len(a.dasha_sandhi) == 8
        assert a.gand_mool is not None
        assert a.longevity is not None
        assert a.mangal_dosha is not None
        assert len(a.varga_analysis) == 4
        assert "D7" in a.varga_analysis
        assert "D10" in a.varga_analysis

    def test_transit_advanced(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert a.sadesati is not None
        assert a.jupiter_transit is not None
        assert a.rahu_ketu_transit is not None

    def test_existing_modules_still_work(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert len(a.argala) == 12
        assert a.sudarshan is not None
        assert len(a.sahams) == 6
        assert "hora" in a.special_lagnas

    def test_deterministic(self, manish_chart: ChartData) -> None:
        a1 = compute_full_analysis(manish_chart)
        a2 = compute_full_analysis(manish_chart)
        assert a1.shadbala == a2.shadbala
        assert a1.gandanta == a2.gandanta
        assert a1.upapada == a2.upapada

    def test_verification_clean(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        errors = [w for w in a.verification_warnings if w.startswith("L1")]
        assert len(errors) == 0

    def test_json_roundtrip(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        json_str = a.model_dump_json()
        from daivai_engine.models.analysis import FullChartAnalysis

        restored = FullChartAnalysis.model_validate_json(json_str)
        assert restored.chart.name == a.chart.name
        assert len(restored.shadbala) == len(a.shadbala)
