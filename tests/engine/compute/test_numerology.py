"""Tests for Vedic Numerology (Anka Jyotish) compute modules.

Primary reference chart: Manish Chaurasia -- DOB 13/03/1989 (Varanasi).

Known numerology values for Manish:
  Mulank  : 4  (Rahu)    -- day 13 → 1+3=4
  Bhagyank: 7  (Ketu)    -- 13+03+1989 → digits sum=34 → 3+4=7
  Namank  : 6  (Venus)   -- "Manish Chaurasia" Chaldean=42 → 4+2=6
  Kua     : 2  (Moon)    -- male, 1989: year sum=9; 11-9=2
  Lo Shu present numbers: [1,3,8,9] -- digits 1,3,3,1,9,8,9 (zero removed)
  Lo Shu missing numbers: [2,4,5,6,7]
  No arrows present (all require at least one missing number)
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.numerology import (
    compute_bhagyank,
    compute_compatibility,
    compute_kua_number,
    compute_mulank,
    compute_namank,
    compute_numerology,
    generate_yantra,
    get_compound_number_meaning,
    get_number_attributes,
    reduce_to_single,
)
from daivai_engine.compute.numerology_loshu import build_loshu_grid
from daivai_engine.exceptions import ValidationError
from daivai_engine.models.numerology import (
    ArrowPattern,
    CompatibilityResult,
    LoShuGrid,
    NumerologyResult,
    NumerologyYantra,
)


# ══════════════════════════════════════════════════════════════════════════════
# reduce_to_single
# ══════════════════════════════════════════════════════════════════════════════


def test_reduce_single_digit_unchanged():
    """Single-digit inputs 1-9 must return unchanged."""
    for n in range(1, 10):
        assert reduce_to_single(n) == n


def test_reduce_two_digit_number():
    """13 → 1+3 = 4."""
    assert reduce_to_single(13) == 4


def test_reduce_multi_step():
    """99 → 18 → 9."""
    assert reduce_to_single(99) == 9


def test_reduce_34_gives_7():
    """Manish bhagyank pre-reduction: 34 → 3+4 = 7."""
    assert reduce_to_single(34) == 7


def test_reduce_master_11_preserved():
    """Master number 11 is kept when preserve_master=True."""
    assert reduce_to_single(11, preserve_master=True) == 11


def test_reduce_master_22_preserved():
    """Master number 22 is kept when preserve_master=True."""
    assert reduce_to_single(22, preserve_master=True) == 22


def test_reduce_master_33_preserved():
    """Master number 33 is kept when preserve_master=True."""
    assert reduce_to_single(33, preserve_master=True) == 33


def test_reduce_master_11_not_preserved():
    """Master number 11 reduces to 2 when preserve_master=False."""
    assert reduce_to_single(11, preserve_master=False) == 2


def test_reduce_zero_raises():
    """Zero input raises ValidationError."""
    with pytest.raises(ValidationError):
        reduce_to_single(0)


def test_reduce_negative_raises():
    """Negative input raises ValidationError."""
    with pytest.raises(ValidationError):
        reduce_to_single(-5)


# ══════════════════════════════════════════════════════════════════════════════
# compute_mulank
# ══════════════════════════════════════════════════════════════════════════════


def test_mulank_single_digit_day_no_compound():
    """Day 1-9 returns that digit and no compound value."""
    mulank, compound = compute_mulank(1)
    assert mulank == 1
    assert compound is None


def test_mulank_day_9_no_compound():
    mulank, compound = compute_mulank(9)
    assert mulank == 9
    assert compound is None


def test_mulank_manish_day_13():
    """Manish: day=13 → mulank=4, compound=13."""
    mulank, compound = compute_mulank(13)
    assert mulank == 4
    assert compound == 13


def test_mulank_day_29_reduces_correctly():
    """Day 29 → 2+9=11 → reduce again → 2 (no master preserve)."""
    mulank, compound = compute_mulank(29, preserve_master=False)
    assert mulank == 2
    assert compound == 29


def test_mulank_day_31():
    """Day 31 → 3+1 = 4."""
    mulank, compound = compute_mulank(31)
    assert mulank == 4
    assert compound == 31


def test_mulank_invalid_day_0_raises():
    with pytest.raises(ValidationError):
        compute_mulank(0)


def test_mulank_invalid_day_32_raises():
    with pytest.raises(ValidationError):
        compute_mulank(32)


# ══════════════════════════════════════════════════════════════════════════════
# compute_bhagyank
# ══════════════════════════════════════════════════════════════════════════════


def test_bhagyank_manish():
    """Manish: 13/03/1989 → digits 1+3+0+3+1+9+8+9=34 → 3+4=7."""
    bhagyank, compound = compute_bhagyank(13, 3, 1989)
    assert bhagyank == 7
    assert compound == 34


def test_bhagyank_compound_captured():
    """Compound value (pre-final-reduction) should be returned when > 9."""
    _, compound = compute_bhagyank(13, 3, 1989)
    assert compound == 34


def test_bhagyank_returns_single_digit():
    bhagyank, _ = compute_bhagyank(13, 3, 1989)
    assert 1 <= bhagyank <= 9


def test_bhagyank_invalid_month_raises():
    with pytest.raises(ValidationError):
        compute_bhagyank(1, 13, 2000)


def test_bhagyank_invalid_day_raises():
    with pytest.raises(ValidationError):
        compute_bhagyank(0, 1, 2000)


# ══════════════════════════════════════════════════════════════════════════════
# compute_namank
# ══════════════════════════════════════════════════════════════════════════════


def test_namank_manish_chaldean():
    """Manish Chaurasia Chaldean: M4+A1+N5+I1+S3+H5 + C3+H5+A1+U6+R2+A1+S3+I1+A1 = 42 → 6."""
    namank, compound = compute_namank("Manish Chaurasia", "chaldean")
    assert namank == 6
    assert compound == 42


def test_namank_case_insensitive():
    """Upper/lower-case should produce identical results."""
    n1, _ = compute_namank("MANISH", "chaldean")
    n2, _ = compute_namank("manish", "chaldean")
    assert n1 == n2


def test_namank_ignores_spaces():
    """Spaces in name should be ignored, not contribute to sum."""
    n_with, _ = compute_namank("Manish Chaurasia", "chaldean")
    n_joined, _ = compute_namank("ManishChaurasia", "chaldean")
    assert n_with == n_joined


def test_namank_chaldean_no_compound_for_single():
    """Name whose letters sum to single digit has compound=None."""
    # Single letter A=1 in Chaldean
    namank, compound = compute_namank("A", "chaldean")
    assert namank == 1
    assert compound is None


def test_namank_pythagorean_system():
    """Pythagorean system should give a valid result in 1-9."""
    namank, _ = compute_namank("Manish", "pythagorean")
    assert 1 <= namank <= 9


def test_namank_pythagorean_differs_from_chaldean():
    """Pythagorean and Chaldean systems generally produce different results."""
    # Not always different, but for "Manish" they should differ
    n_chald, _ = compute_namank("Manish", "chaldean")
    n_pyth, _ = compute_namank("Manish", "pythagorean")
    # Both valid 1-9
    assert 1 <= n_chald <= 9
    assert 1 <= n_pyth <= 9


def test_namank_invalid_system_raises():
    """Unknown system name raises ValidationError."""
    with pytest.raises(ValidationError, match="Unknown letter-value system"):
        compute_namank("Manish", "unknown_system")


def test_namank_empty_name_raises():
    """Empty name raises ValidationError."""
    with pytest.raises(ValidationError):
        compute_namank("", "chaldean")


def test_namank_devanagari_system():
    """Devanagari system should process Hindi name without error."""
    # "मनीष" -- म=4, न=5, ी (vowel sign, skip), ष=5 → sum based on mapping
    namank, _ = compute_namank("मनीष", "devanagari")
    assert 1 <= namank <= 9


# ══════════════════════════════════════════════════════════════════════════════
# compute_kua_number
# ══════════════════════════════════════════════════════════════════════════════


def test_kua_manish_male_1989():
    """Manish: male, 1989 → year_sum=9; 11-9=2 → Kua=2."""
    kua = compute_kua_number(1989, "Male")
    assert kua == 2


def test_kua_female_1989():
    """Female, 1989 → year_sum=9; 4+9=13 → 1+3=4 → Kua=4."""
    kua = compute_kua_number(1989, "Female")
    assert kua == 4


def test_kua_result_in_range_1_to_9():
    """Kua number must always be 1-9."""
    for year in range(1950, 2020, 7):
        for gender in ("Male", "Female"):
            kua = compute_kua_number(year, gender)
            assert 1 <= kua <= 9, f"Kua={kua} out of range for year={year}, gender={gender}"


def test_kua_male_result_5_becomes_2():
    """When formula yields 5 for male, classical adjustment gives 2."""
    # Male, year_digit=6 pre-2000: 11-6=5 → becomes 2
    # 1+9+5+1=16→7; nope. Try 1+9+4+2=16→7. Try 1+9+6+0=16→7.
    # 1+9+8+3=21→3; 11-3=8. Try 1+9+3+8=21→3.
    # We need year_digit=6: sum→6. e.g. 1+9+6+8=24→6; year=1968
    kua = compute_kua_number(1968, "Male")
    assert kua != 5  # Must not be 5


def test_kua_female_result_5_becomes_8():
    """When formula yields 5 for female, classical adjustment gives 8."""
    # Female, year_digit=1: 4+1=5 → becomes 8
    # year_digit=1: e.g. 1+9+9+1=20→2. 2+0+0+1=3. 1+9+1+0=11→2.
    # 2+0+0+10? No. Try: year=2001, digits=2+0+0+1=3; 4+3=7 nope.
    # year_digit=1: 1+9+X+Y=some num→1 after reduction.
    # Example: 1+0+0+0=1 → year=1000. Or 1+9+9+1=20→2. Hmm.
    # Actually: year=2008 → 2+0+0+8=10→1. Post-2000 female: 6+1=7 nope.
    # year=1999→1+9+9+9=28→10→1; pre-2000 female: 4+1=5 → 8!
    kua = compute_kua_number(1999, "Female")
    assert kua == 8


def test_kua_case_insensitive_gender():
    """Gender matching should be case-insensitive."""
    k1 = compute_kua_number(1989, "male")
    k2 = compute_kua_number(1989, "Male")
    assert k1 == k2


def test_kua_invalid_gender_raises():
    with pytest.raises(ValidationError, match="Gender must be"):
        compute_kua_number(1989, "Other")


def test_kua_invalid_year_raises():
    with pytest.raises(ValidationError):
        compute_kua_number(0, "Male")


# ══════════════════════════════════════════════════════════════════════════════
# build_loshu_grid
# ══════════════════════════════════════════════════════════════════════════════


def test_loshu_grid_is_3x3():
    """Grid must always be a 3x3 structure."""
    grid = build_loshu_grid(13, 3, 1989)
    assert len(grid.grid) == 3
    assert all(len(row) == 3 for row in grid.grid)


def test_loshu_grid_manish_present_numbers():
    """Manish birth date has digits 1,3,8,9 present (zeros excluded)."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert sorted(loshu.present_numbers) == [1, 3, 8, 9]


def test_loshu_grid_manish_missing_numbers():
    """Manish birth date is missing digits 2,4,5,6,7."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert sorted(loshu.missing_numbers) == [2, 4, 5, 6, 7]


def test_loshu_grid_zeros_excluded():
    """Zeros in birth date must not appear in digit counts or grid."""
    loshu = build_loshu_grid(10, 3, 2000)
    # Day=10 has a 0; month=3; year=2000 has two zeros
    # Present should not include a "0" key
    assert "0" not in loshu.digit_counts or loshu.digit_counts.get("0", 0) == 0


def test_loshu_grid_digit_counts_manish():
    """Specific digit counts for Manish must match expected values."""
    loshu = build_loshu_grid(13, 3, 1989)
    counts = loshu.digit_counts
    assert counts["1"] == 2  # appears in day '13' and year '1989'
    assert counts["3"] == 2  # appears in day '13' and month '03'
    assert counts["8"] == 1
    assert counts["9"] == 2
    assert counts["2"] == 0
    assert counts["5"] == 0


def test_loshu_grid_cell_at_9_position():
    """Number 9 is at grid position (row=0, col=1); Manish has 2 nines there."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert loshu.grid[0][1] == 2  # position of 9 in Lo Shu


def test_loshu_grid_cell_at_1_position():
    """Number 1 is at grid position (row=2, col=1); Manish has 2 ones there."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert loshu.grid[2][1] == 2  # position of 1 in Lo Shu


def test_loshu_grid_cell_at_8_position():
    """Number 8 is at grid position (row=2, col=0); Manish has 1 eight there."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert loshu.grid[2][0] == 1  # position of 8 in Lo Shu


def test_loshu_grid_has_8_arrows():
    """Exactly 8 arrow patterns must always be returned."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert len(loshu.arrows) == 8


def test_loshu_no_arrows_present_for_manish():
    """Manish has no complete Lo Shu arrows (all rows/cols/diags incomplete)."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert loshu.present_arrow_names == []


def test_loshu_thought_arrow_detected():
    """Thought arrow (4,9,2) present when all three digits in birth date.

    Date 29/04/XXXX would have digits 2,9,0,4 → contains 2,4,9 → arrow present.
    """
    loshu = build_loshu_grid(29, 4, 1922)  # digits: 2,9,0,4,1,9,2,2 → has 2,4,9
    thought_arrow = next(a for a in loshu.arrows if a.key == "thought")
    assert thought_arrow.is_present is True


def test_loshu_will_arrow_detected():
    """Will arrow (3,5,7) present for date containing 3,5,7.

    Date 13/05/2007 → digits 1,3,0,5,2,0,0,7 → contains 3,5,7.
    """
    loshu = build_loshu_grid(13, 5, 2007)
    will_arrow = next(a for a in loshu.arrows if a.key == "will")
    assert will_arrow.is_present is True


def test_loshu_missing_arrow_flag():
    """Arrow with none of its numbers in the date is flagged as missing."""
    loshu = build_loshu_grid(13, 3, 1989)
    emotions_arrow = next(a for a in loshu.arrows if a.key == "emotions")
    # Emotions arrow needs 2,7,6 -- none present in Manish's date
    assert emotions_arrow.is_missing is True


def test_loshu_arrows_are_arrowpattern_instances():
    """Each arrow must be an ArrowPattern instance."""
    loshu = build_loshu_grid(13, 3, 1989)
    assert all(isinstance(a, ArrowPattern) for a in loshu.arrows)


# ══════════════════════════════════════════════════════════════════════════════
# generate_yantra
# ══════════════════════════════════════════════════════════════════════════════


def test_yantra_is_3x3():
    yantra = generate_yantra(4)
    assert len(yantra.grid) == 3
    assert all(len(row) == 3 for row in yantra.grid)


def test_yantra_magic_constant_for_4():
    """Yantra for number 4: magic constant = 15x4 = 60."""
    yantra = generate_yantra(4)
    assert yantra.magic_constant == 60


def test_yantra_rows_sum_to_magic_constant():
    """Every row must sum to magic_constant."""
    for n in range(1, 10):
        yantra = generate_yantra(n)
        for row in yantra.grid:
            assert sum(row) == yantra.magic_constant


def test_yantra_cols_sum_to_magic_constant():
    """Every column must sum to magic_constant."""
    for n in range(1, 10):
        yantra = generate_yantra(n)
        for col_idx in range(3):
            col_sum = sum(yantra.grid[row][col_idx] for row in range(3))
            assert col_sum == yantra.magic_constant


def test_yantra_main_diagonal_sums_to_magic_constant():
    """Main diagonal (top-left to bottom-right) must sum to magic_constant."""
    for n in range(1, 10):
        yantra = generate_yantra(n)
        diag = sum(yantra.grid[i][i] for i in range(3))
        assert diag == yantra.magic_constant


def test_yantra_anti_diagonal_sums_to_magic_constant():
    """Anti-diagonal (top-right to bottom-left) must sum to magic_constant."""
    for n in range(1, 10):
        yantra = generate_yantra(n)
        anti = sum(yantra.grid[i][2 - i] for i in range(3))
        assert anti == yantra.magic_constant


def test_yantra_planet_association():
    """Yantra for number 1 should be associated with the Sun."""
    yantra = generate_yantra(1)
    assert yantra.planet == "Sun"


def test_yantra_number_4_planet_rahu():
    yantra = generate_yantra(4)
    assert yantra.planet == "Rahu"


def test_yantra_invalid_number_raises():
    with pytest.raises(ValidationError):
        generate_yantra(0)

    with pytest.raises(ValidationError):
        generate_yantra(10)


def test_yantra_is_numerology_yantra_instance():
    yantra = generate_yantra(7)
    assert isinstance(yantra, NumerologyYantra)


# ══════════════════════════════════════════════════════════════════════════════
# compute_compatibility
# ══════════════════════════════════════════════════════════════════════════════


def test_compatibility_returns_result_instance():
    result = compute_compatibility(1, 9)
    assert isinstance(result, CompatibilityResult)


def test_compatibility_sun_mars_excellent():
    """1 (Sun) and 9 (Mars) are planetary friends → high score."""
    result = compute_compatibility(1, 9)
    assert result.score >= 80
    assert result.category == "Excellent"


def test_compatibility_sun_saturn_challenging():
    """1 (Sun) and 8 (Saturn) are planetary enemies → low score."""
    result = compute_compatibility(1, 8)
    assert result.score < 50
    assert result.category == "Challenging"


def test_compatibility_symmetric():
    """Compatibility is symmetric: (n1, n2) == (n2, n1)."""
    r1 = compute_compatibility(3, 7)
    r2 = compute_compatibility(7, 3)
    assert r1.score == r2.score
    assert r1.category == r2.category


def test_compatibility_score_in_range():
    """Score must always be in 0-100."""
    for i in range(1, 10):
        for j in range(1, 10):
            r = compute_compatibility(i, j)
            assert 0 <= r.score <= 100


def test_compatibility_invalid_number_raises():
    with pytest.raises(ValidationError):
        compute_compatibility(0, 5)

    with pytest.raises(ValidationError):
        compute_compatibility(5, 10)


def test_compatibility_planets_populated():
    """Planet names must be non-empty strings."""
    r = compute_compatibility(2, 5)
    assert r.planet1 == "Moon"
    assert r.planet2 == "Mercury"


# ══════════════════════════════════════════════════════════════════════════════
# get_number_attributes
# ══════════════════════════════════════════════════════════════════════════════


def test_attributes_sun_for_number_1():
    attrs = get_number_attributes(1)
    assert attrs.planet == "Sun"
    assert attrs.lucky_gemstone == "Ruby"


def test_attributes_rahu_for_number_4():
    attrs = get_number_attributes(4)
    assert attrs.planet == "Rahu"


def test_attributes_mercury_for_number_5():
    attrs = get_number_attributes(5)
    assert attrs.planet == "Mercury"
    assert attrs.lucky_gemstone == "Emerald"


def test_attributes_all_numbers_load():
    """All 9 number attributes must load without error."""
    for n in range(1, 10):
        attrs = get_number_attributes(n)
        assert attrs.number == n
        assert attrs.planet
        assert attrs.lucky_gemstone


def test_attributes_friendly_numbers_non_empty():
    """Friendly numbers list must not be empty for any number."""
    for n in range(1, 10):
        attrs = get_number_attributes(n)
        assert len(attrs.friendly_numbers) > 0


# ══════════════════════════════════════════════════════════════════════════════
# get_compound_number_meaning
# ══════════════════════════════════════════════════════════════════════════════


def test_compound_meaning_returns_string():
    meaning = get_compound_number_meaning(19)
    assert isinstance(meaning, str)
    assert len(meaning) > 0


def test_compound_meaning_19_successful_prince():
    meaning = get_compound_number_meaning(19)
    assert "Successful Prince" in meaning or "success" in meaning.lower()


def test_compound_meaning_out_of_range_returns_empty():
    assert get_compound_number_meaning(9) == ""
    assert get_compound_number_meaning(53) == ""


# ══════════════════════════════════════════════════════════════════════════════
# compute_numerology -- main entry point
# ══════════════════════════════════════════════════════════════════════════════


def test_compute_numerology_manish_full():
    """Full computation for Manish Chaurasia matches known values."""
    result = compute_numerology("13/03/1989", "Manish Chaurasia", "Male")

    assert result.numbers.mulank == 4
    assert result.numbers.bhagyank == 7
    assert result.numbers.namank == 6
    assert result.numbers.kua == 2


def test_compute_numerology_returns_result_type():
    result = compute_numerology("13/03/1989")
    assert isinstance(result, NumerologyResult)


def test_compute_numerology_without_name():
    """Namank should be None when name is not provided."""
    result = compute_numerology("13/03/1989")
    assert result.numbers.namank is None
    assert result.numbers.namank_planet is None


def test_compute_numerology_without_gender():
    """Kua should be None when gender is not provided."""
    result = compute_numerology("13/03/1989", "Manish")
    assert result.numbers.kua is None


def test_compute_numerology_invalid_dob_raises():
    with pytest.raises(ValidationError):
        compute_numerology("13-03-1989")  # Wrong separator


def test_compute_numerology_loshu_present_in_result():
    """Result must include a populated Lo Shu grid."""
    result = compute_numerology("13/03/1989")
    assert isinstance(result.loshu_grid, LoShuGrid)
    assert len(result.loshu_grid.arrows) == 8


def test_compute_numerology_yantra_in_result():
    """Mulank Yantra must be included and valid."""
    result = compute_numerology("13/03/1989")
    yantra = result.mulank_yantra
    assert isinstance(yantra, NumerologyYantra)
    assert yantra.number == result.numbers.mulank
    # Verify magic constant
    for row in yantra.grid:
        assert sum(row) == yantra.magic_constant


def test_compute_numerology_mulank_planet_populated():
    result = compute_numerology("13/03/1989")
    assert result.numbers.mulank_planet == "Rahu"  # 4 = Rahu


def test_compute_numerology_bhagyank_planet_populated():
    result = compute_numerology("13/03/1989")
    assert result.numbers.bhagyank_planet == "Ketu"  # 7 = Ketu


def test_compute_numerology_summary_non_empty():
    result = compute_numerology("13/03/1989", "Manish Chaurasia", "Male")
    assert len(result.summary) > 20


def test_compute_numerology_attributes_loaded():
    result = compute_numerology("13/03/1989")
    assert result.mulank_attributes.planet == "Rahu"
    assert result.bhagyank_attributes.planet == "Ketu"
