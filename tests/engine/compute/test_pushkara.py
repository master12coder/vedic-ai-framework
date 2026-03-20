"""Tests for Pushkara Navamsha and Pushkara Bhaga computation."""

from __future__ import annotations

from daivai_engine.compute.pushkara import check_pushkara, get_pushkara_planets
from daivai_engine.models.pushkara import PushkaraResult


class TestPushkaraStructure:
    def test_returns_9_results_for_all_planets(self, manish_chart):
        """check_pushkara returns exactly 9 results (one per planet)."""
        results = check_pushkara(manish_chart)
        assert len(results) == 9

    def test_all_results_are_model_instances(self, manish_chart):
        """Every result is a PushkaraResult Pydantic model."""
        results = check_pushkara(manish_chart)
        for r in results:
            assert isinstance(r, PushkaraResult)

    def test_field_consistency(self, manish_chart):
        """Each result has valid field values."""
        results = check_pushkara(manish_chart)
        valid_types = {"bhaga", "navamsha", "both", "none"}
        for r in results:
            assert 0 <= r.sign_index <= 11
            assert 0 <= r.degree_in_sign < 30
            assert 0 <= r.pushkara_bhaga_degree <= 30
            assert r.pushkara_bhaga_distance >= 0
            assert r.pushkara_type in valid_types
            assert r.sign
            assert r.sign_en

    def test_pushkara_type_matches_flags(self, manish_chart):
        """pushkara_type is consistent with is_pushkara_navamsha and is_pushkara_bhaga."""
        results = check_pushkara(manish_chart)
        for r in results:
            if r.is_pushkara_navamsha and r.is_pushkara_bhaga:
                assert r.pushkara_type == "both"
            elif r.is_pushkara_bhaga:
                assert r.pushkara_type == "bhaga"
            elif r.is_pushkara_navamsha:
                assert r.pushkara_type == "navamsha"
            else:
                assert r.pushkara_type == "none"

    def test_strength_modifier_non_empty(self, manish_chart):
        """Every result has a non-empty strength_modifier string."""
        results = check_pushkara(manish_chart)
        for r in results:
            assert len(r.strength_modifier) > 0

    def test_bhaga_distance_correct(self, manish_chart):
        """pushkara_bhaga_distance equals abs(degree_in_sign - pushkara_bhaga_degree)."""
        results = check_pushkara(manish_chart)
        for r in results:
            expected = abs(r.degree_in_sign - r.pushkara_bhaga_degree)
            assert abs(r.pushkara_bhaga_distance - expected) < 1e-9


class TestPushkaraFiltered:
    def test_get_pushkara_planets_subset(self, manish_chart):
        """get_pushkara_planets returns only entries where type != 'none'."""
        all_results = check_pushkara(manish_chart)
        pushkara = get_pushkara_planets(manish_chart)
        assert len(pushkara) <= len(all_results)
        for r in pushkara:
            assert r.pushkara_type != "none"

    def test_no_none_type_in_pushkara_list(self, manish_chart):
        """No 'none' pushkara_type in the filtered list."""
        pushkara = get_pushkara_planets(manish_chart)
        for r in pushkara:
            assert r.pushkara_type in {"bhaga", "navamsha", "both"}


class TestPushkaraNavamshaRanges:
    def test_planet_in_last_navamsha_is_pushkara(self, manish_chart):
        """Any planet with degree 26.67-30 should be in Pushkara Navamsha (all elements)."""
        results = check_pushkara(manish_chart)
        for r in results:
            if r.degree_in_sign >= 26.6667:
                assert r.is_pushkara_navamsha, (
                    f"{r.planet} at {r.degree_in_sign:.2f}° in {r.sign_en} "
                    f"should be Pushkara Navamsha (pada 9 is Pushkara for all elements)"
                )

    def test_all_planets_checked(self, manish_chart):
        """All 9 planets appear in the result list."""
        results = check_pushkara(manish_chart)
        planets = [r.planet for r in results]
        expected = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        assert set(planets) == set(expected)
