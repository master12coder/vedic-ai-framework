"""Tests for Dasha-Transit integration — structural and BAV tests.

Covers:
  - Structural validity of DashaTransitAnalysis output
  - BAV bindu integration in transit scoring
  - Double transit activation on dasha lord houses
  - Transit house computation
  - Event domain mapping from active houses
  - Model immutability
  - Two charts (Manish reference + sample)

Fixture:
  manish_chart: Mithuna lagna, Moon in Rohini Pada 2.
  Current MD = Jupiter (7th lord / maraka).
"""

from __future__ import annotations

from datetime import datetime

import pytest
import pytz

from daivai_engine.compute.dasha_transit import compute_dasha_transit
from daivai_engine.compute.dasha_transit_helpers import (
    _classify_bav,
    _get_houses_owned,
)
from daivai_engine.compute.dasha_transit_scoring import (
    compute_score,
    score_to_favorability,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha_transit import (
    DashaLordTransit,
    DashaTransitAnalysis,
    DoubleTransitOnDashaHouses,
)


_DATE = datetime(2026, 3, 22, 12, 0, 0, tzinfo=pytz.UTC)


class TestComputeDashaTransit:
    """Structural tests for compute_dasha_transit() output."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> DashaTransitAnalysis:
        return compute_dasha_transit(manish_chart, _DATE)

    def test_returns_dasha_transit_analysis(self, result: DashaTransitAnalysis) -> None:
        assert isinstance(result, DashaTransitAnalysis)

    def test_analysis_date_formatted(self, result: DashaTransitAnalysis) -> None:
        assert result.analysis_date == "22/03/2026"

    def test_md_lord_is_dasha_lord_transit(self, result: DashaTransitAnalysis) -> None:
        assert isinstance(result.md_lord, DashaLordTransit)
        assert result.md_lord.dasha_level == "MD"

    def test_ad_lord_is_dasha_lord_transit(self, result: DashaTransitAnalysis) -> None:
        assert isinstance(result.ad_lord, DashaLordTransit)
        assert result.ad_lord.dasha_level == "AD"

    def test_pd_lord_present(self, result: DashaTransitAnalysis) -> None:
        assert result.pd_lord is not None
        assert result.pd_lord.dasha_level == "PD"

    def test_md_lord_is_jupiter_for_manish(self, result: DashaTransitAnalysis) -> None:
        assert result.md_lord.lord == "Jupiter"

    def test_dt_activation_not_empty(self, result: DashaTransitAnalysis) -> None:
        assert len(result.double_transit_activation) >= 2

    def test_dt_activation_items_valid(self, result: DashaTransitAnalysis) -> None:
        for dt in result.double_transit_activation:
            assert isinstance(dt, DoubleTransitOnDashaHouses)
            assert 1 <= dt.house <= 12
            assert dt.both_activate == (dt.jupiter_activates and dt.saturn_activates)
            assert len(dt.house_signification) > 0

    def test_md_ad_relationship_valid(self, result: DashaTransitAnalysis) -> None:
        assert result.md_ad_relationship in ("friends", "neutral", "enemies")

    def test_overall_favorability_valid(self, result: DashaTransitAnalysis) -> None:
        valid = {"highly_favorable", "favorable", "mixed", "challenging", "difficult"}
        assert result.overall_favorability in valid

    def test_active_houses_in_range(self, result: DashaTransitAnalysis) -> None:
        for h in result.active_houses:
            assert 1 <= h <= 12

    def test_event_domains_are_strings(self, result: DashaTransitAnalysis) -> None:
        for domain in result.event_domains:
            assert isinstance(domain, str) and len(domain) > 0

    def test_summary_mentions_md_lord(self, result: DashaTransitAnalysis) -> None:
        assert result.md_lord.lord in result.summary

    def test_second_chart(self, sample_chart: ChartData) -> None:
        result = compute_dasha_transit(sample_chart, _DATE)
        assert isinstance(result, DashaTransitAnalysis)


class TestBavIntegration:
    """Tests for BAV bindu scoring in dasha lord transit."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> DashaTransitAnalysis:
        return compute_dasha_transit(manish_chart, _DATE)

    def test_md_bav_in_range(self, result: DashaTransitAnalysis) -> None:
        assert 0 <= result.md_lord.bav_bindus <= 8

    def test_ad_bav_in_range(self, result: DashaTransitAnalysis) -> None:
        assert 0 <= result.ad_lord.bav_bindus <= 8

    def test_pd_bav_in_range(self, result: DashaTransitAnalysis) -> None:
        if result.pd_lord:
            assert 0 <= result.pd_lord.bav_bindus <= 8

    def test_bav_strength_consistent(self, result: DashaTransitAnalysis) -> None:
        for lord in [result.md_lord, result.ad_lord]:
            if lord.bav_bindus >= 5:
                assert lord.bav_strength == "strong"
            elif lord.bav_bindus >= 3:
                assert lord.bav_strength == "moderate"
            else:
                assert lord.bav_strength == "weak"


class TestClassifyBav:
    """Tests for _classify_bav helper."""

    def test_strong_at_5(self) -> None:
        assert _classify_bav(5) == "strong"

    def test_strong_at_8(self) -> None:
        assert _classify_bav(8) == "strong"

    def test_moderate_at_3(self) -> None:
        assert _classify_bav(3) == "moderate"

    def test_moderate_at_4(self) -> None:
        assert _classify_bav(4) == "moderate"

    def test_weak_at_0(self) -> None:
        assert _classify_bav(0) == "weak"

    def test_weak_at_2(self) -> None:
        assert _classify_bav(2) == "weak"


class TestScoring:
    """Tests for composite scoring and favorability classification."""

    def test_max_score(self) -> None:
        assert compute_score(8, "exalted", 1) == 100

    def test_min_score(self) -> None:
        assert compute_score(0, "debilitated", 6) == 13

    def test_moderate_score(self) -> None:
        assert compute_score(4, "neutral", 7) == 60

    def test_capped_at_100(self) -> None:
        assert compute_score(8, "exalted", 1) <= 100

    def test_favorable_above_55(self) -> None:
        assert score_to_favorability(60) == "favorable"

    def test_neutral_35_54(self) -> None:
        assert score_to_favorability(40) == "neutral"

    def test_unfavorable_below_35(self) -> None:
        assert score_to_favorability(20) == "unfavorable"

    def test_score_in_range_real_chart(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        assert 0 <= result.md_lord.score <= 100
        assert 0 <= result.ad_lord.score <= 100


class TestHousesOwned:
    """Tests for _get_houses_owned."""

    def test_jupiter_for_mithuna(self, manish_chart: ChartData) -> None:
        houses = _get_houses_owned(manish_chart, "Jupiter")
        assert 7 in houses and 10 in houses

    def test_mercury_for_mithuna(self, manish_chart: ChartData) -> None:
        houses = _get_houses_owned(manish_chart, "Mercury")
        assert 1 in houses and 4 in houses

    def test_sun_owns_one(self, manish_chart: ChartData) -> None:
        assert len(_get_houses_owned(manish_chart, "Sun")) == 1

    def test_moon_owns_one(self, manish_chart: ChartData) -> None:
        assert len(_get_houses_owned(manish_chart, "Moon")) == 1


class TestDoubleTransitOnDasha:
    """Tests for double transit activation of dasha lord houses."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> DashaTransitAnalysis:
        return compute_dasha_transit(manish_chart, _DATE)

    def test_houses_are_dasha_owned(self, result: DashaTransitAnalysis) -> None:
        dasha_houses = set(result.md_lord.houses_owned + result.ad_lord.houses_owned)
        for dt in result.double_transit_activation:
            assert dt.house in dasha_houses

    def test_both_requires_both(self, result: DashaTransitAnalysis) -> None:
        for dt in result.double_transit_activation:
            if dt.both_activate:
                assert dt.jupiter_activates and dt.saturn_activates

    def test_active_subset_of_both(self, result: DashaTransitAnalysis) -> None:
        both_active = {dt.house for dt in result.double_transit_activation if dt.both_activate}
        for h in result.active_houses:
            assert h in both_active


class TestEventDomainMapping:
    """Tests for mapping active houses to life domains."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> DashaTransitAnalysis:
        return compute_dasha_transit(manish_chart, _DATE)

    def test_domains_count(self, result: DashaTransitAnalysis) -> None:
        assert len(result.event_domains) == len(result.active_houses)

    def test_known_domains(self, result: DashaTransitAnalysis) -> None:
        known = {
            "self/health",
            "wealth/family",
            "siblings/courage",
            "home/mother",
            "children/creativity",
            "enemies/disease",
            "marriage/partnership",
            "transformation/longevity",
            "fortune/father",
            "career/status",
            "gains/income",
            "loss/liberation",
        }
        for domain in result.event_domains:
            assert domain in known


class TestTransitHouses:
    """Tests for transit house calculations."""

    @pytest.fixture
    def result(self, manish_chart: ChartData) -> DashaTransitAnalysis:
        return compute_dasha_transit(manish_chart, _DATE)

    def test_md_houses_in_range(self, result: DashaTransitAnalysis) -> None:
        assert 1 <= result.md_lord.transit_house_from_lagna <= 12
        assert 1 <= result.md_lord.transit_house_from_moon <= 12
        assert 1 <= result.md_lord.transit_house_from_natal <= 12

    def test_ad_houses_in_range(self, result: DashaTransitAnalysis) -> None:
        assert 1 <= result.ad_lord.transit_house_from_lagna <= 12
        assert 1 <= result.ad_lord.transit_house_from_moon <= 12

    def test_natal_house_matches_chart(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        md_lord_name = result.md_lord.lord
        assert result.md_lord.natal_house == manish_chart.planets[md_lord_name].house

    def test_natal_dignity_matches_chart(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        md_lord_name = result.md_lord.lord
        assert result.md_lord.natal_dignity == manish_chart.planets[md_lord_name].dignity


class TestModelFrozen:
    """Pydantic models should be frozen (immutable)."""

    def test_analysis_frozen(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        with pytest.raises((TypeError, Exception)):
            result.summary = "hacked"  # type: ignore[misc]

    def test_lord_transit_frozen(self, manish_chart: ChartData) -> None:
        result = compute_dasha_transit(manish_chart, _DATE)
        with pytest.raises((TypeError, Exception)):
            result.md_lord.score = 99  # type: ignore[misc]
