"""Tests for Namakarana (Naming Ceremony) computation.

Verification references:
    Manish Chaurasia: 13/03/1989, 12:17 PM, Varanasi
    Moon nakshatra: Rohini (index 3), Pada: 2
    Recommended syllable: Va (वा)
    Birth rashi: Vrishabha (index 1)

Tests cover:
    - 108-syllable lookup accuracy (known nakshatra-pada pairs)
    - Syllable count and completeness (all 27 nakshatras x 4 padas = 108)
    - Rashi letter assignment for all 12 rashis
    - Name scoring dimensions (nakshatra, rashi, numerology, sound)
    - Name suggestions filtering and ranking
    - Muhurta computation basics
    - Model structure validation
    - Edge cases and type safety
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.namakarana import (
    compute_life_number,
    compute_namakarana,
    compute_namakarana_muhurta,
    compute_name_numerology,
    get_nakshtra_akshar,
    get_naming_syllables,
    get_rashi_letters,
    score_name,
    suggest_names,
)
from daivai_engine.knowledge.loader import load_namakarana_rules
from daivai_engine.models.namakarana import (
    NakshtraAkshar,
    NamakaranaMuhurta,
    NamakaranaResult,
    NameScore,
    NameSuggestion,
    RashiLetters,
)


# ── YAML completeness tests ────────────────────────────────────────────────


class TestNamakaranaYaml:
    def test_yaml_loads_successfully(self) -> None:
        rules = load_namakarana_rules()
        assert isinstance(rules, dict)
        assert "aksharas" in rules

    def test_108_padas_present(self) -> None:
        """Exactly 27 nakshatras x 4 padas = 108 entries."""
        rules = load_namakarana_rules()
        aksharas: list[dict] = rules["aksharas"]
        assert len(aksharas) == 27
        total_padas = sum(len(a["padas"]) for a in aksharas)
        assert total_padas == 108

    def test_nakshatra_indices_are_0_to_26(self) -> None:
        rules = load_namakarana_rules()
        indices = sorted(a["nakshatra_index"] for a in rules["aksharas"])
        assert indices == list(range(27))

    def test_rashi_letters_all_12_present(self) -> None:
        rules = load_namakarana_rules()
        rashi_data: list[dict] = rules["rashi_letters"]
        assert len(rashi_data) == 12
        indices = sorted(r["rashi_index"] for r in rashi_data)
        assert indices == list(range(12))

    def test_numerology_mapping_has_all_letters(self) -> None:
        rules = load_namakarana_rules()
        letter_vals: dict = rules["numerology"]["letter_values"]
        for ch in "abcdefghijklmnopqrstuvwxyz":
            assert ch in letter_vals, f"Missing letter: {ch}"

    def test_muhurta_rules_present(self) -> None:
        rules = load_namakarana_rules()
        assert "muhurta_rules" in rules
        assert "all_favorable_nakshatras" in rules["muhurta_rules"]
        assert len(rules["muhurta_rules"]["all_favorable_nakshatras"]) >= 10

    def test_names_database_present(self) -> None:
        rules = load_namakarana_rules()
        names: list[dict] = rules["names"]
        assert len(names) >= 30


# ── Syllable lookup tests ──────────────────────────────────────────────────


class TestGetNamingSyllables:
    def test_rohini_pada_2_returns_va(self) -> None:
        """Manish = Rohini Pada 2 → primary syllable is Va."""
        syllables = get_naming_syllables(3, 2)
        assert "Va" in syllables

    def test_ashwini_pada_1_returns_chu(self) -> None:
        syllables = get_naming_syllables(0, 1)
        assert "Chu" in syllables

    def test_ashwini_pada_4_returns_la(self) -> None:
        syllables = get_naming_syllables(0, 4)
        assert "La" in syllables

    def test_bharani_pada_1_returns_li(self) -> None:
        syllables = get_naming_syllables(1, 1)
        assert "Li" in syllables

    def test_krittika_pada_1_returns_a(self) -> None:
        syllables = get_naming_syllables(2, 1)
        assert "A" in syllables

    def test_magha_pada_1_returns_ma(self) -> None:
        syllables = get_naming_syllables(9, 1)
        assert "Ma" in syllables

    def test_revati_pada_3_returns_cha(self) -> None:
        syllables = get_naming_syllables(26, 3)
        assert "Cha" in syllables

    def test_moola_pada_3_returns_bha(self) -> None:
        syllables = get_naming_syllables(18, 3)
        assert "Bha" in syllables

    def test_all_nakshatras_return_non_empty_syllables(self) -> None:
        for nak_idx in range(27):
            for pada in range(1, 5):
                result = get_naming_syllables(nak_idx, pada)
                assert len(result) >= 1, f"Empty for nakshatra {nak_idx} pada {pada}"

    def test_returns_list_type(self) -> None:
        result = get_naming_syllables(3, 1)
        assert isinstance(result, list)


# ── NakshtraAkshar model tests ─────────────────────────────────────────────


class TestGetNakshtraAkshar:
    def test_rohini_pada_2_model(self) -> None:
        akshar = get_nakshtra_akshar(3, 2)
        assert isinstance(akshar, NakshtraAkshar)
        assert akshar.nakshatra == "Rohini"
        assert akshar.nakshatra_index == 3
        assert akshar.pada == 2
        assert akshar.syllable == "Va"
        assert akshar.nakshatra_lord == "Moon"
        assert akshar.rashi == "Vrishabha"

    def test_ashwini_pada_1_model(self) -> None:
        akshar = get_nakshtra_akshar(0, 1)
        assert akshar.nakshatra == "Ashwini"
        assert akshar.syllable == "Chu"
        assert akshar.nakshatra_lord == "Ketu"

    def test_revati_pada_4_model(self) -> None:
        akshar = get_nakshtra_akshar(26, 4)
        assert akshar.nakshatra == "Revati"
        assert akshar.nakshatra_lord == "Mercury"

    def test_model_is_frozen(self) -> None:
        from pydantic import ValidationError
        akshar = get_nakshtra_akshar(0, 1)
        with pytest.raises((ValidationError, TypeError)):
            akshar.syllable = "X"  # type: ignore[misc]


# ── Rashi letters tests ────────────────────────────────────────────────────


class TestGetRashiLetters:
    def test_vrishabha_contains_va(self) -> None:
        """Rohini falls in Vrishabha — should include Va."""
        rashi = get_rashi_letters(1)
        assert isinstance(rashi, RashiLetters)
        assert "Va" in rashi.letters

    def test_mesha_contains_chu(self) -> None:
        """Ashwini falls in Mesha — should include Chu."""
        rashi = get_rashi_letters(0)
        assert "Chu" in rashi.letters

    def test_mithuna_contains_ka(self) -> None:
        """Mrigashira pada 3-4 falls in Mithuna."""
        rashi = get_rashi_letters(2)
        assert "Ka" in rashi.letters

    def test_all_rashis_return_non_empty(self) -> None:
        for idx in range(12):
            rashi = get_rashi_letters(idx)
            assert len(rashi.letters) >= 1

    def test_each_rashi_has_primary_letters(self) -> None:
        for idx in range(12):
            rashi = get_rashi_letters(idx)
            assert len(rashi.primary_letters) >= 1


# ── Numerology tests ───────────────────────────────────────────────────────


class TestNumerology:
    def test_compute_name_numerology_returns_1_to_9(self) -> None:
        for name in ["Ram", "Sita", "Arjun", "Draupadi", "Krishna"]:
            num = compute_name_numerology(name)
            assert 1 <= num <= 9, f"Invalid number {num} for {name}"

    def test_compute_life_number_manish(self) -> None:
        """13/03/1989: 1+3+0+3+1+9+8+9 = 34 → 3+4 = 7."""
        num = compute_life_number("13/03/1989")
        assert num == 7

    def test_compute_life_number_reduces_correctly(self) -> None:
        """01/01/2000: 0+1+0+1+2+0+0+0 = 4."""
        num = compute_life_number("01/01/2000")
        assert num == 4

    def test_numerology_consistent_for_same_name(self) -> None:
        assert compute_name_numerology("Varun") == compute_name_numerology("VARUN")

    def test_numerology_handles_single_letter(self) -> None:
        num = compute_name_numerology("A")
        assert 1 <= num <= 9


# ── Name scoring tests ─────────────────────────────────────────────────────


class TestScoreName:
    def test_varun_scores_high_for_manish_chart(self, manish_chart) -> None:
        """Varun starts with 'Va' = Rohini Pada 2 syllable → nakshatra match."""
        score = score_name("Varun", manish_chart)
        assert score.nakshatra_syllable_match is True
        assert score.matching_syllable == "Va"
        assert score.nakshatra_score == 10.0
        assert score.total_score >= 7.0

    def test_non_matching_name_scores_lower(self, manish_chart) -> None:
        score_match = score_name("Varun", manish_chart)
        score_nomatch = score_name("Rajesh", manish_chart)
        assert score_match.total_score > score_nomatch.total_score

    def test_score_model_structure(self, manish_chart) -> None:
        score = score_name("Varun", manish_chart)
        assert isinstance(score, NameScore)
        assert 0 <= score.total_score <= 10
        assert score.recommendation in (
            "Highly Recommended", "Recommended", "Acceptable", "Avoid"
        )
        assert 1 <= score.numerology_name_number <= 9
        assert 1 <= score.numerology_life_number <= 9

    def test_nakshatra_mismatch_gives_zero_nakshatra_score(self, manish_chart) -> None:
        """'Zephyr' doesn't start with any Rohini syllable."""
        score = score_name("Zephyr", manish_chart)
        assert score.nakshatra_syllable_match is False
        assert score.nakshatra_score == 0.0

    def test_planet_of_sound_is_valid_planet(self, manish_chart) -> None:
        from daivai_engine.constants import PLANETS
        score = score_name("Mahesh", manish_chart)
        assert score.planet_of_sound in PLANETS

    def test_highly_recommended_label_for_nakshatra_match(self, manish_chart) -> None:
        score = score_name("Varun", manish_chart)
        assert score.recommendation in ("Highly Recommended", "Recommended")


# ── Name suggestions tests ─────────────────────────────────────────────────


class TestSuggestNames:
    def test_returns_list(self, manish_chart) -> None:
        suggestions = suggest_names(manish_chart, "M")
        assert isinstance(suggestions, list)

    def test_male_filter_works(self, manish_chart) -> None:
        suggestions = suggest_names(manish_chart, "M")
        for s in suggestions:
            assert s.gender in ("M", "N")

    def test_female_filter_works(self, sample_chart) -> None:
        suggestions = suggest_names(sample_chart, "F")
        for s in suggestions:
            assert s.gender in ("F", "N")

    def test_sorted_by_score_descending(self, manish_chart) -> None:
        suggestions = suggest_names(manish_chart, "M")
        if len(suggestions) >= 2:
            scores = [s.score.total_score for s in suggestions]
            assert scores == sorted(scores, reverse=True)

    def test_nakshatra_match_names_at_top(self, manish_chart) -> None:
        """Names starting with Va/Ba/O should score highest for Rohini Pada 2."""
        suggestions = suggest_names(manish_chart, "M")
        if suggestions:
            top = suggestions[0]
            assert top.score.total_score >= suggestions[-1].score.total_score

    def test_suggestion_model_structure(self, manish_chart) -> None:
        suggestions = suggest_names(manish_chart, "M")
        if suggestions:
            s = suggestions[0]
            assert isinstance(s, NameSuggestion)
            assert isinstance(s.name, str) and s.name
            assert isinstance(s.meaning, str)
            assert isinstance(s.score, NameScore)


# ── Muhurta tests ──────────────────────────────────────────────────────────


class TestNamakaranaMuhurta:
    def test_returns_list(self) -> None:
        results = compute_namakarana_muhurta(
            birth_date="13/03/1989",
            lat=25.3176,
            lon=83.0067,
        )
        assert isinstance(results, list)

    def test_muhurta_model_structure(self) -> None:
        results = compute_namakarana_muhurta(
            birth_date="13/03/1989",
            lat=25.3176,
            lon=83.0067,
            max_results=3,
        )
        if results:
            m = results[0]
            assert isinstance(m, NamakaranaMuhurta)
            assert m.paksha in ("Shukla", "Krishna")
            assert isinstance(m.score, float)
            assert isinstance(m.reasons, list)
            assert isinstance(m.is_recommended, bool)

    def test_sorted_by_score_descending(self) -> None:
        results = compute_namakarana_muhurta(
            birth_date="13/03/1989",
            lat=25.3176,
            lon=83.0067,
            max_results=5,
        )
        if len(results) >= 2:
            scores = [r.score for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_max_results_respected(self) -> None:
        results = compute_namakarana_muhurta(
            birth_date="13/03/1989",
            lat=25.3176,
            lon=83.0067,
            max_results=3,
        )
        assert len(results) <= 3

    def test_dates_after_sutak_period(self) -> None:
        """All returned dates must be ≥ 10 days after birth."""
        from datetime import datetime
        birth = datetime(1989, 3, 13)
        earliest_allowed = birth.replace(day=23)  # + 10 days
        results = compute_namakarana_muhurta(
            birth_date="13/03/1989",
            lat=25.3176,
            lon=83.0067,
        )
        for r in results:
            day, month, year = r.date.split("/")
            date = datetime(int(year), int(month), int(day))
            assert date >= earliest_allowed, f"Date {r.date} is before sutak period end"


# ── Full computation tests ─────────────────────────────────────────────────


class TestComputeNamakarana:
    def test_full_result_structure(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart, "M")
        assert isinstance(result, NamakaranaResult)
        assert result.birth_nakshatra == "Rohini"
        assert result.birth_nakshatra_index == 3
        assert result.birth_pada == 2
        assert result.birth_rashi == "Vrishabha"

    def test_prescribed_syllable_is_va(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart, "M")
        assert result.nakshatra_akshar.syllable == "Va"

    def test_rashi_letters_are_vrishabha(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart, "M")
        assert result.rashi_letters.rashi == "Vrishabha"
        assert "Va" in result.rashi_letters.letters

    def test_name_suggestions_present(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart, "M")
        assert len(result.name_suggestions) >= 1

    def test_muhurta_candidates_present(self, manish_chart) -> None:
        result = compute_namakarana(manish_chart, "M")
        assert len(result.muhurta_candidates) >= 1
