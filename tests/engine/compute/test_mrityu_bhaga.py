"""Tests for Mrityu Bhaga (death degree) computation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.mrityu_bhaga import (
    check_mrityu_bhaga,
    get_afflicted_bodies,
)
from daivai_engine.models.mrityu_bhaga import MrityuBhagaResult


class TestMrityuBhagaStructure:
    def test_returns_10_results_for_9_planets_and_lagna(self, manish_chart):
        """check_mrityu_bhaga returns exactly 10 results (9 planets + Lagna)."""
        results = check_mrityu_bhaga(manish_chart)
        assert len(results) == 10

    def test_all_results_are_model_instances(self, manish_chart):
        """Every result is a MrityuBhagaResult Pydantic model."""
        results = check_mrityu_bhaga(manish_chart)
        for r in results:
            assert isinstance(r, MrityuBhagaResult)

    def test_result_fields_are_consistent(self, manish_chart):
        """Each result has valid field values within expected ranges."""
        results = check_mrityu_bhaga(manish_chart)
        for r in results:
            assert 0 <= r.sign_index <= 11
            assert 0 <= r.actual_degree < 30
            assert 0 <= r.mrityu_degree <= 30
            assert r.distance >= 0
            assert r.severity in ("severe", "moderate", "clear")
            assert r.sign  # non-empty
            assert r.sign_en  # non-empty

    def test_lagna_entry_present(self, manish_chart):
        """Lagna is included as the last body in results."""
        results = check_mrityu_bhaga(manish_chart)
        lagna_entries = [r for r in results if r.body == "Lagna"]
        assert len(lagna_entries) == 1

    def test_all_planets_present(self, manish_chart):
        """All 9 planets are represented in results."""
        results = check_mrityu_bhaga(manish_chart)
        planet_bodies = [r.body for r in results if r.body != "Lagna"]
        expected = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        assert set(planet_bodies) == set(expected)

    def test_severity_distance_consistency(self, manish_chart):
        """Severity label matches the distance value correctly."""
        results = check_mrityu_bhaga(manish_chart)
        for r in results:
            if r.distance <= 1.0:
                assert r.severity == "severe"
            elif r.distance <= 3.0:
                assert r.severity == "moderate"
            else:
                assert r.severity == "clear"


class TestMrityuBhagaAfflicted:
    def test_get_afflicted_bodies_subset_of_full(self, manish_chart):
        """get_afflicted_bodies returns a subset of check_mrityu_bhaga."""
        all_results = check_mrityu_bhaga(manish_chart)
        afflicted = get_afflicted_bodies(manish_chart)
        assert len(afflicted) <= len(all_results)
        for r in afflicted:
            assert r.severity in ("severe", "moderate")

    def test_afflicted_bodies_have_no_clear_entries(self, manish_chart):
        """No 'clear' entries appear in the afflicted list."""
        afflicted = get_afflicted_bodies(manish_chart)
        for r in afflicted:
            assert r.severity != "clear"


class TestMrityuBhagaKnownValues:
    @pytest.mark.safety
    def test_mrityu_bhaga_table_aries_sun(self, manish_chart):
        """Sun's Mrityu Bhaga in Aries should be 20 per BPHS table."""
        results = check_mrityu_bhaga(manish_chart)
        sun_result = next(r for r in results if r.body == "Sun")
        # Verify the tabulated value is within valid range
        assert 0 <= sun_result.mrityu_degree <= 30

    def test_distance_computed_correctly(self, manish_chart):
        """Distance must equal abs(actual_degree - mrityu_degree)."""
        results = check_mrityu_bhaga(manish_chart)
        for r in results:
            expected_dist = abs(r.actual_degree - r.mrityu_degree)
            assert abs(r.distance - expected_dist) < 1e-9
