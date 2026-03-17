"""Tests for the Jaimini astrology system.

Covers Chara Karakas, Jaimini sign aspects, Arudha Padas, and Karakamsha.
"""

import pytest

from jyotish.compute.jaimini import (
    CHARA_KARAKA_PLANETS,
    DUAL_SIGNS,
    FIXED_SIGNS,
    KARAKA_NAMES,
    MOVABLE_SIGNS,
    NUM_SIGNS,
    compute_arudha_padas,
    compute_chara_karakas,
    compute_jaimini,
    compute_karakamsha,
    get_jaimini_aspects,
)
from jyotish.domain.models.jaimini import JaiminiResult


class TestCharaKarakas:
    """Tests for Chara Karaka computation."""

    def test_returns_seven_karakas(self, manish_chart):
        """Chara karaka computation should return exactly 7 karakas."""
        karakas = compute_chara_karakas(manish_chart)
        assert len(karakas) == 7

    def test_karaka_ordering_by_degree(self, manish_chart):
        """Karakas should be sorted by degree in sign, descending."""
        karakas = compute_chara_karakas(manish_chart)
        degrees = [k.degree_in_sign for k in karakas]
        assert degrees == sorted(degrees, reverse=True), (
            f"Karakas not in descending degree order: {degrees}"
        )

    def test_first_is_atmakaraka_last_is_darakaraka(self, manish_chart):
        """First karaka must be AK (Atmakaraka), last must be DK (Darakaraka)."""
        karakas = compute_chara_karakas(manish_chart)
        assert karakas[0].karaka == "AK"
        assert karakas[0].karaka_full == "Atmakaraka"
        assert karakas[-1].karaka == "DK"
        assert karakas[-1].karaka_full == "Darakaraka"

    def test_all_seven_planets_represented(self, manish_chart):
        """All 7 eligible planets should appear exactly once."""
        karakas = compute_chara_karakas(manish_chart)
        planet_names = {k.planet for k in karakas}
        assert planet_names == set(CHARA_KARAKA_PLANETS)

    def test_no_rahu_ketu_in_karakas(self, manish_chart):
        """Rahu and Ketu must not appear in the 7-karaka scheme."""
        karakas = compute_chara_karakas(manish_chart)
        for k in karakas:
            assert k.planet not in ("Rahu", "Ketu"), (
                f"Node {k.planet} found in Chara Karakas"
            )

    def test_karaka_names_complete(self, manish_chart):
        """All 7 karaka abbreviations should be present in order."""
        karakas = compute_chara_karakas(manish_chart)
        names = [k.karaka for k in karakas]
        assert names == KARAKA_NAMES

    def test_hindi_names_populated(self, manish_chart):
        """Each karaka should have a non-empty Hindi name."""
        karakas = compute_chara_karakas(manish_chart)
        for k in karakas:
            assert k.karaka_hi, f"Empty Hindi name for {k.karaka}"


class TestJaiminiAspects:
    """Tests for Jaimini sign-based aspects."""

    def test_movable_sign_aspects_three_fixed(self):
        """Movable signs should aspect exactly 3 fixed signs."""
        for sign in MOVABLE_SIGNS:
            aspects = get_jaimini_aspects(sign)
            assert len(aspects) == 3, (
                f"Movable sign {sign} aspects {len(aspects)} signs, expected 3"
            )
            for aspected in aspects:
                assert aspected in FIXED_SIGNS, (
                    f"Movable sign {sign} aspects non-fixed sign {aspected}"
                )

    def test_fixed_sign_aspects_three_movable(self):
        """Fixed signs should aspect exactly 3 movable signs."""
        for sign in FIXED_SIGNS:
            aspects = get_jaimini_aspects(sign)
            assert len(aspects) == 3, (
                f"Fixed sign {sign} aspects {len(aspects)} signs, expected 3"
            )
            for aspected in aspects:
                assert aspected in MOVABLE_SIGNS, (
                    f"Fixed sign {sign} aspects non-movable sign {aspected}"
                )

    def test_dual_sign_aspects_three_dual(self):
        """Dual signs should aspect exactly 3 other dual signs."""
        for sign in DUAL_SIGNS:
            aspects = get_jaimini_aspects(sign)
            assert len(aspects) == 3, (
                f"Dual sign {sign} aspects {len(aspects)} signs, expected 3"
            )
            for aspected in aspects:
                assert aspected in DUAL_SIGNS, (
                    f"Dual sign {sign} aspects non-dual sign {aspected}"
                )
            assert sign not in aspects, (
                f"Dual sign {sign} should not aspect itself"
            )

    def test_movable_excludes_adjacent_fixed(self):
        """Movable sign must not aspect the fixed sign adjacent (next) to it.

        Aries(0) excludes Taurus(1), Cancer(3) excludes Leo(4),
        Libra(6) excludes Scorpio(7), Capricorn(9) excludes Aquarius(10).
        """
        expected_exclusions = {0: 1, 3: 4, 6: 7, 9: 10}
        for sign, excluded in expected_exclusions.items():
            aspects = get_jaimini_aspects(sign)
            assert excluded not in aspects, (
                f"Movable sign {sign} should not aspect adjacent fixed sign {excluded}"
            )

    def test_fixed_excludes_adjacent_movable(self):
        """Fixed sign must not aspect the movable sign adjacent (previous) to it.

        Taurus(1) excludes Aries(0), Leo(4) excludes Cancer(3),
        Scorpio(7) excludes Libra(6), Aquarius(10) excludes Capricorn(9).
        """
        expected_exclusions = {1: 0, 4: 3, 7: 6, 10: 9}
        for sign, excluded in expected_exclusions.items():
            aspects = get_jaimini_aspects(sign)
            assert excluded not in aspects, (
                f"Fixed sign {sign} should not aspect adjacent movable sign {excluded}"
            )

    def test_invalid_sign_raises(self):
        """Invalid sign index should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid sign index"):
            get_jaimini_aspects(-1)
        with pytest.raises(ValueError, match="Invalid sign index"):
            get_jaimini_aspects(12)

    def test_aries_aspects_specific(self):
        """Aries(0) should aspect Leo(4), Scorpio(7), Aquarius(10)."""
        aspects = get_jaimini_aspects(0)
        assert sorted(aspects) == [4, 7, 10]

    def test_taurus_aspects_specific(self):
        """Taurus(1) should aspect Cancer(3), Libra(6), Capricorn(9)."""
        aspects = get_jaimini_aspects(1)
        assert sorted(aspects) == [3, 6, 9]

    def test_gemini_aspects_specific(self):
        """Gemini(2) should aspect Virgo(5), Sagittarius(8), Pisces(11)."""
        aspects = get_jaimini_aspects(2)
        assert sorted(aspects) == [5, 8, 11]


class TestArudhaPadas:
    """Tests for Arudha Pada computation."""

    def test_returns_twelve_padas(self, manish_chart):
        """Should return exactly 12 Arudha Padas (A1-A12)."""
        padas = compute_arudha_padas(manish_chart)
        assert len(padas) == 12

    def test_pada_names_sequential(self, manish_chart):
        """Padas should be named A1 through A12 in order."""
        padas = compute_arudha_padas(manish_chart)
        for i, pada in enumerate(padas, start=1):
            assert pada.house == i
            assert pada.name == f"A{i}"

    def test_pada_sign_indices_valid(self, manish_chart):
        """All Arudha sign indices should be in 0-11 range."""
        padas = compute_arudha_padas(manish_chart)
        for pada in padas:
            assert 0 <= pada.sign_index < NUM_SIGNS, (
                f"{pada.name} has invalid sign index {pada.sign_index}"
            )

    def test_pada_sign_names_match_indices(self, manish_chart):
        """Pada sign name should correspond to its sign index."""
        from jyotish.utils.constants import SIGNS
        padas = compute_arudha_padas(manish_chart)
        for pada in padas:
            assert pada.sign == SIGNS[pada.sign_index], (
                f"{pada.name}: sign '{pada.sign}' doesn't match index {pada.sign_index}"
            )

    def test_arudha_not_in_own_house_or_seventh(self, manish_chart):
        """No Arudha should fall in its own house sign or 7th from it.

        The Arudha algorithm has an exception rule to prevent this.
        """
        padas = compute_arudha_padas(manish_chart)
        for pada in padas:
            house_sign = (manish_chart.lagna_sign_index + pada.house - 1) % NUM_SIGNS
            seventh_sign = (house_sign + 6) % NUM_SIGNS
            assert pada.sign_index != house_sign, (
                f"{pada.name} falls in its own house sign {house_sign}"
            )
            assert pada.sign_index != seventh_sign, (
                f"{pada.name} falls in 7th from house sign {seventh_sign}"
            )


class TestKarakamsha:
    """Tests for Karakamsha computation."""

    def test_karakamsha_valid_sign(self, manish_chart):
        """Karakamsha should be a valid sign index (0-11)."""
        km = compute_karakamsha(manish_chart)
        assert 0 <= km < NUM_SIGNS

    def test_karakamsha_is_navamsha_of_atmakaraka(self, manish_chart):
        """Karakamsha should equal the Navamsha sign of the Atmakaraka."""
        from jyotish.compute.divisional import compute_navamsha_sign

        karakas = compute_chara_karakas(manish_chart)
        ak_planet = karakas[0].planet
        ak_longitude = manish_chart.planets[ak_planet].longitude
        expected = compute_navamsha_sign(ak_longitude)

        km = compute_karakamsha(manish_chart)
        assert km == expected


class TestJaiminiResult:
    """Tests for the full Jaimini analysis."""

    def test_compute_jaimini_returns_complete_result(self, manish_chart):
        """Full Jaimini computation should return a JaiminiResult with all fields."""
        result = compute_jaimini(manish_chart)
        assert isinstance(result, JaiminiResult)
        assert len(result.chara_karakas) == 7
        assert len(result.arudha_padas) == 12
        assert 0 <= result.karakamsha_sign_index < NUM_SIGNS
        assert result.karakamsha_sign != ""
        assert result.atmakaraka in CHARA_KARAKA_PLANETS
        assert result.darakaraka in CHARA_KARAKA_PLANETS
        assert result.atmakaraka != result.darakaraka

    def test_ak_dk_match_karakas(self, manish_chart):
        """Atmakaraka and Darakaraka in result should match the karaka list."""
        result = compute_jaimini(manish_chart)
        assert result.atmakaraka == result.chara_karakas[0].planet
        assert result.darakaraka == result.chara_karakas[-1].planet
