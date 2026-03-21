"""Tests for Rasi Tulya Navamsha (RTN) computation."""

from __future__ import annotations

from daivai_engine.compute.rasi_tulya_navamsha import compute_rtn
from daivai_engine.models.chart import ChartData
from daivai_engine.models.rasi_tulya import RTNPlanet, RTNResult


class TestRTNStructure:
    def test_returns_nine_planets(self, manish_chart: ChartData) -> None:
        """compute_rtn returns exactly 9 results — one per planet."""
        result = compute_rtn(manish_chart)
        assert len(result.planets) == 9

    def test_result_is_rtn_model(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        assert isinstance(result, RTNResult)

    def test_all_planets_are_rtn_planet(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        for p in result.planets:
            assert isinstance(p, RTNPlanet)

    def test_all_relationships_valid(self, manish_chart: ChartData) -> None:
        """Every planet has one of the 5 valid RTN relationships."""
        result = compute_rtn(manish_chart)
        valid = {"vargottama", "kendra", "trikona", "dusthana", "neutral"}
        for p in result.planets:
            assert p.relationship in valid, f"{p.planet}: '{p.relationship}' not in {valid}"

    def test_sign_distance_range(self, manish_chart: ChartData) -> None:
        """sign_distance must be in 0-11 (forward distance)."""
        result = compute_rtn(manish_chart)
        for p in result.planets:
            assert 0 <= p.sign_distance <= 11, (
                f"{p.planet}: sign_distance={p.sign_distance}"
            )

    def test_sign_indices_valid(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        for p in result.planets:
            assert 0 <= p.d1_sign_index <= 11
            assert 0 <= p.d9_sign_index <= 11


class TestRTNRelationshipLogic:
    def test_vargottama_means_same_sign(self, manish_chart: ChartData) -> None:
        """Vargottama planets must have d1_sign_index == d9_sign_index."""
        result = compute_rtn(manish_chart)
        for p in result.planets:
            if p.relationship == "vargottama":
                assert p.d1_sign_index == p.d9_sign_index, (
                    f"{p.planet}: vargottama but D1={p.d1_sign_index} != D9={p.d9_sign_index}"
                )

    def test_vargottama_in_summary_list(self, manish_chart: ChartData) -> None:
        """RTNResult.vargottama_planets matches planets with vargottama relationship."""
        result = compute_rtn(manish_chart)
        expected = [p.planet for p in result.planets if p.relationship == "vargottama"]
        assert sorted(result.vargottama_planets) == sorted(expected)

    def test_kendra_distance_is_3_6_or_9(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        for p in result.planets:
            if p.relationship == "kendra":
                assert p.sign_distance in (3, 6, 9)

    def test_trikona_distance_is_4_or_8(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        for p in result.planets:
            if p.relationship == "trikona":
                assert p.sign_distance in (4, 8)

    def test_dusthana_distance_is_5_7_or_11(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        for p in result.planets:
            if p.relationship == "dusthana":
                assert p.sign_distance in (5, 7, 11)


class TestRTNPushkara:
    def test_pushkara_type_valid(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        valid_types = {"none", "navamsha", "bhaga", "both"}
        for p in result.planets:
            assert p.pushkara_type in valid_types

    def test_pushkara_planets_list_consistent(self, manish_chart: ChartData) -> None:
        """RTNResult.pushkara_planets == planets with pushkara_type != 'none'."""
        result = compute_rtn(manish_chart)
        expected = [p.planet for p in result.planets if p.pushkara_type != "none"]
        assert sorted(result.pushkara_planets) == sorted(expected)

    def test_timing_note_not_empty(self, manish_chart: ChartData) -> None:
        result = compute_rtn(manish_chart)
        for p in result.planets:
            assert p.timing_note.strip(), f"Empty timing_note for {p.planet}"
