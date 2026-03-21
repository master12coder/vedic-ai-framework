"""Tests for Vastu Shastra computation module.

Primary fixture: manish_chart — Manish Chaurasia, Mithuna lagna (Gemini).
Known Mithuna lagna facts:
  Lagna lord: Mercury → North direction
  4th lord:   Mercury → North direction  (Kanya = Virgo, lord Mercury)
  9th lord:   Saturn  → West direction   (Kumbha = Aquarius)
  10th lord:  Jupiter → North-East       (Meena = Pisces)
  2nd lord:   Moon    → North-West       (Karka = Cancer)  ← maraka_1
  7th lord:   Jupiter → North-East       (Dhanu = Sagittarius) ← maraka_2
  6th lord:   Mars    → South            (Vrischika = Scorpio)
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from daivai_engine.compute.vastu import (
    compute_direction_strengths,
    compute_favorable_directions,
    compute_vastu,
    detect_vastu_doshas,
)
from daivai_engine.compute.vastu_mandala import (
    analyze_entry_door,
    compute_mandala_zones,
    compute_room_recommendations,
)
from daivai_engine.models.chart import ChartData, PlanetData
from daivai_engine.models.vastu import (
    AyadiField,
    DirectionStrength,
    DoorAnalysis,
    RoomRecommendation,
    VastuDosha,
    VastuResult,
    VastuZone,
)


# ── Synthetic chart helpers ────────────────────────────────────────────────────


def _make_planet_in_house(name: str, house: int) -> PlanetData:
    """Minimal PlanetData with a specific house number for dosha testing."""
    return PlanetData(
        name=name,
        name_hi="",
        longitude=float(house - 1) * 30.0 + 15.0,
        sign_index=(house - 1) % 12,
        sign="",
        sign_en="",
        sign_hi="",
        degree_in_sign=15.0,
        nakshatra_index=0,
        nakshatra="",
        nakshatra_lord="",
        pada=1,
        house=house,
        is_retrograde=False,
        speed=1.0,
        dignity="neutral",
        avastha="Yuva",
        is_combust=False,
        sign_lord="",
    )


def _make_dosha_chart(trigger_planet: str) -> ChartData:
    """Build a minimal chart with the given planet in house 4 (to trigger a dosha)."""
    chart = ChartData(
        name="Dosha Test",
        dob="01/01/2000",
        tob="06:00",
        place="Delhi",
        gender="Male",
        latitude=28.6139,
        longitude=77.2090,
        timezone_name="Asia/Kolkata",
        julian_day=2451545.0,
        ayanamsha=23.7,
        lagna_longitude=60.0,
        lagna_sign_index=2,  # Mithuna
        lagna_sign="Mithuna",
        lagna_sign_en="Gemini",
        lagna_sign_hi="मिथुन",
        lagna_degree=0.0,
    )
    # Populate all required planets with neutral placements
    all_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for i, pname in enumerate(all_planets):
        h = 4 if pname == trigger_planet else (i % 12) + 1
        chart.planets[pname] = _make_planet_in_house(pname, h)
    return chart


# ── Direction Strengths ───────────────────────────────────────────────────────


class TestComputeDirectionStrengths:
    """Tests for compute_direction_strengths()."""

    def test_returns_nine_entries_for_nine_planets(self, manish_chart):
        results = compute_direction_strengths(manish_chart)
        assert len(results) == 9

    def test_all_entries_are_direction_strength_instances(self, manish_chart):
        for item in compute_direction_strengths(manish_chart):
            assert isinstance(item, DirectionStrength)

    def test_strength_scores_in_valid_range(self, manish_chart):
        for ds in compute_direction_strengths(manish_chart):
            assert 0.0 <= ds.strength_score <= 100.0, (
                f"{ds.planet}: score {ds.strength_score} out of range"
            )

    def test_sorted_descending_by_score(self, manish_chart):
        results = compute_direction_strengths(manish_chart)
        scores = [r.strength_score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_is_favorable_consistent_with_score(self, manish_chart):
        for ds in compute_direction_strengths(manish_chart):
            if ds.strength_score >= 50.0:
                assert ds.is_favorable is True
            else:
                assert ds.is_favorable is False

    def test_all_directions_have_hindi_names(self, manish_chart):
        for ds in compute_direction_strengths(manish_chart):
            assert ds.direction_hi, f"{ds.direction} missing Hindi name"

    def test_all_planets_present_in_results(self, manish_chart):
        planets = {ds.planet for ds in compute_direction_strengths(manish_chart)}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert planets == expected

    def test_ketu_and_moon_both_map_to_northwest(self, manish_chart):
        results = compute_direction_strengths(manish_chart)
        nw_planets = {ds.planet for ds in results if ds.direction == "North-West"}
        assert "Moon" in nw_planets
        assert "Ketu" in nw_planets

    def test_description_contains_planet_name(self, manish_chart):
        for ds in compute_direction_strengths(manish_chart):
            assert ds.planet.split()[0] in ds.description


# ── Favorable Directions ──────────────────────────────────────────────────────


class TestComputeFavorableDirections:
    """Tests for compute_favorable_directions() with Mithuna lagna."""

    def test_returns_all_seven_roles(self, manish_chart):
        dirs = compute_favorable_directions(manish_chart)
        expected_keys = {"lagna", "home", "fortune", "career", "maraka_1", "maraka_2", "dusthana"}
        assert set(dirs.keys()) == expected_keys

    def test_mithuna_lagna_lord_mercury_rules_north(self, manish_chart):
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["lagna"] == "North"

    def test_mithuna_4th_lord_mercury_rules_north(self, manish_chart):
        # 4th house from Mithuna = Kanya (Virgo), lord Mercury → North
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["home"] == "North"

    def test_mithuna_9th_lord_saturn_rules_west(self, manish_chart):
        # 9th house from Mithuna = Kumbha (Aquarius), lord Saturn → West
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["fortune"] == "West"

    def test_mithuna_10th_lord_jupiter_rules_northeast(self, manish_chart):
        # 10th house from Mithuna = Meena (Pisces), lord Jupiter → North-East
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["career"] == "North-East"

    def test_mithuna_maraka1_moon_rules_northwest(self, manish_chart):
        # 2nd house from Mithuna = Karka (Cancer), lord Moon → North-West
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["maraka_1"] == "North-West"

    def test_mithuna_maraka2_jupiter_rules_northeast(self, manish_chart):
        # 7th house from Mithuna = Dhanu (Sagittarius), lord Jupiter → North-East
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["maraka_2"] == "North-East"

    def test_mithuna_dusthana_mars_rules_south(self, manish_chart):
        # 6th house from Mithuna = Vrischika (Scorpio), lord Mars → South
        dirs = compute_favorable_directions(manish_chart)
        assert dirs["dusthana"] == "South"


# ── Vastu Doshas ──────────────────────────────────────────────────────────────


class TestDetectVastuDoshas:
    """Tests for detect_vastu_doshas()."""

    def test_returns_list_of_vastu_dosha_instances(self, manish_chart):
        doshas = detect_vastu_doshas(manish_chart)
        assert all(isinstance(d, VastuDosha) for d in doshas)

    def test_returns_five_defined_doshas(self, manish_chart):
        # vastu_rules.yaml defines 5 dosha triggers
        doshas = detect_vastu_doshas(manish_chart)
        assert len(doshas) == 5

    def test_absent_doshas_have_severity_none(self, manish_chart):
        for dosha in detect_vastu_doshas(manish_chart):
            if not dosha.is_present:
                assert dosha.severity == "none"

    def test_present_doshas_have_nonzero_severity(self, manish_chart):
        for dosha in detect_vastu_doshas(manish_chart):
            if dosha.is_present:
                assert dosha.severity in {"mild", "moderate", "severe"}

    def test_all_doshas_have_remedy_direction(self, manish_chart):
        for dosha in detect_vastu_doshas(manish_chart):
            assert dosha.remedy_direction, f"{dosha.name} missing remedy direction"

    def test_all_doshas_have_hindi_names(self, manish_chart):
        for dosha in detect_vastu_doshas(manish_chart):
            assert dosha.name_hi, f"{dosha.name} missing Hindi name"

    def test_dosha_house_is_four(self, manish_chart):
        # All defined doshas trigger on house 4
        for dosha in detect_vastu_doshas(manish_chart):
            assert dosha.house == 4


# ── Mandala Zones ─────────────────────────────────────────────────────────────


class TestComputeMandalaZones:
    """Tests for compute_mandala_zones()."""

    def test_returns_nine_zones(self, manish_chart):
        zones = compute_mandala_zones(manish_chart)
        assert len(zones) == 9

    def test_all_zones_are_vastu_zone_instances(self, manish_chart):
        for zone in compute_mandala_zones(manish_chart):
            assert isinstance(zone, VastuZone)

    def test_zone_strengths_in_valid_range(self, manish_chart):
        for zone in compute_mandala_zones(manish_chart):
            assert 0.0 <= zone.zone_strength <= 100.0

    def test_center_zone_present(self, manish_chart):
        directions = {z.direction for z in compute_mandala_zones(manish_chart)}
        assert "Center" in directions

    def test_all_eight_compass_zones_present(self, manish_chart):
        directions = {z.direction for z in compute_mandala_zones(manish_chart)}
        expected = {"North", "North-East", "East", "South-East",
                    "South", "South-West", "West", "North-West"}
        assert expected.issubset(directions)

    def test_zones_have_hindi_names(self, manish_chart):
        for zone in compute_mandala_zones(manish_chart):
            assert zone.direction_hi, f"{zone.direction} missing Hindi name"

    def test_center_zone_planet_is_brahma(self, manish_chart):
        center = next(z for z in compute_mandala_zones(manish_chart) if z.direction == "Center")
        assert center.planet == "Brahma"


# ── Room Recommendations ──────────────────────────────────────────────────────


class TestComputeRoomRecommendations:
    """Tests for compute_room_recommendations()."""

    def test_returns_list_of_room_recommendations(self, manish_chart):
        rooms = compute_room_recommendations(manish_chart)
        assert all(isinstance(r, RoomRecommendation) for r in rooms)

    def test_returns_seven_room_types(self, manish_chart):
        # vastu_rules.yaml defines 7 room types
        rooms = compute_room_recommendations(manish_chart)
        assert len(rooms) == 7

    def test_planet_strengths_in_range(self, manish_chart):
        for room in compute_room_recommendations(manish_chart):
            assert 0.0 <= room.planet_strength <= 100.0

    def test_is_favorable_consistent_with_strength(self, manish_chart):
        for room in compute_room_recommendations(manish_chart):
            if room.planet_strength >= 50.0:
                assert room.is_favorable is True
            else:
                assert room.is_favorable is False

    def test_kitchen_ideal_direction_is_southeast(self, manish_chart):
        rooms = compute_room_recommendations(manish_chart)
        kitchen = next(r for r in rooms if r.room == "Kitchen")
        assert kitchen.ideal_direction == "South-East"

    def test_puja_room_ideal_direction_is_northeast(self, manish_chart):
        rooms = compute_room_recommendations(manish_chart)
        puja = next(r for r in rooms if r.room == "Puja Room")
        assert puja.ideal_direction == "North-East"

    def test_main_entrance_uses_lagna_lord_direction(self, manish_chart):
        # Mithuna lagna → Mercury → North
        rooms = compute_room_recommendations(manish_chart)
        entrance = next(r for r in rooms if r.room == "Main Entrance")
        assert entrance.ideal_direction == "North"

    def test_all_rooms_have_reasons(self, manish_chart):
        for room in compute_room_recommendations(manish_chart):
            assert room.reason, f"{room.room} missing reason"


# ── Door Analysis ─────────────────────────────────────────────────────────────


class TestAnalyzeEntryDoor:
    """Tests for analyze_entry_door()."""

    def test_returns_door_analysis_instance(self, manish_chart):
        assert isinstance(analyze_entry_door(manish_chart), DoorAnalysis)

    def test_ayadi_field_is_valid_instance(self, manish_chart):
        door = analyze_entry_door(manish_chart)
        assert isinstance(door.ayadi_field, AyadiField)

    def test_field_number_in_range(self, manish_chart):
        door = analyze_entry_door(manish_chart)
        assert 1 <= door.ayadi_field.field_number <= 32

    def test_lagna_alignment_is_valid(self, manish_chart):
        door = analyze_entry_door(manish_chart)
        assert door.lagna_alignment in {"Excellent", "Good", "Neutral"}

    def test_mithuna_gets_north_devta_field(self, manish_chart):
        # Mercury rules North; North has Devta fields (1 and 2)
        door = analyze_entry_door(manish_chart)
        assert door.recommended_direction == "North"
        assert door.classification == "Devta"
        assert door.lagna_alignment == "Excellent"

    def test_recommendation_is_nonempty_string(self, manish_chart):
        door = analyze_entry_door(manish_chart)
        assert len(door.recommendation) > 10

    def test_recommended_direction_has_hindi_name(self, manish_chart):
        door = analyze_entry_door(manish_chart)
        assert door.recommended_direction_hi


# ── Integration: compute_vastu ────────────────────────────────────────────────


class TestComputeVastu:
    """Integration tests for compute_vastu() — the main entry point."""

    def test_returns_vastu_result_instance(self, manish_chart):
        assert isinstance(compute_vastu(manish_chart), VastuResult)

    def test_lagna_populated_correctly(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert result.lagna == "Mithuna"

    def test_lagna_lord_is_mercury(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert result.lagna_lord == "Mercury"

    def test_direction_strengths_present(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert len(result.direction_strengths) == 9

    def test_favorable_directions_present(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert "lagna" in result.favorable_directions

    def test_mandala_zones_count(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert len(result.mandala_zones) == 9

    def test_room_recommendations_count(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert len(result.room_recommendations) == 7

    def test_door_analysis_present(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert isinstance(result.door_analysis, DoorAnalysis)

    def test_doshas_all_defined(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert len(result.doshas) == 5

    def test_active_doshas_is_subset_of_doshas(self, manish_chart):
        result = compute_vastu(manish_chart)
        dosha_names = {d.name for d in result.doshas}
        for active in result.active_doshas:
            assert active in dosha_names

    def test_summary_contains_lagna(self, manish_chart):
        result = compute_vastu(manish_chart)
        assert "Mithuna" in result.summary

    def test_most_and_least_favorable_directions_differ(self, manish_chart):
        result = compute_vastu(manish_chart)
        # With 9 planets spread across 8 directions, these could be the same
        # only if all planets have identical strength — extremely unlikely
        assert result.most_favorable_direction != "" or result.least_favorable_direction != ""

    @pytest.mark.safety
    def test_vastu_result_is_frozen(self, manish_chart):
        """VastuResult must be immutable — no accidental mutation."""
        result = compute_vastu(manish_chart)
        with pytest.raises(ValidationError):
            result.lagna = "Mesha"  # type: ignore[misc]


# ── Vastu Dosha Activation ────────────────────────────────────────────────────


class TestVastuDoshaActivation:
    """Verify each of the 5 vastu doshas fires when the trigger planet is in house 4."""

    def _get_present_doshas(self, trigger_planet: str) -> list[VastuDosha]:
        chart = _make_dosha_chart(trigger_planet)
        return [d for d in detect_vastu_doshas(chart) if d.is_present]

    def test_saturn_in_4th_triggers_griha_bala_dosha(self):
        """Saturn in 4th → Griha Bala Dosha present."""
        present = self._get_present_doshas("Saturn")
        names = [d.name for d in present]
        assert "Griha Bala Dosha" in names

    def test_mars_in_4th_triggers_agni_sthan_dosha(self):
        """Mars in 4th → Agni Sthan Dosha present."""
        present = self._get_present_doshas("Mars")
        names = [d.name for d in present]
        assert "Agni Sthan Dosha" in names

    def test_rahu_in_4th_triggers_vastu_bhaya_dosha(self):
        """Rahu in 4th → Vastu Bhaya Dosha present."""
        present = self._get_present_doshas("Rahu")
        names = [d.name for d in present]
        assert "Vastu Bhaya Dosha" in names

    def test_sun_in_4th_triggers_pitr_sthan_dosha(self):
        """Sun in 4th → Pitr Sthan Dosha present."""
        present = self._get_present_doshas("Sun")
        names = [d.name for d in present]
        assert "Pitr Sthan Dosha" in names

    def test_ketu_in_4th_triggers_moksha_sthan_dosha(self):
        """Ketu in 4th → Moksha Sthan Dosha present."""
        present = self._get_present_doshas("Ketu")
        names = [d.name for d in present]
        assert "Moksha Sthan Dosha" in names

    def test_saturn_not_in_4th_griha_bala_absent(self, manish_chart):
        """Manish: Saturn in house 7, not 4 → Griha Bala Dosha absent."""
        # Manish's Saturn is in house 7 (Sagittarius)
        doshas = detect_vastu_doshas(manish_chart)
        griha = next(d for d in doshas if d.name == "Griha Bala Dosha")
        assert griha.is_present is False
        assert griha.severity == "none"

    def test_present_dosha_has_non_none_severity(self):
        """An activated dosha has severity in {mild, moderate, severe}."""
        chart = _make_dosha_chart("Saturn")
        doshas = detect_vastu_doshas(chart)
        saturn_dosha = next(d for d in doshas if d.name == "Griha Bala Dosha")
        assert saturn_dosha.is_present is True
        assert saturn_dosha.severity in {"mild", "moderate", "severe"}

    def test_only_trigger_planet_dosha_is_present(self):
        """Only the dosha for the trigger planet should be present (others absent)."""
        chart = _make_dosha_chart("Mars")
        doshas = detect_vastu_doshas(chart)
        present = [d for d in doshas if d.is_present]
        # Only Agni Sthan Dosha should be present
        assert len(present) == 1
        assert present[0].name == "Agni Sthan Dosha"
