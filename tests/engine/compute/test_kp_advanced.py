"""Tests for upgraded KP — house groupings for events."""

from __future__ import annotations

from daivai_engine.compute.kp import (
    KP_HOUSE_GROUPS,
    check_kp_event_promise,
    get_significators,
)
from daivai_engine.models.chart import ChartData


class TestKPHouseGroups:
    def test_has_eight_event_types(self) -> None:
        assert len(KP_HOUSE_GROUPS) >= 8

    def test_all_event_types_have_required_keys(self) -> None:
        for event_type, group in KP_HOUSE_GROUPS.items():
            assert "positive_houses" in group, f"{event_type}: missing positive_houses"
            assert "negative_houses" in group, f"{event_type}: missing negative_houses"
            assert "primary_cusp" in group, f"{event_type}: missing primary_cusp"
            assert "description" in group, f"{event_type}: missing description"

    def test_houses_in_valid_range(self) -> None:
        for event_type, group in KP_HOUSE_GROUPS.items():
            for h in group["positive_houses"]:  # type: ignore[union-attr]
                assert 1 <= h <= 12, f"{event_type}: positive house {h} out of range"
            for h in group["negative_houses"]:  # type: ignore[union-attr]
                assert 1 <= h <= 12, f"{event_type}: negative house {h} out of range"

    def test_marriage_positive_houses(self) -> None:
        assert 7 in KP_HOUSE_GROUPS["marriage"]["positive_houses"]  # type: ignore[operator]
        assert 11 in KP_HOUSE_GROUPS["marriage"]["positive_houses"]  # type: ignore[operator]

    def test_career_primary_cusp_is_10(self) -> None:
        assert KP_HOUSE_GROUPS["career"]["primary_cusp"] == 10


class TestCheckKPEventPromise:
    def test_valid_event_returns_dict(self, manish_chart: ChartData) -> None:
        result = check_kp_event_promise(manish_chart, "marriage")
        assert isinstance(result, dict)
        assert "promise_level" in result

    def test_promise_level_is_valid(self, manish_chart: ChartData) -> None:
        for event in ("marriage", "career", "health_recovery"):
            result = check_kp_event_promise(manish_chart, event)
            assert result["promise_level"] in ("strong", "moderate", "weak", "denied")

    def test_unknown_event_returns_error(self, manish_chart: ChartData) -> None:
        result = check_kp_event_promise(manish_chart, "flying_to_moon")
        assert "error" in result
        assert result["promise_level"] == "unknown"

    def test_result_has_significator_houses(self, manish_chart: ChartData) -> None:
        result = check_kp_event_promise(manish_chart, "career")
        assert "significator_houses" in result
        for h in result["significator_houses"]:
            assert 1 <= h <= 12

    def test_cusp_lord_is_valid_planet(self, manish_chart: ChartData) -> None:
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        for event in KP_HOUSE_GROUPS:
            result = check_kp_event_promise(manish_chart, event)
            if "cusp_lord" in result:
                assert result["cusp_lord"] in valid

    def test_sub_lord_is_valid_planet(self, manish_chart: ChartData) -> None:
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = check_kp_event_promise(manish_chart, "marriage")
        if "sub_lord" in result:
            assert result["sub_lord"] in valid


class TestGetSignificatorsUpgraded:
    def test_includes_sub_lord_houses(self, manish_chart: ChartData) -> None:
        sigs = get_significators(manish_chart, "Jupiter")
        assert "sub_lord_houses" in sigs
        assert "sub_lord" in sigs

    def test_sub_lord_is_valid_planet(self, manish_chart: ChartData) -> None:
        valid = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        sigs = get_significators(manish_chart, "Venus")
        assert sigs["sub_lord"] in valid

    def test_all_significator_houses_in_range(self, manish_chart: ChartData) -> None:
        for planet in ("Sun", "Moon", "Mars", "Jupiter", "Venus"):
            sigs = get_significators(manish_chart, planet)
            all_houses = (
                sigs["occupies"] + sigs["owns"] + sigs["star_lord_houses"] + sigs["sub_lord_houses"]
            )
            for h in all_houses:
                assert 1 <= h <= 12, f"{planet}: house {h} out of range"
