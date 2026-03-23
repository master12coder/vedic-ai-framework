"""Tests for the full chart analysis v5.0 — all modules wired in."""

from __future__ import annotations

from daivai_engine.compute.full_analysis import compute_full_analysis
from daivai_engine.models.chart import ChartData


def _lordship(chart: ChartData) -> dict:
    from daivai_products.interpret.context import build_lordship_context

    return build_lordship_context(chart.lagna_sign)


class TestFullAnalysisV4:
    def test_version(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert a.version == "5.0"

    def test_core_fields(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart, lordship_context=_lordship(manish_chart))
        assert len(a.mahadashas) == 9
        assert len(a.shadbala) == 7
        assert len(a.double_transit) == 12

    def test_yoga_count_extended(self, manish_chart: ChartData) -> None:
        """Extended yoga engine should find many more yogas."""
        a = compute_full_analysis(manish_chart)
        assert len(a.yogas) >= 10

    def test_dosha_count_10(self, manish_chart: ChartData) -> None:
        """4 original + 6 extended = 10 doshas checked."""
        a = compute_full_analysis(manish_chart)
        assert len(a.doshas) == 10

    def test_all_dasha_systems(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert len(a.narayana_dasha) >= 1
        assert len(a.yogini_dasha) >= 1
        assert len(a.ashtottari_dasha) >= 1
        assert len(a.chara_dasha) >= 1
        assert len(a.dasha_sandhi) >= 1

    def test_orphaned_modules_wired(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert a.jaimini is not None
        assert len(a.kp_positions) >= 1
        assert a.bhava_chalit is not None
        assert len(a.upagrahas) >= 1
        assert len(a.navamsha_positions) >= 1
        assert isinstance(a.vargottam_planets, list)
        assert a.birth_panchang is not None

    def test_bhava_bala(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        assert len(a.bhava_bala) == 12

    def test_deterministic(self, manish_chart: ChartData) -> None:
        a1 = compute_full_analysis(manish_chart)
        a2 = compute_full_analysis(manish_chart)
        assert a1.shadbala == a2.shadbala
        assert a1.gandanta == a2.gandanta

    def test_json_roundtrip(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        json_str = a.model_dump_json()
        from daivai_engine.models.analysis import FullChartAnalysis

        restored = FullChartAnalysis.model_validate_json(json_str)
        assert restored.chart.name == a.chart.name

    def test_verification_clean(self, manish_chart: ChartData) -> None:
        a = compute_full_analysis(manish_chart)
        errors = [w for w in a.verification_warnings if w.startswith("L1")]
        assert len(errors) == 0
