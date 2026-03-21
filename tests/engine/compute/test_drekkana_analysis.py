"""Tests for Drekkana (D3) Analysis for sibling significations."""

from __future__ import annotations

from daivai_engine.compute.drekkana_analysis import (
    DrekkanaAnalysisResult,
    DrekkanaPosition,
    SiblingAnalysis,
    compute_drekkana_analysis,
    get_drekkana_position,
)
from daivai_engine.models.chart import ChartData


_VALID_NATURES = {"human", "quadruped", "serpent", "mixed"}
_VALID_STRENGTHS = {"strong", "moderate", "weak"}


class TestDrekkanaPositions:
    def test_returns_9_positions(self, manish_chart: ChartData) -> None:
        """9 planets: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu."""
        result = compute_drekkana_analysis(manish_chart)
        assert len(result.all_positions) == 9

    def test_all_planets_present(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        planets = {p.planet for p in result.all_positions}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert planets == expected

    def test_d3_sign_indices_valid(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert 0 <= p.d3_sign_index <= 11

    def test_drekkana_parts_valid(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert p.drekkana_part in (0, 1, 2)

    def test_nature_values_valid(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert p.nature in _VALID_NATURES

    def test_drekkana_name_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert len(p.drekkana_name) > 0

    def test_d3_lord_is_valid_planet(self, manish_chart: ChartData) -> None:
        valid_lords = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert p.d3_lord in valid_lords

    def test_is_sarpa_drekkana_is_bool(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert isinstance(p.is_sarpa_drekkana, bool)

    def test_sibling_indication_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert len(p.sibling_indication) > 0

    def test_returns_drekkana_position_instances(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        for p in result.all_positions:
            assert isinstance(p, DrekkanaPosition)

    def test_natal_sign_matches_chart(self, manish_chart: ChartData) -> None:
        from daivai_engine.constants import SIGNS
        result = compute_drekkana_analysis(manish_chart)
        for pos in result.all_positions:
            chart_sign = manish_chart.planets[pos.planet].sign_index
            assert pos.natal_sign_index == chart_sign
            assert pos.natal_sign == SIGNS[chart_sign]

    def test_drekkana_part_from_degree(self, manish_chart: ChartData) -> None:
        """Part 0 for 0-10°, part 1 for 10-20°, part 2 for 20-30°."""
        result = compute_drekkana_analysis(manish_chart)
        for pos in result.all_positions:
            degree = pos.natal_degree
            expected_part = min(int(degree / 10.0), 2)
            assert pos.drekkana_part == expected_part


class TestSarpaDispositor:
    def test_sarpa_planets_are_subset_of_all(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        all_names = {p.planet for p in result.all_positions}
        assert set(result.sarpa_drekkana_planets).issubset(all_names)

    def test_sarpa_planets_match_positions(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        sarpa_from_positions = {
            p.planet for p in result.all_positions if p.is_sarpa_drekkana
        }
        assert set(result.sarpa_drekkana_planets) == sarpa_from_positions

    def test_known_sarpa_drekkanas(self) -> None:
        """Test static Sarpa identification: Mesha 2nd decanate should be Sarpa."""
        from daivai_engine.compute.drekkana_analysis import _is_sarpa_drekkana
        # Mesha (0), part 1 = Sarpa
        assert _is_sarpa_drekkana(0, 1, 4) is True
        # Karka (3), part 0 = Sarpa
        assert _is_sarpa_drekkana(3, 0, 3) is True
        # Vrischika (7), parts 0 and 1 = Sarpa
        assert _is_sarpa_drekkana(7, 0, 7) is True
        assert _is_sarpa_drekkana(7, 1, 11) is True
        # Meena (11), part 0 = Sarpa
        assert _is_sarpa_drekkana(11, 0, 11) is True
        # Dhanu (8), part 0 = NOT Sarpa
        assert _is_sarpa_drekkana(8, 0, 8) is False


class TestSiblingAnalysis:
    def test_returns_sibling_analysis(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert isinstance(result.sibling_analysis, SiblingAnalysis)

    def test_third_house_lord_valid(self, manish_chart: ChartData) -> None:
        valid_lords = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        result = compute_drekkana_analysis(manish_chart)
        assert result.sibling_analysis.third_house_lord in valid_lords

    def test_third_house_occupants_list(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert isinstance(result.sibling_analysis.third_house_occupants, list)

    def test_d3_third_house_occupants_list(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert isinstance(result.sibling_analysis.d3_third_house_occupants, list)

    def test_sibling_count_indication_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert len(result.sibling_analysis.sibling_count_indication) > 0

    def test_sibling_nature_non_empty(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert len(result.sibling_analysis.sibling_nature) > 0

    def test_strength_valid(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert result.sibling_analysis.strength in _VALID_STRENGTHS

    def test_has_sarpa_drekkana_is_bool(self, manish_chart: ChartData) -> None:
        result = compute_drekkana_analysis(manish_chart)
        assert isinstance(result.sibling_analysis.has_sarpa_drekkana, bool)

    def test_manish_third_lord_is_sun(self, manish_chart: ChartData) -> None:
        """Manish: Lagna = Mithuna (2). 3rd house = Simha (4). Lord = Sun."""
        result = compute_drekkana_analysis(manish_chart)
        # 3rd house from Mithuna (index 2) = (2+2)%12 = 4 = Simha, lord=Sun
        assert result.sibling_analysis.third_house_lord == "Sun"

    def test_third_lord_d3_sign_is_valid_sign(self, manish_chart: ChartData) -> None:
        from daivai_engine.constants import SIGNS
        result = compute_drekkana_analysis(manish_chart)
        assert result.sibling_analysis.third_house_lord_d3_sign in SIGNS

    def test_works_on_sample_chart(self, sample_chart: ChartData) -> None:
        result = compute_drekkana_analysis(sample_chart)
        assert isinstance(result, DrekkanaAnalysisResult)


class TestGetDrekkanaPosition:
    def test_longitude_0_is_mesha_first_drekkana(self) -> None:
        """0° = start of Mesha, first Drekkana."""
        pos = get_drekkana_position(0.0, "Lagna")
        assert pos.natal_sign_index == 0
        assert pos.drekkana_part == 0
        assert pos.d3_sign_index == 0  # Same sign for first Drekkana

    def test_longitude_15_mesha_second_drekkana(self) -> None:
        """15° Mesha = second Drekkana (10-20°). D3 = 5th from Mesha = Simha (4)."""
        pos = get_drekkana_position(15.0, "Test")
        assert pos.natal_sign_index == 0
        assert pos.drekkana_part == 1
        assert pos.d3_sign_index == 4  # Simha
        assert pos.is_sarpa_drekkana is True  # Mesha 2nd Drekkana = Sarpa

    def test_longitude_25_mesha_third_drekkana(self) -> None:
        """25° Mesha = third Drekkana (20-30°). D3 = 9th from Mesha = Dhanu (8)."""
        pos = get_drekkana_position(25.0, "Test")
        assert pos.natal_sign_index == 0
        assert pos.drekkana_part == 2
        assert pos.d3_sign_index == 8  # Dhanu

    def test_label_used_as_planet_name(self) -> None:
        pos = get_drekkana_position(90.0, "Lagna")
        assert pos.planet == "Lagna"

    def test_default_planet_name(self) -> None:
        pos = get_drekkana_position(90.0)
        assert pos.planet == "Point"
