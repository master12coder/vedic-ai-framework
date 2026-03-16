"""Tests for the enhanced six-fold Shadbala computation."""

from __future__ import annotations

import pytest

from jyotish.compute.strength import (
    compute_shadbala,
    compute_planet_strengths,
    get_strongest_planet,
    get_weakest_planet,
    NAISARGIKA,
    REQUIRED_SHADBALA,
    SHADBALA_PLANETS,
)
from jyotish.domain.models.strength import ShadbalaResult, PlanetStrength


class TestShadbalaComputation:
    """Core Shadbala computation tests."""

    def test_returns_seven_planets(self, manish_chart):
        results = compute_shadbala(manish_chart)
        assert len(results) == 7
        names = {r.planet for r in results}
        assert names == set(SHADBALA_PLANETS)

    def test_all_six_components_present(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert isinstance(r.sthana_bala, float)
            assert isinstance(r.dig_bala, float)
            assert isinstance(r.kala_bala, float)
            assert isinstance(r.cheshta_bala, float)
            assert isinstance(r.naisargika_bala, float)
            assert isinstance(r.drik_bala, float)

    def test_ratio_positive(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.ratio > 0, f"{r.planet} has non-positive ratio: {r.ratio}"

    def test_total_equals_sum_of_components(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            expected = round(
                r.sthana_bala + r.dig_bala + r.kala_bala
                + r.cheshta_bala + r.naisargika_bala + r.drik_bala, 2
            )
            assert abs(r.total - expected) < 0.1, (
                f"{r.planet}: total={r.total}, sum={expected}"
            )

    def test_naisargika_values_match_fixed_table(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            expected = NAISARGIKA[r.planet]
            assert r.naisargika_bala == expected, (
                f"{r.planet}: naisargika={r.naisargika_bala}, expected={expected}"
            )

    def test_ratio_is_total_over_required(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            expected_ratio = round(r.total / REQUIRED_SHADBALA[r.planet], 3)
            assert abs(r.ratio - expected_ratio) < 0.01, (
                f"{r.planet}: ratio={r.ratio}, expected={expected_ratio}"
            )

    def test_is_strong_matches_ratio(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.is_strong == (r.ratio >= 1.0), (
                f"{r.planet}: is_strong={r.is_strong}, ratio={r.ratio}"
            )

    def test_ranks_unique_and_sequential(self, manish_chart):
        results = compute_shadbala(manish_chart)
        ranks = sorted(r.rank for r in results)
        assert ranks == list(range(1, 8))

    def test_rank_1_has_highest_total(self, manish_chart):
        results = compute_shadbala(manish_chart)
        by_rank = {r.rank: r for r in results}
        assert by_rank[1].total >= by_rank[7].total

    def test_sthana_bala_positive(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.sthana_bala >= 0, f"{r.planet} sthana_bala negative"

    def test_dig_bala_range(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert 0.0 <= r.dig_bala <= 60.0, (
                f"{r.planet} dig_bala={r.dig_bala} out of range"
            )

    def test_cheshta_bala_sun_moon(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            if r.planet in ("Sun", "Moon"):
                assert r.cheshta_bala == 30.0

    def test_required_values_match(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.required == REQUIRED_SHADBALA[r.planet]


class TestBackwardCompatibility:
    """Ensure compute_planet_strengths still works for existing callers."""

    def test_returns_nine_planets(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        assert len(strengths) == 9
        names = {s.planet for s in strengths}
        assert "Rahu" in names
        assert "Ketu" in names

    def test_has_total_relative(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        for s in strengths:
            assert hasattr(s, "total_relative")
            assert 0.0 <= s.total_relative <= 1.0

    def test_has_rank(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        ranks = sorted(s.rank for s in strengths)
        assert ranks == list(range(1, 10))

    def test_has_is_strong(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        for s in strengths:
            assert isinstance(s.is_strong, bool)

    def test_strongest_planet_returns_string(self, manish_chart):
        result = get_strongest_planet(manish_chart)
        assert isinstance(result, str)
        assert result in set(SHADBALA_PLANETS) | {"Rahu", "Ketu"}

    def test_weakest_planet_returns_string(self, manish_chart):
        result = get_weakest_planet(manish_chart)
        assert isinstance(result, str)
        assert result in set(SHADBALA_PLANETS) | {"Rahu", "Ketu"}
