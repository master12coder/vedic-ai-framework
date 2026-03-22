"""Tests for Namakarana — Vedic naming ceremony computation."""

from __future__ import annotations

from daivai_engine.compute.namakarana import (
    check_gand_mool,
    compute_namakarana,
    compute_name_number,
    get_naming_syllables,
    get_rashi_letters,
    score_name,
    suggest_names,
)
from daivai_engine.models.namakarana import (
    GandMoolResult,
    NamakaranaResult,
    NameNumerology,
    NameScore,
    NameSuggestion,
)


class TestGetNamingSyllables:
    """Tests for get_naming_syllables()."""

    def test_returns_list(self, manish_chart) -> None:
        moon = manish_chart.planets["Moon"]
        syllables = get_naming_syllables(moon.nakshatra, moon.pada)
        assert isinstance(syllables, list)

    def test_rohini_pada_2_returns_syllables(self) -> None:
        # Manish: Moon in Rohini Pada 2
        syllables = get_naming_syllables("Rohini", 2)
        assert len(syllables) > 0

    def test_syllables_are_strings(self) -> None:
        syllables = get_naming_syllables("Ashwini", 1)
        for s in syllables:
            assert isinstance(s, str)

    def test_all_27_nakshatras_load(self) -> None:
        from daivai_engine.constants import NAKSHATRAS

        for nak in NAKSHATRAS:
            syllables = get_naming_syllables(nak, 1)
            assert isinstance(syllables, list)


class TestGetRashiLetters:
    """Tests for get_rashi_letters()."""

    def test_returns_list(self, manish_chart) -> None:
        letters = get_rashi_letters(manish_chart.planets["Moon"].sign)
        assert isinstance(letters, list)

    def test_letters_are_strings(self) -> None:
        letters = get_rashi_letters("Mithuna")
        for letter in letters:
            assert isinstance(letter, str)


class TestCheckGandMool:
    """Tests for check_gand_mool()."""

    def test_returns_gand_mool_result(self, manish_chart) -> None:
        result = check_gand_mool(manish_chart)
        assert isinstance(result, GandMoolResult)

    def test_is_gand_mool_is_bool(self, manish_chart) -> None:
        result = check_gand_mool(manish_chart)
        assert isinstance(result.is_gand_mool, bool)

    def test_manish_not_gand_mool(self, manish_chart) -> None:
        # Manish Moon in Rohini — NOT a Gand Mool nakshatra
        result = check_gand_mool(manish_chart)
        assert not result.is_gand_mool

    def test_severity_field_exists(self, manish_chart) -> None:
        result = check_gand_mool(manish_chart)
        assert hasattr(result, "severity")

    def test_description_non_empty(self, manish_chart) -> None:
        result = check_gand_mool(manish_chart)
        assert result.description


class TestComputeNameNumber:
    """Tests for compute_name_number()."""

    def test_returns_name_numerology(self) -> None:
        result = compute_name_number("Manish")
        assert isinstance(result, NameNumerology)

    def test_name_number_in_range(self) -> None:
        result = compute_name_number("Manish")
        assert 1 <= result.name_number <= 9

    def test_raw_sum_positive(self) -> None:
        result = compute_name_number("Manish")
        assert result.raw_sum > 0

    def test_name_stored_correctly(self) -> None:
        result = compute_name_number("Manish")
        assert result.name == "Manish"

    def test_interpretation_non_empty(self) -> None:
        result = compute_name_number("Manish")
        assert result.interpretation


class TestScoreName:
    """Tests for score_name()."""

    def test_returns_name_score(self, manish_chart) -> None:
        result = score_name("Manish", manish_chart)
        assert isinstance(result, NameScore)

    def test_total_score_in_range(self, manish_chart) -> None:
        result = score_name("Manish", manish_chart)
        assert 0.0 <= result.total_score <= 100.0

    def test_is_recommended_is_bool(self, manish_chart) -> None:
        result = score_name("Manish", manish_chart)
        assert isinstance(result.is_recommended, bool)

    def test_recommendation_threshold_60(self, manish_chart) -> None:
        result = score_name("Manish", manish_chart)
        if result.total_score >= 60.0:
            assert result.is_recommended
        else:
            assert not result.is_recommended

    def test_name_number_in_range(self, manish_chart) -> None:
        result = score_name("Manish", manish_chart)
        assert 1 <= result.name_number <= 9

    def test_breakdown_is_dict(self, manish_chart) -> None:
        result = score_name("Manish", manish_chart)
        assert isinstance(result.breakdown, dict)


class TestSuggestNames:
    """Tests for suggest_names()."""

    def test_returns_name_suggestion(self, manish_chart) -> None:
        result = suggest_names(manish_chart)
        assert isinstance(result, NameSuggestion)

    def test_nakshatra_is_rohini(self, manish_chart) -> None:
        result = suggest_names(manish_chart)
        assert result.nakshatra == "Rohini"

    def test_pada_is_2(self, manish_chart) -> None:
        result = suggest_names(manish_chart)
        assert result.pada == 2

    def test_primary_letters_non_empty(self, manish_chart) -> None:
        result = suggest_names(manish_chart)
        assert len(result.primary_letters) > 0

    def test_guidance_non_empty(self, manish_chart) -> None:
        result = suggest_names(manish_chart)
        assert result.guidance

    def test_compatible_name_numbers_in_range(self, manish_chart) -> None:
        result = suggest_names(manish_chart)
        for n in result.compatible_name_numbers:
            assert 1 <= n <= 9


class TestComputeNamakarana:
    """Integration tests for compute_namakarana()."""

    def test_returns_namakarana_result(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart)
        assert isinstance(result, NamakaranaResult)

    def test_gand_mool_field_present(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart)
        assert isinstance(result.gand_mool, GandMoolResult)

    def test_suggestion_field_present(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart)
        assert isinstance(result.suggestion, NameSuggestion)

    def test_suggestion_nakshatra_matches_moon(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart)
        assert result.suggestion.nakshatra == manish_chart.planets["Moon"].nakshatra

    def test_suggestion_pada_matches_moon(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart)
        assert result.suggestion.pada == manish_chart.planets["Moon"].pada
