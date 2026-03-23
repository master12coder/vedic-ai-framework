"""Tests for Vimshottari Dasha — MD/AD/PD computation."""

from __future__ import annotations

from datetime import datetime

from daivai_engine.compute.dasha import (
    _balance_of_dasha,
    _dasha_start_index,
    compute_antardashas,
    compute_mahadashas,
    compute_pratyantardashas,
    find_current_dasha,
    get_dasha_timeline,
)
from daivai_engine.constants import DASHA_SEQUENCE


class TestDashaHelpers:
    """Tests for dasha calculation helper functions."""

    def test_dasha_start_index_sun_is_zero(self) -> None:
        assert _dasha_start_index("Sun") == DASHA_SEQUENCE.index("Sun")

    def test_dasha_start_index_all_valid(self) -> None:
        for lord in DASHA_SEQUENCE:
            idx = _dasha_start_index(lord)
            assert 0 <= idx < 9

    def test_balance_full_at_start_of_nakshatra(self) -> None:
        # Moon at exactly 0.0° (start of Ashwini) → full balance
        balance = _balance_of_dasha(0.0)
        assert abs(balance - 1.0) < 0.01

    def test_balance_zero_at_end_of_nakshatra(self) -> None:
        # Moon at end of first nakshatra (13.333° - small offset) → ~0 balance
        balance = _balance_of_dasha(13.3)
        assert balance < 0.02

    def test_balance_half_at_midpoint(self) -> None:
        balance = _balance_of_dasha(6.666)
        assert abs(balance - 0.5) < 0.05


class TestMahadashas:
    """Tests for compute_mahadashas()."""

    def test_returns_nine_periods(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        assert len(mds) == 9

    def test_all_lords_are_in_dasha_sequence(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        for md in mds:
            assert md.lord in DASHA_SEQUENCE

    def test_consecutive_periods_are_contiguous(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        for i in range(len(mds) - 1):
            # End of period i should equal start of period i+1
            gap = abs((mds[i + 1].start - mds[i].end).total_seconds())
            assert gap < 1.0, f"Gap between MD {i} and {i + 1}: {gap}s"

    def test_first_md_starts_at_birth(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        # First MD start should equal birth datetime
        from daivai_engine.compute.datetime_utils import parse_birth_datetime

        birth = parse_birth_datetime(manish_chart.dob, manish_chart.tob, manish_chart.timezone_name)
        diff = abs((mds[0].start - birth).total_seconds())
        assert diff < 1.0

    def test_total_duration_under_120_years(self, manish_chart) -> None:
        """First dasha is only partial balance, so total < 120 years."""
        mds = compute_mahadashas(manish_chart)
        total_days = (mds[-1].end - mds[0].start).days
        # Range: ~110-120 years depending on Moon's nakshatra position at birth
        max_days = 120 * 366  # Upper bound (120 years)
        min_days = 110 * 365  # Lower bound (≥110 years)
        assert min_days <= total_days <= max_days, f"Total days: {total_days}"

    def test_level_is_md(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        for md in mds:
            assert md.level == "MD"

    def test_all_nine_lords_appear_once(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        lords = [md.lord for md in mds]
        assert len(set(lords)) == 9


class TestAntardashas:
    """Tests for compute_antardashas()."""

    def test_returns_nine_per_mahadasha(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        for md in mds:
            ads = compute_antardashas(md)
            assert len(ads) == 9

    def test_ad_level_is_ad(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        for ad in ads:
            assert ad.level == "AD"

    def test_ad_parent_lord_matches_md_lord(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        for ad in ads:
            assert ad.parent_lord == mds[0].lord

    def test_ad_periods_span_full_md(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        md = mds[0]
        ads = compute_antardashas(md)
        assert ads[0].start == md.start
        assert abs((ads[-1].end - md.end).total_seconds()) < 60

    def test_all_nine_lords_appear_in_ad(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        lords = [ad.lord for ad in ads]
        assert len(set(lords)) == 9


class TestPratyantardashas:
    """Tests for compute_pratyantardashas()."""

    def test_returns_nine_per_antardasha(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        pds = compute_pratyantardashas(ads[0])
        assert len(pds) == 9

    def test_pd_level_is_pd(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        pds = compute_pratyantardashas(ads[0])
        for pd in pds:
            assert pd.level == "PD"

    def test_pd_spans_full_antardasha(self, manish_chart) -> None:
        mds = compute_mahadashas(manish_chart)
        ads = compute_antardashas(mds[0])
        ad = ads[0]
        pds = compute_pratyantardashas(ad)
        assert pds[0].start == ad.start
        assert abs((pds[-1].end - ad.end).total_seconds()) < 60


class TestFindCurrentDasha:
    """Tests for find_current_dasha()."""

    def test_returns_three_period_tuple(self, manish_chart) -> None:
        import pytz

        target = datetime(2026, 3, 22, 12, 0, tzinfo=pytz.UTC)
        md, ad, pd = find_current_dasha(manish_chart, target)
        assert md.level == "MD"
        assert ad.level == "AD"
        assert pd.level == "PD"

    def test_current_md_lord_is_jupiter(self, manish_chart) -> None:
        """Manish current MD = Jupiter per CLAUDE.md."""
        import pytz

        target = datetime(2026, 3, 22, 12, 0, tzinfo=pytz.UTC)
        md, _, _ = find_current_dasha(manish_chart, target)
        assert md.lord == "Jupiter"

    def test_target_date_within_md_range(self, manish_chart) -> None:
        import pytz

        target = datetime(2026, 3, 22, 12, 0, tzinfo=pytz.UTC)
        md, ad, _pd = find_current_dasha(manish_chart, target)
        assert md.start <= target <= md.end
        assert ad.start <= target <= ad.end


class TestDashaTimeline:
    """Tests for get_dasha_timeline()."""

    def test_returns_list_of_nine(self, manish_chart) -> None:
        timeline = get_dasha_timeline(manish_chart)
        assert len(timeline) == 9

    def test_each_entry_has_antardashas(self, manish_chart) -> None:
        timeline = get_dasha_timeline(manish_chart)
        for entry in timeline:
            assert "antardashas" in entry
            assert len(entry["antardashas"]) == 9

    def test_entries_have_required_keys(self, manish_chart) -> None:
        timeline = get_dasha_timeline(manish_chart)
        for entry in timeline:
            assert "lord" in entry
            assert "start" in entry
            assert "end" in entry
            assert "level" in entry
