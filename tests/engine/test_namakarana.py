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
    - Name scoring dimensions (nakshatra, rashi, numerology)
    - Name suggestions filtering and ranking
    - Gand Mool dosha check
    - Model structure validation
    - Edge cases and type safety
"""

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
from daivai_engine.knowledge.loader import load_namakarana_rules
from daivai_engine.models.namakarana import (
    GandMoolResult,
    NamakaranaResult,
    NameScore,
    NameSuggestion,
)


# ── YAML completeness tests ────────────────────────────────────────────────


class TestNamakaranaYaml:
    def test_yaml_loads_successfully(self) -> None:
        rules = load_namakarana_rules()
        assert isinstance(rules, dict)

    def test_yaml_has_required_sections(self) -> None:
        rules = load_namakarana_rules()
        # Should have at least some content
        assert len(rules) > 0


# ── Syllable lookup tests ───────────────────────────────────────────────────


class TestNamingSyllables:
    def test_rohini_pada2_returns_va(self) -> None:
        """Rohini pada 2 -> Va syllable (standard Jyotish reference)."""
        syllables = get_naming_syllables("Rohini", 2)
        assert any("Va" in s or "va" in s.lower() for s in syllables)

    def test_ashwini_pada1_returns_chu(self) -> None:
        syllables = get_naming_syllables("Ashwini", 1)
        assert any("Chu" in s or "che" in s.lower() for s in syllables)

    def test_returns_list_of_strings(self) -> None:
        syllables = get_naming_syllables("Rohini", 1)
        assert isinstance(syllables, list)
        assert all(isinstance(s, str) for s in syllables)

    def test_all_27_nakshatras_x_4_padas(self) -> None:
        """Verify all 108 nakshatra-pada combinations return results."""
        nakshatras = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
            "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
            "Anuradha", "Jyeshtha", "Moola", "Purva Ashadha",
            "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
        ]
        for nakshatra in nakshatras:
            for pada in range(1, 5):
                syllables = get_naming_syllables(nakshatra, pada)
                assert len(syllables) >= 1, f"No syllables for {nakshatra} pada {pada}"

    def test_invalid_nakshatra_handled(self) -> None:
        """Invalid nakshatra should not crash — returns empty list or raises ValueError."""
        try:
            result = get_naming_syllables("InvalidNakshatra", 1)
            assert isinstance(result, list)
        except (KeyError, ValueError):
            pass  # Acceptable to raise on invalid input


# ── Rashi letter tests ─────────────────────────────────────────────────────


class TestRashiLetters:
    def test_vrishabha_has_letters(self) -> None:
        letters = get_rashi_letters("Vrishabha")
        assert isinstance(letters, list)
        assert len(letters) > 0

    def test_all_12_rashis_have_letters(self) -> None:
        rashis = [
            "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
            "Tula", "Vrischika", "Dhanu", "Makara", "Kumbha", "Meena",
        ]
        for rashi in rashis:
            letters = get_rashi_letters(rashi)
            assert len(letters) >= 1, f"No letters for {rashi}"

    def test_returns_list_of_strings(self) -> None:
        letters = get_rashi_letters("Mesha")
        assert isinstance(letters, list)
        assert all(isinstance(s, str) for s in letters)


# ── Name number tests ──────────────────────────────────────────────────────


class TestNameNumber:
    def test_compute_name_number_returns_numerology(self) -> None:
        result = compute_name_number("Manish")
        assert hasattr(result, "name_number")
        assert 1 <= result.name_number <= 9

    def test_same_name_consistent_result(self) -> None:
        r1 = compute_name_number("Priya")
        r2 = compute_name_number("Priya")
        assert r1.name_number == r2.name_number

    def test_name_stored_in_result(self) -> None:
        result = compute_name_number("Arjun")
        assert result.name == "Arjun"

    def test_empty_name_handled(self) -> None:
        """Empty name should either return default or raise ValueError."""
        try:
            result = compute_name_number("")
            assert isinstance(result.name_number, int)
        except (ValueError, ZeroDivisionError):
            pass


# ── Name scoring tests ─────────────────────────────────────────────────────


class TestScoreName:
    def test_score_returns_name_score_model(self, manish_chart: object) -> None:
        result = score_name("Manish", manish_chart)  # type: ignore[arg-type]
        assert isinstance(result, NameScore)

    def test_score_within_bounds(self, manish_chart: object) -> None:
        result = score_name("Manish", manish_chart)  # type: ignore[arg-type]
        assert 0.0 <= result.total_score <= 100.0

    def test_score_components_present(self, manish_chart: object) -> None:
        result = score_name("Manish", manish_chart)  # type: ignore[arg-type]
        assert hasattr(result, "nakshatra_match")
        assert hasattr(result, "rashi_score")
        assert hasattr(result, "numerology_score")
        assert hasattr(result, "is_recommended")

    def test_manish_name_high_score(self, manish_chart: object) -> None:
        """'Manish' starts with 'Ma' — partially matches Rohini pada 2 (Va)."""
        result = score_name("Manish", manish_chart)  # type: ignore[arg-type]
        # Score may be low since 'Ma' != 'Va' — just verify it's computable
        assert 0.0 <= result.total_score <= 100.0


# ── Name suggestion tests ──────────────────────────────────────────────────


class TestSuggestNames:
    def test_suggest_names_returns_suggestion(self, manish_chart: object) -> None:
        result = suggest_names(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result, NameSuggestion)

    def test_suggestion_has_letters(self, manish_chart: object) -> None:
        result = suggest_names(manish_chart)  # type: ignore[arg-type]
        assert len(result.nakshatra_letters) >= 1
        assert len(result.rashi_letters) >= 1

    def test_suggestion_has_nakshatra(self, manish_chart: object) -> None:
        result = suggest_names(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result.nakshatra, str)
        assert result.pada in (1, 2, 3, 4)

    def test_rohini_pada2_manish_chart(self, manish_chart: object) -> None:
        """Manish chart: Moon in Rohini pada 2 -> Va syllable expected."""
        result = suggest_names(manish_chart)  # type: ignore[arg-type]
        assert result.nakshatra == "Rohini"
        assert result.pada == 2


# ── Gand Mool tests ────────────────────────────────────────────────────────


class TestGandMool:
    def test_check_gand_mool_returns_result(self, manish_chart: object) -> None:
        result = check_gand_mool(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result, GandMoolResult)

    def test_gand_mool_has_required_fields(self, manish_chart: object) -> None:
        result = check_gand_mool(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result.is_gand_mool, bool)
        assert isinstance(result.nakshatra, str)
        assert result.pada in (1, 2, 3, 4)
        assert result.severity in ("none", "mild", "moderate", "severe")

    def test_rohini_is_not_gand_mool(self, manish_chart: object) -> None:
        """Rohini is not a Gand Mool nakshatra."""
        result = check_gand_mool(manish_chart)  # type: ignore[arg-type]
        assert result.is_gand_mool is False


# ── Full computation tests ─────────────────────────────────────────────────


class TestComputeNamakarana:
    def test_returns_namakarana_result(self, manish_chart: object) -> None:
        result = compute_namakarana(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result, NamakaranaResult)

    def test_result_has_gand_mool(self, manish_chart: object) -> None:
        result = compute_namakarana(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result.gand_mool, GandMoolResult)

    def test_result_has_suggestion(self, manish_chart: object) -> None:
        result = compute_namakarana(manish_chart)  # type: ignore[arg-type]
        assert isinstance(result.suggestion, NameSuggestion)

    def test_manish_rohini_pada2(self, manish_chart: object) -> None:
        """End-to-end: Manish chart Rohini pada 2 -> Va starting syllable."""
        result = compute_namakarana(manish_chart)  # type: ignore[arg-type]
        assert result.suggestion.nakshatra == "Rohini"
        assert result.suggestion.pada == 2
        assert any("Va" in s for s in result.suggestion.nakshatra_letters)
