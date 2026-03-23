"""Tests for Yoga activation timing — unit tests and edge cases.

Covers:
  - Currently active yoga detection (check_current_activation)
  - Next activation finding (find_next_activation)
  - Dual activation (both MD and AD are yoga planets)
  - Cancelled yoga timing (still computed, strength preserved)
  - Single planet yoga (Panch Mahapurush)
  - Sort key and significance ranking

Fixture:
  manish_chart: Mithuna lagna, Moon in Rohini Pada 2.
"""

from __future__ import annotations

from datetime import datetime

import pytest
import pytz

from daivai_engine.compute.dasha import (
    compute_mahadashas,
    find_current_dasha,
)
from daivai_engine.compute.yoga import detect_all_yogas
from daivai_engine.compute.yoga_timing import compute_yoga_timing
from daivai_engine.compute.yoga_timing_helpers import (
    check_current_activation,
    find_next_activation,
    yoga_sort_key,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.dasha import DashaPeriod
from daivai_engine.models.yoga import YogaResult
from daivai_engine.models.yoga_timing import (
    YogaActivationPeriod,
    YogaTimingResult,
)


_DATE = datetime(2026, 3, 22, 12, 0, 0, tzinfo=pytz.UTC)


class TestCurrentActivation:
    """Tests for check_current_activation logic."""

    def _md(self, lord: str, year: int = 2020) -> DashaPeriod:
        return DashaPeriod(
            level="MD",
            lord=lord,
            start=datetime(year, 1, 1, tzinfo=pytz.UTC),
            end=datetime(year + 5, 1, 1, tzinfo=pytz.UTC),
        )

    def _ad(self, lord: str, year: int = 2020) -> DashaPeriod:
        return DashaPeriod(
            level="AD",
            lord=lord,
            start=datetime(year, 1, 1, tzinfo=pytz.UTC),
            end=datetime(year + 5, 1, 1, tzinfo=pytz.UTC),
        )

    def test_dual_both_yoga_planets(self) -> None:
        now = datetime(2023, 6, 1, tzinfo=pytz.UTC)
        active, strength = check_current_activation(
            {"Jupiter", "Moon"},
            self._md("Jupiter"),
            self._ad("Moon"),
            now,
        )
        assert active is True and strength == "dual"

    def test_primary_only_md(self) -> None:
        now = datetime(2023, 6, 1, tzinfo=pytz.UTC)
        active, strength = check_current_activation(
            {"Jupiter", "Moon"},
            self._md("Jupiter"),
            self._ad("Venus"),
            now,
        )
        assert active is True and strength == "primary"

    def test_secondary_only_ad(self) -> None:
        now = datetime(2023, 6, 1, tzinfo=pytz.UTC)
        active, strength = check_current_activation(
            {"Jupiter", "Moon"},
            self._md("Venus"),
            self._ad("Moon"),
            now,
        )
        assert active is True and strength == "secondary"

    def test_inactive_no_yoga_planet(self) -> None:
        now = datetime(2023, 6, 1, tzinfo=pytz.UTC)
        active, strength = check_current_activation(
            {"Jupiter", "Moon"},
            self._md("Venus"),
            self._ad("Saturn"),
            now,
        )
        assert active is False and strength is None

    def test_inactive_outside_md_range(self) -> None:
        now = datetime(2030, 6, 1, tzinfo=pytz.UTC)
        active, _ = check_current_activation(
            {"Jupiter"},
            self._md("Jupiter"),
            self._ad("Moon"),
            now,
        )
        assert active is False

    def test_same_lord_is_primary_not_dual(self) -> None:
        now = datetime(2023, 6, 1, tzinfo=pytz.UTC)
        active, strength = check_current_activation(
            {"Jupiter"},
            self._md("Jupiter"),
            self._ad("Jupiter"),
            now,
        )
        assert active is True and strength == "primary"


class TestNextActivation:
    """Tests for find_next_activation logic."""

    def _ap(self, strength: str, year: int, month: int = 1) -> YogaActivationPeriod:
        level = {"primary": "MD", "secondary": "AD", "dual": "MD-AD"}[strength]
        end_month = month + 6 if month <= 6 else 12
        return YogaActivationPeriod(
            dasha_level=level,
            lord="Jupiter",
            parent_lord="Saturn" if strength != "primary" else None,
            start=datetime(year, month, 1, tzinfo=pytz.UTC),
            end=datetime(year, end_month, 1, tzinfo=pytz.UTC),
            activation_strength=strength,
        )

    def test_nearest_future(self) -> None:
        now = datetime(2025, 6, 1, tzinfo=pytz.UTC)
        result = find_next_activation(
            [self._ap("primary", 2020), self._ap("primary", 2026), self._ap("primary", 2030)],
            now,
        )
        assert result is not None and result.start.year == 2026

    def test_none_when_no_future(self) -> None:
        now = datetime(2040, 6, 1, tzinfo=pytz.UTC)
        result = find_next_activation(
            [self._ap("primary", 2020), self._ap("primary", 2030)],
            now,
        )
        assert result is None

    def test_prefers_dual(self) -> None:
        now = datetime(2025, 6, 1, tzinfo=pytz.UTC)
        result = find_next_activation(
            [self._ap("primary", 2026, 1), self._ap("dual", 2026, 3)],
            now,
        )
        assert result is not None and result.activation_strength == "dual"

    def test_prefers_primary_over_secondary(self) -> None:
        now = datetime(2025, 6, 1, tzinfo=pytz.UTC)
        result = find_next_activation(
            [self._ap("secondary", 2026, 1), self._ap("primary", 2026, 3)],
            now,
        )
        assert result is not None and result.activation_strength == "primary"


class TestSingleYogaTiming:
    """Tests for compute_yoga_timing() with individual yogas."""

    @pytest.fixture
    def mds(self, manish_chart: ChartData) -> list[DashaPeriod]:
        return compute_mahadashas(manish_chart)

    @pytest.fixture
    def current(self, manish_chart: ChartData) -> tuple[DashaPeriod, DashaPeriod, DashaPeriod]:
        return find_current_dasha(manish_chart, _DATE)

    def test_single_planet_yoga(
        self,
        manish_chart: ChartData,
        mds: list[DashaPeriod],
        current: tuple[DashaPeriod, DashaPeriod, DashaPeriod],
    ) -> None:
        yoga = YogaResult(
            name="Bhadra",
            name_hindi="bhdr",
            is_present=True,
            planets_involved=["Mercury"],
            houses_involved=[1],
            description="Mercury in own/exalted in kendra",
            effect="benefic",
        )
        md, ad, _ = current
        result = compute_yoga_timing(manish_chart, yoga, mds, md, ad, _DATE)
        assert len(result.activation_periods) > 0
        for ap in result.activation_periods:
            assert "Mercury" in ap.lord

    def test_two_planet_yoga_has_dual(
        self,
        manish_chart: ChartData,
        mds: list[DashaPeriod],
        current: tuple[DashaPeriod, DashaPeriod, DashaPeriod],
    ) -> None:
        yoga = YogaResult(
            name="TestDual",
            name_hindi="tst",
            is_present=True,
            planets_involved=["Jupiter", "Moon"],
            houses_involved=[1, 7],
            description="Test two-planet yoga",
            effect="benefic",
        )
        md, ad, _ = current
        result = compute_yoga_timing(manish_chart, yoga, mds, md, ad, _DATE)
        dual = [ap for ap in result.activation_periods if ap.activation_strength == "dual"]
        assert len(dual) > 0

    def test_present_yoga_positive_years(
        self,
        manish_chart: ChartData,
        mds: list[DashaPeriod],
        current: tuple[DashaPeriod, DashaPeriod, DashaPeriod],
    ) -> None:
        yogas = detect_all_yogas(manish_chart)
        present = [y for y in yogas if y.is_present]
        if present:
            md, ad, _ = current
            result = compute_yoga_timing(manish_chart, present[0], mds, md, ad, _DATE)
            assert result.total_activation_years > 0

    def test_cancelled_yoga_preserved(
        self,
        manish_chart: ChartData,
        mds: list[DashaPeriod],
        current: tuple[DashaPeriod, DashaPeriod, DashaPeriod],
    ) -> None:
        yoga = YogaResult(
            name="Cancelled",
            name_hindi="cncl",
            is_present=True,
            planets_involved=["Saturn", "Mars"],
            houses_involved=[8, 6],
            description="Cancelled test yoga",
            effect="malefic",
            strength="cancelled",
        )
        md, ad, _ = current
        result = compute_yoga_timing(manish_chart, yoga, mds, md, ad, _DATE)
        assert result.strength == "cancelled"
        assert len(result.activation_periods) > 0


class TestYogaSortKey:
    """Tests for yoga_sort_key ranking."""

    def _make(
        self,
        active: bool = False,
        effect: str = "benefic",
        years: float = 10.0,
    ) -> YogaTimingResult:
        return YogaTimingResult(
            yoga_name="Test",
            planets_involved=["Jupiter"],
            houses_involved=[1],
            effect=effect,
            strength="full",
            activation_periods=[],
            total_activation_years=years,
            is_currently_active=active,
            current_activation_strength="primary" if active else None,
            next_activation=None,
            summary="test",
        )

    def test_active_over_inactive(self) -> None:
        assert yoga_sort_key(self._make(active=True)) > yoga_sort_key(self._make(active=False))

    def test_benefic_over_malefic(self) -> None:
        assert yoga_sort_key(self._make(effect="benefic")) > yoga_sort_key(
            self._make(effect="malefic")
        )

    def test_more_years_higher(self) -> None:
        assert yoga_sort_key(self._make(years=20.0)) > yoga_sort_key(self._make(years=5.0))

    def test_active_benefic_highest(self) -> None:
        best = self._make(active=True, effect="benefic", years=20.0)
        worst = self._make(active=False, effect="malefic", years=5.0)
        assert yoga_sort_key(best) > yoga_sort_key(worst)
