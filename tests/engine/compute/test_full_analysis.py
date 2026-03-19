"""Tests for the full chart analysis — all computations in one call."""

from __future__ import annotations

from daivai_engine.compute.full_analysis import compute_full_analysis
from daivai_engine.models.chart import ChartData


def _lordship(chart: ChartData) -> dict:
    """Build lordship context via products layer (test helper)."""
    from daivai_products.interpret.context import build_lordship_context

    return build_lordship_context(chart.lagna_sign)


class TestFullChartAnalysis:
    def test_full_analysis_returns_all_fields(self, manish_chart: ChartData) -> None:
        ctx = _lordship(manish_chart)
        analysis = compute_full_analysis(manish_chart, lordship_context=ctx)
        assert analysis.chart.name == "Manish Chaurasia"
        assert len(analysis.mahadashas) == 9
        assert analysis.current_md is not None
        assert analysis.current_ad is not None
        assert len(analysis.shadbala) == 7
        assert len(analysis.gandanta) == 9
        assert len(analysis.deeptadi_avasthas) == 7
        assert len(analysis.lajjitadi_avasthas) == 7
        assert len(analysis.vimshopaka) == 7
        assert len(analysis.ishta_kashta) == 7
        assert len(analysis.double_transit) == 12
        assert len(analysis.double_transit_moon) == 12
        assert analysis.upapada is not None
        assert isinstance(analysis.verification_warnings, list)

    def test_full_analysis_deterministic(self, manish_chart: ChartData) -> None:
        """Same input must produce same output."""
        a1 = compute_full_analysis(manish_chart)
        a2 = compute_full_analysis(manish_chart)
        assert a1.shadbala == a2.shadbala
        assert a1.gandanta == a2.gandanta
        assert a1.graha_yuddha == a2.graha_yuddha
        assert a1.upapada == a2.upapada

    def test_full_analysis_has_lordship_context(self, manish_chart: ChartData) -> None:
        ctx = _lordship(manish_chart)
        analysis = compute_full_analysis(manish_chart, lordship_context=ctx)
        assert "functional_benefics" in analysis.lordship_context
        assert "functional_malefics" in analysis.lordship_context

    def test_verification_clean(self, manish_chart: ChartData) -> None:
        """Manish chart should pass all verification checks."""
        analysis = compute_full_analysis(manish_chart)
        errors = [w for w in analysis.verification_warnings if w.startswith("ERROR")]
        assert len(errors) == 0

    def test_json_roundtrip(self, manish_chart: ChartData) -> None:
        """FullChartAnalysis should survive JSON serialization."""
        analysis = compute_full_analysis(manish_chart)
        json_str = analysis.model_dump_json()
        from daivai_engine.models.analysis import FullChartAnalysis

        restored = FullChartAnalysis.model_validate_json(json_str)
        assert restored.chart.name == analysis.chart.name
        assert len(restored.shadbala) == len(analysis.shadbala)
        assert len(restored.gandanta) == len(analysis.gandanta)
