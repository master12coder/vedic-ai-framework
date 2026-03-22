"""Tests for D60 Shashtyamsha analysis — deity lookup and chart analysis."""

from __future__ import annotations

from daivai_engine.compute.shashtyamsha_analysis import (
    _get_deity_for_part,
    _load_deities,
    analyze_d60_chart,
    get_d60_position,
)
from daivai_engine.constants import PLANETS, SIGNS
from daivai_engine.models.shashtyamsha import (
    D60Analysis,
    ShashtyamshaDeity,
    ShashtyamshaPosition,
)


class TestLoadDeities:
    """Tests for _load_deities() — YAML deity data."""

    def test_returns_60_deities(self) -> None:
        deities = _load_deities()
        assert len(deities) == 60

    def test_all_are_shashtyamsha_deity(self) -> None:
        deities = _load_deities()
        for d in deities:
            assert isinstance(d, ShashtyamshaDeity)

    def test_nature_is_valid(self) -> None:
        deities = _load_deities()
        valid_natures = {"Saumya", "Krura", "Mishra"}
        for d in deities:
            assert d.nature in valid_natures, f"Deity {d}: invalid nature {d.nature}"

    def test_deity_names_non_empty(self) -> None:
        deities = _load_deities()
        for d in deities:
            assert d.name, "Deity has empty name"


class TestGetDeityForPart:
    """Tests for _get_deity_for_part() — sign/part → deity."""

    def test_returns_shashtyamsha_deity(self) -> None:
        deity = _get_deity_for_part(0, 0)
        assert isinstance(deity, ShashtyamshaDeity)

    def test_odd_sign_forward_order(self) -> None:
        # Odd sign (sign_index=0) — part 0 = deity 1 (index 0)
        deity_0 = _get_deity_for_part(0, 0)
        deity_1 = _get_deity_for_part(0, 1)
        deities = _load_deities()
        assert deity_0 == deities[0]
        assert deity_1 == deities[1]

    def test_even_sign_reverse_order(self) -> None:
        # Even sign (sign_index=1) — part 0 = deity 60 (index 59)
        deity_0 = _get_deity_for_part(1, 0)
        deities = _load_deities()
        assert deity_0 == deities[59]

    def test_all_sign_part_combinations_valid(self) -> None:
        for sign_idx in range(12):
            for part in range(60):
                deity = _get_deity_for_part(sign_idx, part)
                assert isinstance(deity, ShashtyamshaDeity)


class TestGetD60Position:
    """Tests for get_d60_position() — longitude → ShashtyamshaPosition."""

    def test_returns_shashtyamsha_position(self) -> None:
        pos = get_d60_position(45.0, "Sun")
        assert isinstance(pos, ShashtyamshaPosition)

    def test_d1_sign_matches_longitude(self) -> None:
        # 45.0° → Taurus (sign_index=1)
        pos = get_d60_position(45.0, "Sun")
        assert pos.d1_sign_index == 1

    def test_d60_sign_in_valid_range(self) -> None:
        for lon in [0.0, 30.0, 90.0, 180.0, 270.0, 359.9]:
            pos = get_d60_position(lon)
            assert 0 <= pos.d60_sign_index <= 11, f"lon={lon}: d60_sign={pos.d60_sign_index}"

    def test_d1_sign_name_correct(self) -> None:
        pos = get_d60_position(45.0, "Sun")
        assert pos.d1_sign == SIGNS[1]  # Taurus

    def test_d60_sign_name_matches_index(self) -> None:
        pos = get_d60_position(45.0, "Moon")
        assert pos.d60_sign == SIGNS[pos.d60_sign_index]

    def test_vargottam_when_d1_equals_d60(self) -> None:
        pos = get_d60_position(45.0, "Sun")
        expected = pos.d1_sign_index == pos.d60_sign_index
        assert pos.is_vargottam == expected

    def test_planet_name_stored(self) -> None:
        pos = get_d60_position(100.0, "Jupiter")
        assert pos.planet == "Jupiter"

    def test_part_in_range_0_59(self) -> None:
        for lon in [0.0, 15.0, 29.9, 60.0, 180.0, 359.9]:
            pos = get_d60_position(lon)
            assert 0 <= pos.part <= 59, f"lon={lon}: part={pos.part}"


class TestAnalyzeD60Chart:
    """Tests for analyze_d60_chart() — full D60 analysis."""

    def test_returns_d60_analysis(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        assert isinstance(result, D60Analysis)

    def test_all_nine_planets_analyzed(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        assert len(result.planets) == 9

    def test_planet_names_match_input(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        analyzed_names = {pos.planet for pos in result.planets}
        for p in PLANETS:
            assert p in analyzed_names

    def test_classifications_cover_all_planets(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        all_classified = set(result.benefic_planets + result.malefic_planets + result.mixed_planets)
        for p in PLANETS:
            assert p in all_classified, f"{p} not classified in D60"

    def test_no_planet_in_multiple_categories(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        b = set(result.benefic_planets)
        m = set(result.malefic_planets)
        mx = set(result.mixed_planets)
        assert b & m == set()
        assert b & mx == set()
        assert m & mx == set()

    def test_vargottam_planets_are_subset_of_all(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        for p in result.vargottam_planets:
            assert p in PLANETS

    def test_key_findings_is_list(self, manish_chart) -> None:
        result = analyze_d60_chart(manish_chart)
        assert isinstance(result.key_findings, list)
