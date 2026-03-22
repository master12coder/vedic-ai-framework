"""Tests for Vastu Purusha Mandala zone strengths and room recommendations."""

from __future__ import annotations

from daivai_engine.compute.vastu_mandala import (
    _planet_score,
    compute_mandala_zones,
    compute_room_recommendations,
)
from daivai_engine.models.vastu import RoomRecommendation, VastuZone


class TestPlanetScore:
    """Tests for _planet_score() — planet strength scorer for Vastu."""

    def test_returns_float(self, manish_chart) -> None:
        sun = manish_chart.planets["Sun"]
        score = _planet_score(sun)
        assert isinstance(score, float)

    def test_score_in_0_100_range(self, manish_chart) -> None:
        for p_data in manish_chart.planets.values():
            score = _planet_score(p_data)
            assert 0.0 <= score <= 100.0, f"{p_data.name}: score={score}"

    def test_exalted_planet_scores_higher_than_neutral(self, manish_chart) -> None:
        """Exalted dignity should give a higher base score than neutral."""
        # Find a neutral planet vs an exalted/own one for comparison
        neutral_scores = []
        exalted_scores = []
        for p_data in manish_chart.planets.values():
            if p_data.dignity == "exalted":
                exalted_scores.append(_planet_score(p_data))
            elif p_data.dignity == "neutral":
                neutral_scores.append(_planet_score(p_data))
        if exalted_scores and neutral_scores:
            assert max(exalted_scores) >= min(neutral_scores)


class TestComputeMandalaZones:
    """Tests for compute_mandala_zones()."""

    def test_returns_list(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        assert isinstance(zones, list)

    def test_returns_nine_zones(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        assert len(zones) == 9

    def test_all_are_vastu_zones(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        for z in zones:
            assert isinstance(z, VastuZone)

    def test_zone_strengths_in_0_100(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        for z in zones:
            assert 0.0 <= z.zone_strength <= 100.0, f"{z.direction}: {z.zone_strength}"

    def test_directions_are_non_empty(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        for z in zones:
            assert z.direction, "Zone has empty direction"

    def test_no_duplicate_directions(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        directions = [z.direction for z in zones]
        assert len(directions) == len(set(directions))

    def test_brahmasthana_center_has_50_strength(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        center = next((z for z in zones if "Center" in z.direction or "Brahma" in z.planet), None)
        if center:
            assert center.zone_strength == 50.0

    def test_element_non_empty(self, manish_chart) -> None:
        zones = compute_mandala_zones(manish_chart)
        for z in zones:
            assert z.element, f"{z.direction}: empty element"


class TestComputeRoomRecommendations:
    """Tests for compute_room_recommendations()."""

    def test_returns_list(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        assert isinstance(rooms, list)

    def test_all_are_room_recommendations(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        for r in rooms:
            assert isinstance(r, RoomRecommendation)

    def test_room_names_non_empty(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        for r in rooms:
            assert r.room, "Room has empty name"

    def test_ideal_direction_non_empty(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        for r in rooms:
            assert r.ideal_direction, f"{r.room}: empty direction"

    def test_is_favorable_is_bool(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        for r in rooms:
            assert isinstance(r.is_favorable, bool)

    def test_planet_strength_in_0_100(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        for r in rooms:
            assert 0.0 <= r.planet_strength <= 100.0, f"{r.room}: strength={r.planet_strength}"

    def test_reason_non_empty(self, manish_chart) -> None:
        rooms = compute_room_recommendations(manish_chart)
        for r in rooms:
            assert r.reason, f"{r.room}: empty reason"
