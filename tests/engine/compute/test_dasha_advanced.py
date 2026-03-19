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
