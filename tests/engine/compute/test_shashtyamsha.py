"""Tests for D60 Shashtyamsha deity analysis.

Fixture: manish_chart (Manish Chaurasia, 13/03/1989, 12:17, Varanasi)
  Lagna: Mithuna (Gemini, index 2) — odd sign → forward deity order
  Moon: Rohini Pada 2
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.shashtyamsha_analysis import (
    _get_deity_for_part,
    _load_deities,
    analyze_d60_chart,
    compare_d1_d60,
    get_d60_position,
)
from daivai_engine.constants import PLANETS
from daivai_engine.models.shashtyamsha import (
    D1D60ComparisonResult,
    D60Analysis,
    ShashtyamshaDeity,
    ShashtyamshaPosition,
)


# ── Deity data integrity ──────────────────────────────────────────────────────


class TestShashtyamshaDeityData:
    def test_exactly_60_deities_loaded(self):
        deities = _load_deities()
        assert len(deities) == 60

    def test_deity_numbers_are_1_to_60(self):
        deities = _load_deities()
        numbers = [d.number for d in deities]
        assert numbers == list(range(1, 61))

    def test_all_natures_valid(self):
        valid = {"Saumya", "Krura", "Mishra"}
        for deity in _load_deities():
            assert deity.nature in valid, (
                f"Deity {deity.number} ({deity.name}) has invalid nature: {deity.nature}"
            )

    def test_all_elements_valid(self):
        valid = {"Fire", "Water", "Air", "Earth", "Akasha"}
        for deity in _load_deities():
            assert deity.element in valid, (
                f"Deity {deity.number} ({deity.name}) has invalid element: {deity.element}"
            )

    def test_all_deities_have_signification(self):
        for deity in _load_deities():
            assert deity.signification.strip(), (
                f"Deity {deity.number} ({deity.name}) has empty signification"
            )

    def test_known_deity_1_is_ghora_krura(self):
        """BPHS Ch.6: first deity for odd signs is Ghora (malefic)."""
        deity = _load_deities()[0]
        assert deity.name == "Ghora"
        assert deity.nature == "Krura"

    def test_known_deity_3_is_deva_saumya(self):
        deity = _load_deities()[2]
        assert deity.name == "Deva"
        assert deity.nature == "Saumya"

    def test_known_deity_23_is_vishnu_saumya(self):
        deity = _load_deities()[22]
        assert deity.name == "Vishnu"
        assert deity.nature == "Saumya"

    def test_known_deity_60_is_chandrarekha_saumya(self):
        deity = _load_deities()[59]
        assert deity.name == "Chandrarekha"
        assert deity.nature == "Saumya"

    def test_known_deity_59_is_bhramana_mishra(self):
        deity = _load_deities()[58]
        assert deity.name == "Bhramana"
        assert deity.nature == "Mishra"

    def test_mishra_deities_are_11_and_59(self):
        """Only deities 11 (Maya) and 59 (Bhramana) are Mishra per BPHS."""
        mishra = [d for d in _load_deities() if d.nature == "Mishra"]
        assert len(mishra) == 2
        assert {d.number for d in mishra} == {11, 59}


# ── Odd/Even sign reversal ────────────────────────────────────────────────────


class TestOddEvenSignRule:
    def test_odd_sign_part0_gives_deity1(self):
        """Mesha (index 0, odd sign): part 0 → deity 1 (Ghora)."""
        deity = _get_deity_for_part(sign_index=0, part=0)
        assert deity.number == 1
        assert deity.name == "Ghora"

    def test_odd_sign_part59_gives_deity60(self):
        """Mesha (index 0): part 59 → deity 60 (Chandrarekha)."""
        deity = _get_deity_for_part(sign_index=0, part=59)
        assert deity.number == 60
        assert deity.name == "Chandrarekha"

    def test_even_sign_part0_gives_deity60(self):
        """Vrishabha (index 1, even sign): part 0 → deity 60 (reversed)."""
        deity = _get_deity_for_part(sign_index=1, part=0)
        assert deity.number == 60
        assert deity.name == "Chandrarekha"

    def test_even_sign_part59_gives_deity1(self):
        """Vrishabha (index 1): part 59 → deity 1 (reversed)."""
        deity = _get_deity_for_part(sign_index=1, part=59)
        assert deity.number == 1
        assert deity.name == "Ghora"

    def test_gemini_odd_sign_forward(self):
        """Mithuna (index 2, odd sign): forward order."""
        deity = _get_deity_for_part(sign_index=2, part=0)
        assert deity.number == 1  # Ghora

    def test_cancer_even_sign_reversed(self):
        """Karka (index 3, even sign): reversed order."""
        deity = _get_deity_for_part(sign_index=3, part=0)
        assert deity.number == 60  # Chandrarekha

    @pytest.mark.parametrize("sign_index", [0, 2, 4, 6, 8, 10])
    def test_all_odd_signs_forward_at_part0(self, sign_index: int):
        """All odd signs (even 0-index) use forward order."""
        deity = _get_deity_for_part(sign_index=sign_index, part=0)
        assert deity.number == 1, f"Sign {sign_index}: expected deity 1, got {deity.number}"

    @pytest.mark.parametrize("sign_index", [1, 3, 5, 7, 9, 11])
    def test_all_even_signs_reversed_at_part0(self, sign_index: int):
        """All even signs (odd 0-index) use reversed order."""
        deity = _get_deity_for_part(sign_index=sign_index, part=0)
        assert deity.number == 60, f"Sign {sign_index}: expected deity 60, got {deity.number}"


# ── get_d60_position ──────────────────────────────────────────────────────────


class TestGetD60Position:
    def test_returns_shashtyamsha_position(self):
        pos = get_d60_position(planet_longitude=45.0, planet_name="Sun")
        assert isinstance(pos, ShashtyamshaPosition)

    def test_d60_sign_in_valid_range(self):
        for lon in [0.0, 30.0, 90.5, 180.25, 270.75, 359.9]:
            pos = get_d60_position(lon)
            assert 0 <= pos.d60_sign_index <= 11, (
                f"D60 sign out of range for longitude {lon}: {pos.d60_sign_index}"
            )

    def test_part_in_valid_range(self):
        for lon in [0.0, 15.0, 29.9, 30.0, 90.0, 180.0, 359.9]:
            pos = get_d60_position(lon)
            assert 0 <= pos.part <= 59, f"Part out of range for {lon}: {pos.part}"

    def test_vargottam_when_d1_equals_d60_sign(self):
        """Longitude 0° (Aries, part 0) → D60 sign = (0 + 0) % 12 = Aries = vargottam."""
        pos = get_d60_position(0.0)
        assert pos.d1_sign_index == 0  # Aries
        # vargottam only when d1_sign == d60_sign
        assert pos.is_vargottam == (pos.d1_sign_index == pos.d60_sign_index)

    def test_planet_name_stored(self):
        pos = get_d60_position(120.0, "Jupiter")
        assert pos.planet == "Jupiter"

    def test_deity_is_shashtyamsha_deity(self):
        pos = get_d60_position(0.0)
        assert isinstance(pos.deity, ShashtyamshaDeity)

    def test_longitude_at_sign_boundary(self):
        """Exactly at 30° boundary = start of Taurus."""
        pos = get_d60_position(30.0)
        assert pos.d1_sign_index == 1  # Taurus

    def test_d60_lord_is_valid_planet(self):
        valid_lords = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        pos = get_d60_position(45.0)
        assert pos.d60_lord in valid_lords

    def test_first_part_of_aries_is_ghora(self):
        """Aries 0-0.5° = part 0, odd sign → deity 1 = Ghora."""
        pos = get_d60_position(0.1)
        assert pos.deity.name == "Ghora"
        assert pos.deity.nature == "Krura"

    def test_third_part_of_aries_is_deva(self):
        """Aries 1.0-1.5° = part 2, odd sign → deity 3 = Deva (Saumya)."""
        pos = get_d60_position(1.1)
        assert pos.deity.name == "Deva"
        assert pos.deity.nature == "Saumya"


# ── analyze_d60_chart ─────────────────────────────────────────────────────────


class TestAnalyzeD60Chart:
    def test_returns_d60_analysis(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        assert isinstance(result, D60Analysis)

    def test_all_9_planets_present(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        planet_names = [pos.planet for pos in result.planets]
        for planet in PLANETS:
            assert planet in planet_names

    def test_every_planet_has_valid_deity(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        for pos in result.planets:
            assert isinstance(pos.deity, ShashtyamshaDeity)
            assert 1 <= pos.deity.number <= 60

    def test_benefic_malefic_mixed_partition(self, manish_chart):
        """Every planet must appear in exactly one classification bucket."""
        result = analyze_d60_chart(manish_chart)
        all_classified = (
            set(result.benefic_planets) | set(result.malefic_planets) | set(result.mixed_planets)
        )
        assert all_classified == set(PLANETS)

    def test_no_duplicate_classification(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        all_classified = result.benefic_planets + result.malefic_planets + result.mixed_planets
        assert len(all_classified) == len(set(all_classified))

    def test_vargottam_subset_of_planets(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        for planet in result.vargottam_planets:
            assert planet in PLANETS

    def test_key_findings_non_empty(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        assert len(result.key_findings) > 0

    def test_all_d60_signs_valid(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        for pos in result.planets:
            assert 0 <= pos.d60_sign_index <= 11

    def test_all_parts_valid(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        for pos in result.planets:
            assert 0 <= pos.part <= 59


# ── compare_d1_d60 ────────────────────────────────────────────────────────────


class TestCompareD1D60:
    def test_returns_comparison_result(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        assert isinstance(result, D1D60ComparisonResult)

    def test_all_9_planets_compared(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        compared_planets = [c.planet for c in result.comparisons]
        for planet in PLANETS:
            assert planet in compared_planets

    def test_every_planet_in_exactly_one_bucket(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        all_bucketed = result.certain_benefics + result.certain_malefics + result.conflicting
        assert set(all_bucketed) == set(PLANETS)

    def test_no_duplicate_in_buckets(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        all_bucketed = result.certain_benefics + result.certain_malefics + result.conflicting
        assert len(all_bucketed) == len(set(all_bucketed))

    def test_certainty_values_valid(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        for comp in result.comparisons:
            assert comp.certainty in {"certain", "uncertain"}, (
                f"{comp.planet}: invalid certainty '{comp.certainty}'"
            )

    def test_d1_assessments_valid(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        for comp in result.comparisons:
            assert comp.d1_assessment in {"benefic", "malefic", "neutral"}, (
                f"{comp.planet}: invalid d1_assessment '{comp.d1_assessment}'"
            )

    def test_d60_assessments_valid(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        for comp in result.comparisons:
            assert comp.d60_assessment in {"Saumya", "Krura", "Mishra"}, (
                f"{comp.planet}: invalid d60_assessment '{comp.d60_assessment}'"
            )

    def test_agreement_consistent_with_buckets(self, manish_chart):
        """Planets in certain_benefics/malefics must have agreement=True."""
        result = compare_d1_d60(manish_chart)
        certain = set(result.certain_benefics) | set(result.certain_malefics)
        for comp in result.comparisons:
            if comp.planet in certain:
                assert comp.agreement is True
            elif comp.planet in result.conflicting:
                assert comp.agreement is False

    def test_summary_non_empty(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        assert result.summary.strip()

    def test_interpretation_non_empty(self, manish_chart):
        result = compare_d1_d60(manish_chart)
        for comp in result.comparisons:
            assert comp.interpretation.strip()


# ── Integration: Manish chart specific checks ─────────────────────────────────


class TestManishChartD60:
    @pytest.mark.safety
    def test_lagna_is_mithuna_odd_sign(self, manish_chart):
        """Manish lagna is Mithuna (index 2) — odd sign uses forward deity order."""
        assert manish_chart.lagna_sign_index == 2

    def test_d60_analysis_produces_9_planets(self, manish_chart):
        result = analyze_d60_chart(manish_chart)
        assert len(result.planets) == 9

    def test_each_planet_deity_nature_matches_bucket(self, manish_chart):
        """Cross-check that each planet's bucket matches its deity nature."""
        result = analyze_d60_chart(manish_chart)
        pos_map = {pos.planet: pos for pos in result.planets}
        for planet in result.benefic_planets:
            assert pos_map[planet].deity.nature == "Saumya"
        for planet in result.malefic_planets:
            assert pos_map[planet].deity.nature == "Krura"
        for planet in result.mixed_planets:
            assert pos_map[planet].deity.nature == "Mishra"

    def test_d60_lord_matches_sign_lords_constant(self, manish_chart):
        """D60 lord must match SIGN_LORDS for the D60 sign."""
        from daivai_engine.constants import SIGN_LORDS

        result = analyze_d60_chart(manish_chart)
        for pos in result.planets:
            expected_lord = SIGN_LORDS[pos.d60_sign_index]
            assert pos.d60_lord == expected_lord, (
                f"{pos.planet}: d60_lord={pos.d60_lord} "
                f"but SIGN_LORDS[{pos.d60_sign_index}]={expected_lord}"
            )
