"""Tests for transit computation — compute_transits()."""

from __future__ import annotations

from datetime import datetime

import pytz

from daivai_engine.compute.transit import compute_transits
from daivai_engine.constants import NAKSHATRAS, PLANETS, SIGNS
from daivai_engine.models.transit import TransitData


_REFERENCE_DATE = datetime(2026, 3, 22, 12, 0, tzinfo=pytz.UTC)


class TestTransitComputation:
    """Tests for compute_transits() output structure."""

    def test_returns_transit_data(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        assert isinstance(result, TransitData)

    def test_all_nine_planets_present(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        transit_names = [t.name for t in result.transits]
        for p in PLANETS:
            assert p in transit_names, f"{p} missing from transits"

    def test_all_longitudes_in_range(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        for tp in result.transits:
            assert 0.0 <= tp.longitude < 360.0, f"{tp.name} lon={tp.longitude}"

    def test_all_sign_indices_in_range(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        for tp in result.transits:
            assert 0 <= tp.sign_index <= 11, f"{tp.name} sign={tp.sign_index}"

    def test_signs_match_sign_indices(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        for tp in result.transits:
            assert tp.sign == SIGNS[tp.sign_index], f"{tp.name}: sign mismatch"

    def test_nakshatras_are_valid(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        for tp in result.transits:
            assert tp.nakshatra in NAKSHATRAS, f"{tp.name}: invalid nakshatra"

    def test_natal_house_activated_in_range(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        for tp in result.transits:
            assert 1 <= tp.natal_house_activated <= 12

    def test_ketu_opposite_rahu(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        rahu_t = next(t for t in result.transits if t.name == "Rahu")
        ketu_t = next(t for t in result.transits if t.name == "Ketu")
        diff = abs(rahu_t.longitude - ketu_t.longitude)
        if diff > 180:
            diff = 360 - diff
        assert abs(diff - 180.0) < 0.01

    def test_ketu_always_retrograde(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        ketu_t = next(t for t in result.transits if t.name == "Ketu")
        assert ketu_t.is_retrograde


class TestMajorTransits:
    """Tests for major transit annotations."""

    def test_major_transits_is_list(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        assert isinstance(result.major_transits, list)

    def test_at_least_one_major_transit(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        # Jupiter transit is always added
        assert len(result.major_transits) >= 1

    def test_jupiter_transit_in_major(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        jupiter_mention = any("Jupiter" in m for m in result.major_transits)
        assert jupiter_mention

    def test_rahu_ketu_axis_in_major(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        rahu_mention = any("Rahu" in m for m in result.major_transits)
        assert rahu_mention


class TestTransitMetadata:
    """Tests for transit metadata fields."""

    def test_target_date_formatted(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        assert result.target_date == "22/03/2026"

    def test_natal_chart_name_matches(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        assert result.natal_chart_name == manish_chart.name

    def test_natal_lagna_sign_matches(self, manish_chart) -> None:
        result = compute_transits(manish_chart, _REFERENCE_DATE)
        assert result.natal_lagna_sign == manish_chart.lagna_sign


class TestTransitWithoutDate:
    """Tests for compute_transits() with default (now) date."""

    def test_default_date_returns_valid_result(self, manish_chart) -> None:
        result = compute_transits(manish_chart)
        assert isinstance(result, TransitData)
        assert len(result.transits) == 9
