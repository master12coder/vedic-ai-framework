"""Tests for advanced dasha features — sandhi, sookshma, prana."""

from __future__ import annotations

from daivai_engine.compute.dasha import (
    compute_antardashas,
    compute_mahadashas,
    compute_pratyantardashas,
)
from daivai_engine.compute.dasha_advanced import (
    compute_dasha_sandhi,
    compute_prana_dasha,
    compute_sookshma_dasha,
    detect_dasha_sandhi,
)
from daivai_engine.models.chart import ChartData


class TestDashaSandhi:
    def test_returns_eight_sandhis(self, manish_chart: ChartData) -> None:
        """9 MDs → 8 transitions."""
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        assert len(sandhis) == 8

    def test_nature_valid(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        valid = {"easy", "challenging", "transformative"}
        for s in sandhis:
            assert s.nature in valid


class TestSookshmaDasha:
    def test_returns_nine_periods(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        pds = compute_pratyantardashas(ads[0])
        sds = compute_sookshma_dasha(pds[0])
        assert len(sds) == 9

    def test_level_is_sd(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        pds = compute_pratyantardashas(ads[0])
        sds = compute_sookshma_dasha(pds[0])
        for s in sds:
            assert s.level == "SD"


class TestPranaDasha:
    def test_returns_nine_periods(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        pds = compute_pratyantardashas(ads[0])
        sds = compute_sookshma_dasha(pds[0])
        prs = compute_prana_dasha(sds[0])
        assert len(prs) == 9
        for p in prs:
            assert p.level == "PR"


class TestDashaSandhiSeverity:
    def test_severity_in_valid_range(self, manish_chart: ChartData) -> None:
        """compute_dasha_sandhi now returns severity 1-3."""
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        for s in sandhis:
            assert s.severity in (1, 2, 3), f"Invalid severity: {s.severity}"

    def test_is_malefic_transition_flag(self, manish_chart: ChartData) -> None:
        """is_malefic_transition = True only when both lords are natural malefics."""
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
        for s in sandhis:
            both_malefic = s.ending_lord in malefics and s.starting_lord in malefics
            assert s.is_malefic_transition == both_malefic

    def test_malefic_transition_has_severity_3(self, manish_chart: ChartData) -> None:
        """Both-malefic transitions must have severity 3."""
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        for s in sandhis:
            if s.is_malefic_transition:
                assert s.severity == 3

    def test_md_level_tag(self, manish_chart: ChartData) -> None:
        """compute_dasha_sandhi output must have level='MD'."""
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        for s in sandhis:
            assert s.level == "MD"

    def test_jupiter_saturn_transition_manish(self, manish_chart: ChartData) -> None:
        """Jupiter (benefic) → Saturn (malefic) must be transformative, severity 2.

        Manish's dasha sequence: Moon→Mars→Rahu→Jupiter→Saturn.
        Jupiter MD is current (2026), Saturn follows — this transition must exist.
        """
        mds = compute_mahadashas(manish_chart)
        sandhis = compute_dasha_sandhi(mds)
        jup_sat = next(
            (s for s in sandhis if s.ending_lord == "Jupiter" and s.starting_lord == "Saturn"),
            None,
        )
        assert jup_sat is not None, "Jupiter→Saturn MD transition not found in Manish's chart"
        assert jup_sat.nature == "transformative"
        assert jup_sat.severity == 2
        assert jup_sat.is_malefic_transition is False  # Jupiter is benefic


class TestDetectDashaSandhi:
    def test_md_only_returns_eight(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        results = detect_dasha_sandhi(mds)
        assert len(results) == 8

    def test_md_only_all_levels_md(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        results = detect_dasha_sandhi(mds)
        for r in results:
            assert r.level == "MD"

    def test_with_antardashas_adds_ad_sandhis(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        results = detect_dasha_sandhi(mds, ads)
        md_count = sum(1 for r in results if r.level == "MD")
        ad_count = sum(1 for r in results if r.level == "AD")
        assert md_count == 8
        assert ad_count == 8  # 9 ADs → 8 transitions

    def test_ad_sandhis_have_ad_level(self, manish_chart: ChartData) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        results = detect_dasha_sandhi(mds, ads)
        ad_sandhis = [r for r in results if r.level == "AD"]
        assert len(ad_sandhis) == 8
        for r in ad_sandhis:
            assert r.level == "AD"
