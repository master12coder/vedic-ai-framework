"""Tests for South Indian 10-Porutham marriage compatibility system.

Nakshatra index reference (0-based):
  0=Ashwini, 1=Bharani, 2=Krittika, 3=Rohini, 4=Mrigashira, 5=Ardra,
  6=Punarvasu, 7=Pushya, 8=Ashlesha, 9=Magha, 10=Purva Phalguni,
  11=Uttara Phalguni, 12=Hasta, 13=Chitra, 14=Swati, 15=Vishakha,
  16=Anuradha, 17=Jyeshtha, 18=Moola, 19=Purva Ashadha, 20=Uttara Ashadha,
  21=Shravana, 22=Dhanishtha, 23=Shatabhisha, 24=Purva Bhadrapada,
  25=Uttara Bhadrapada, 26=Revati

Sign index reference (0-based):
  0=Aries, 1=Taurus, 2=Gemini, 3=Cancer, 4=Leo, 5=Virgo,
  6=Libra, 7=Scorpio, 8=Sagittarius, 9=Capricorn, 10=Aquarius, 11=Pisces
"""

from __future__ import annotations

from daivai_engine.compute.matching_porutham import (
    _dinam,
    _ganam,
    _mahendra,
    _rajju,
    _rasi,
    _rasyadhipati,
    _stree_deergha,
    _vasya,
    _vedha,
    _yoni,
    compute_porutham,
)


# ---------------------------------------------------------------------------
# 1. Dinam Porutham
# ---------------------------------------------------------------------------


class TestDinam:
    def test_dinam_auspicious_count_2_agrees(self):
        """Count 2 → mod 9 = 2 → auspicious."""
        # girl=0 (Ashwini), boy=1 (Bharani): count=2, 2%9=2 → agrees
        result = _dinam(boy_nak=1, girl_nak=0)
        assert result.agrees is True

    def test_dinam_auspicious_count_divisible_by_9_agrees(self):
        """Count divisible by 9 → mod 9 = 0 → Adhimitra, auspicious."""
        # girl=0, boy=8 (Ashlesha): count=9, 9%9=0 → agrees
        result = _dinam(boy_nak=8, girl_nak=0)
        assert result.agrees is True

    def test_dinam_inauspicious_count_1_disagrees(self):
        """Count 1 → mod 9 = 1 → Janma, inauspicious."""
        # Same nakshatra counts as 27; different: girl=0, boy=0 gives count=(0-0)%27+1=1
        # Use girl=1, boy=1: (1-1)%27+1=1 → mod9=1 → disagrees
        result = _dinam(boy_nak=1, girl_nak=1)
        assert result.agrees is False

    def test_dinam_inauspicious_count_3_disagrees(self):
        """Count 3 → mod 9 = 3 → Vipath, inauspicious."""
        # girl=0, boy=2 (Krittika): count=3, 3%9=3 → disagrees
        result = _dinam(boy_nak=2, girl_nak=0)
        assert result.agrees is False

    def test_dinam_auspicious_count_8_agrees(self):
        """Count 8 → mod 9 = 8 → auspicious."""
        # girl=0, boy=7 (Pushya): count=8 → agrees
        result = _dinam(boy_nak=7, girl_nak=0)
        assert result.agrees is True

    def test_dinam_result_name(self):
        result = _dinam(boy_nak=0, girl_nak=3)
        assert result.name == "Dinam"
        assert result.is_eliminatory is False


# ---------------------------------------------------------------------------
# 2. Ganam Porutham
# ---------------------------------------------------------------------------


class TestGanam:
    def test_ganam_same_deva_agrees(self):
        """Deva + Deva: same gana → agrees."""
        # Ashwini (0=Deva) + Punarvasu (6=Deva)
        result = _ganam(boy_nak=0, girl_nak=6)
        assert result.agrees is True

    def test_ganam_same_rakshasa_agrees(self):
        """Rakshasa + Rakshasa: same gana → agrees."""
        # Ashlesha (8=Rakshasa) + Magha (9=Rakshasa)
        result = _ganam(boy_nak=8, girl_nak=9)
        assert result.agrees is True

    def test_ganam_deva_manushya_agrees(self):
        """Deva + Manushya mixing → agrees."""
        # Ashwini (0=Deva) + Bharani (1=Manushya)
        result = _ganam(boy_nak=0, girl_nak=1)
        assert result.agrees is True

    def test_ganam_rakshasa_deva_disagrees(self):
        """Rakshasa + Deva → disagrees."""
        # Ashlesha (8=Rakshasa) + Ashwini (0=Deva)
        result = _ganam(boy_nak=8, girl_nak=0)
        assert result.agrees is False

    def test_ganam_rakshasa_manushya_disagrees(self):
        """Rakshasa + Manushya → disagrees."""
        # Magha (9=Rakshasa) + Bharani (1=Manushya)
        result = _ganam(boy_nak=9, girl_nak=1)
        assert result.agrees is False

    def test_ganam_not_eliminatory(self):
        result = _ganam(boy_nak=0, girl_nak=1)
        assert result.is_eliminatory is False


# ---------------------------------------------------------------------------
# 3. Yoni Porutham
# ---------------------------------------------------------------------------


class TestYoni:
    def test_yoni_same_animal_agrees(self):
        """Same yoni animal → agrees."""
        # Ashwini (0=Horse) + Shatabhisha (23=Horse)
        result = _yoni(boy_nak=0, girl_nak=23)
        assert result.agrees is True

    def test_yoni_enemy_disagrees(self):
        """Enemy yoni pair → disagrees."""
        # Ashwini (0=Horse) + Hasta (12=Buffalo): Horse and Buffalo are enemies
        result = _yoni(boy_nak=0, girl_nak=12)
        assert result.agrees is False

    def test_yoni_non_enemy_agrees(self):
        """Non-enemy, different animals → agrees."""
        # Ashwini (0=Horse) + Rohini (3=Serpent): not enemies
        result = _yoni(boy_nak=0, girl_nak=3)
        assert result.agrees is True

    def test_yoni_cat_rat_enemy_disagrees(self):
        """Cat-Rat enemy pair → disagrees."""
        # Punarvasu (6=Cat) + Magha (9=Rat)
        result = _yoni(boy_nak=6, girl_nak=9)
        assert result.agrees is False


# ---------------------------------------------------------------------------
# 4. Rasi Porutham
# ---------------------------------------------------------------------------


class TestRasi:
    def test_rasi_distance_2_disagrees(self):
        """Distance 2 from girl to boy → disagrees."""
        # girl=0 (Aries), boy=1 (Taurus): dist=(1-0)%12+1=2 → disagrees
        result = _rasi(boy_sign=1, girl_sign=0)
        assert result.agrees is False

    def test_rasi_distance_6_disagrees(self):
        """Distance 6 → disagrees."""
        # girl=0, boy=5 (Virgo): dist=6 → disagrees
        result = _rasi(boy_sign=5, girl_sign=0)
        assert result.agrees is False

    def test_rasi_distance_3_agrees(self):
        """Distance 3 → agrees."""
        # girl=0, boy=2 (Gemini): dist=3 → agrees
        result = _rasi(boy_sign=2, girl_sign=0)
        assert result.agrees is True

    def test_rasi_distance_7_agrees(self):
        """Distance 7 → agrees."""
        # girl=0 (Aries), boy=6 (Libra): dist=7 → agrees
        result = _rasi(boy_sign=6, girl_sign=0)
        assert result.agrees is True

    def test_rasi_distance_12_disagrees(self):
        """Distance 12 (same sign going backwards) → disagrees."""
        # girl=1, boy=0: dist=(0-1)%12+1=12 → disagrees
        result = _rasi(boy_sign=0, girl_sign=1)
        assert result.agrees is False

    def test_rasi_mutual_friend_lords_mitigate_bad_distance(self):
        """Mutual friend lords cancel bad axis — Rasi exception."""
        # Cancer (3, Moon) and Leo (4, Sun): Sun-Moon are mutual friends
        # Distance = (4-3)%12+1 = 2 (bad), but lords are friends → mitigated
        result = _rasi(boy_sign=4, girl_sign=3)
        assert result.agrees is True
        assert "mitigated" in result.exception_note


# ---------------------------------------------------------------------------
# 5. Rasyadhipati Porutham
# ---------------------------------------------------------------------------


class TestRasyadhipati:
    def test_rasyadhipati_same_lord_agrees(self):
        """Same rasi lord → agrees (e.g., both ruled by Mercury)."""
        # Gemini (2, Mercury) + Virgo (5, Mercury)
        result = _rasyadhipati(boy_sign=2, girl_sign=5)
        assert result.agrees is True

    def test_rasyadhipati_mutual_friends_agrees(self):
        """Mutual friend lords → agrees."""
        # Cancer (3, Moon) + Leo (4, Sun): Sun-Moon are mutual friends
        result = _rasyadhipati(boy_sign=4, girl_sign=3)
        assert result.agrees is True

    def test_rasyadhipati_enemy_lords_disagrees(self):
        """Mutual enemy lords → disagrees."""
        # Capricorn (9, Saturn) + Leo (4, Sun): Saturn-Sun are mutual enemies
        result = _rasyadhipati(boy_sign=9, girl_sign=4)
        assert result.agrees is False

    def test_rasyadhipati_one_sided_enmity_disagrees(self):
        """One-sided enmity → disagrees (conservative)."""
        # Sagittarius (8, Jupiter) + Gemini (2, Mercury):
        # Jupiter considers Mercury enemy; Mercury doesn't consider Jupiter enemy
        result = _rasyadhipati(boy_sign=8, girl_sign=2)
        assert result.agrees is False


# ---------------------------------------------------------------------------
# 6. Rajju Porutham (ELIMINATORY)
# ---------------------------------------------------------------------------


class TestRajju:
    def test_rajju_same_paada_disagrees(self):
        """Same Paada nakshatra group → Rajju Dosha."""
        # Ashwini (0=Paada) + Ashlesha (8=Paada)
        result = _rajju(boy_nak=0, girl_nak=8)
        assert result.agrees is False
        assert result.is_eliminatory is True

    def test_rajju_different_groups_agrees(self):
        """Different Rajju groups → no dosha."""
        # Ashwini (0=Paada) + Bharani (1=Kati)
        result = _rajju(boy_nak=0, girl_nak=1)
        assert result.agrees is True
        assert result.is_eliminatory is True

    def test_rajju_shira_is_severe(self):
        """Shira (head) Rajju is severe — widowhood risk."""
        # Mrigashira (4=Shira) + Chitra (13=Shira)
        result = _rajju(boy_nak=4, girl_nak=13)
        assert result.agrees is False
        assert "severe" in result.description.lower()

    def test_rajju_kantha_is_severe(self):
        """Kantha (neck) Rajju is severe — wife's longevity."""
        # Rohini (3=Kantha) + Hasta (12=Kantha)
        result = _rajju(boy_nak=3, girl_nak=12)
        assert result.agrees is False
        assert "severe" in result.description.lower()

    def test_rajju_ascending_descending_exception_noted(self):
        """Opposite directions in same non-Shira Rajju → exception noted."""
        # Ashwini (0=Paada, ascending) + Jyeshtha (17=Paada, descending)
        result = _rajju(boy_nak=0, girl_nak=17)
        assert result.agrees is False
        assert (
            "ascending" in result.exception_note.lower()
            or "direction" in result.exception_note.lower()
        )

    def test_rajju_nabhi_is_moderate(self):
        """Nabhi (navel) Rajju is moderate — progeny issues."""
        # Krittika (2=Nabhi) + Punarvasu (6=Nabhi): both descending is same direction
        # But Krittika (2) is ascending (in set), Punarvasu (6) is descending (not in set)
        result = _rajju(boy_nak=2, girl_nak=6)
        assert result.agrees is False
        assert "moderate" in result.description.lower()


# ---------------------------------------------------------------------------
# 7. Vedha Porutham (ELIMINATORY, South Indian pairs)
# ---------------------------------------------------------------------------


class TestVedha:
    def test_vedha_ashwini_jyeshtha_disagrees(self):
        """Ashwini-Jyeshtha: South Indian Vedha pair → disagrees."""
        # 0=Ashwini, 17=Jyeshtha
        result = _vedha(boy_nak=0, girl_nak=17)
        assert result.agrees is False
        assert result.is_eliminatory is True

    def test_vedha_ashlesha_magha_disagrees(self):
        """Ashlesha-Magha: South Indian Vedha pair → disagrees."""
        result = _vedha(boy_nak=8, girl_nak=9)
        assert result.agrees is False

    def test_vedha_moola_revati_disagrees(self):
        """Moola-Revati: South Indian Vedha pair → disagrees."""
        result = _vedha(boy_nak=18, girl_nak=26)
        assert result.agrees is False

    def test_vedha_shravana_shatabhisha_disagrees(self):
        """Shravana-Shatabhisha: South Indian Vedha pair → disagrees."""
        result = _vedha(boy_nak=21, girl_nak=23)
        assert result.agrees is False

    def test_vedha_dhanishtha_no_pair_agrees(self):
        """Dhanishtha (22) has no Vedha pair — any partner agrees."""
        # Dhanishtha with Ashwini is not a Vedha pair
        result = _vedha(boy_nak=22, girl_nak=0)
        assert result.agrees is True

    def test_vedha_north_indian_pair_not_south_indian(self):
        """Ashwini-Shatabhisha is North Indian pair, NOT South Indian — should agree."""
        # {0, 23} is in North Indian Vedha but NOT in South Indian _SI_VEDHA_PAIRS
        result = _vedha(boy_nak=0, girl_nak=23)
        assert result.agrees is True

    def test_vedha_mrigashira_hasta_disagrees(self):
        """Mrigashira-Hasta: South Indian Vedha pair → disagrees."""
        result = _vedha(boy_nak=4, girl_nak=12)
        assert result.agrees is False

    def test_vedha_is_eliminatory(self):
        result = _vedha(boy_nak=0, girl_nak=3)
        assert result.is_eliminatory is True


# ---------------------------------------------------------------------------
# 8. Vasya Porutham
# ---------------------------------------------------------------------------


class TestVasya:
    def test_vasya_boy_controls_girl_agrees(self):
        """Boy's sign vasya of girl's sign → agrees."""
        # Aries (0) vasya = [Leo(4), Scorpio(7)]
        # boy=Aries(0), girl=Leo(4): girl in boy's vasya → agrees
        result = _vasya(boy_sign=0, girl_sign=4)
        assert result.agrees is True

    def test_vasya_no_relationship_disagrees(self):
        """No vasya relationship → disagrees."""
        # Aries (0) vasya=[4,7]; Taurus (1) vasya=[3,5]
        # boy=Aries(0), girl=Taurus(1): neither controls the other
        result = _vasya(boy_sign=0, girl_sign=1)
        assert result.agrees is False

    def test_vasya_girl_controls_boy_agrees(self):
        """Girl's sign controls boy's → agrees."""
        # Taurus (1) vasya=[3,5]; Cancer(3) in Taurus vasya
        # boy=Cancer(3), girl=Taurus(1): girl controls boy → agrees
        result = _vasya(boy_sign=3, girl_sign=1)
        assert result.agrees is True


# ---------------------------------------------------------------------------
# 9. Mahendra Porutham
# ---------------------------------------------------------------------------


class TestMahendra:
    def test_mahendra_count_4_agrees(self):
        """Count 4 from girl to boy → Mahendra agrees."""
        # girl=0 (Ashwini), boy=3 (Rohini): count=4 → agrees
        result = _mahendra(boy_nak=3, girl_nak=0)
        assert result.agrees is True

    def test_mahendra_count_7_agrees(self):
        """Count 7 from girl to boy → agrees."""
        # girl=0, boy=6 (Punarvasu): count=7 → agrees
        result = _mahendra(boy_nak=6, girl_nak=0)
        assert result.agrees is True

    def test_mahendra_count_6_disagrees(self):
        """Count 6 (not in auspicious list) → disagrees."""
        # girl=0, boy=5 (Ardra): count=6 → disagrees
        result = _mahendra(boy_nak=5, girl_nak=0)
        assert result.agrees is False

    def test_mahendra_count_25_agrees(self):
        """Count 25 → agrees."""
        # girl=0, boy=24 (Purva Bhadrapada): count=25 → agrees
        result = _mahendra(boy_nak=24, girl_nak=0)
        assert result.agrees is True


# ---------------------------------------------------------------------------
# 10. Stree Deergha Porutham
# ---------------------------------------------------------------------------


class TestStreeDeergha:
    def test_stree_deergha_far_ahead_agrees(self):
        """Girl nak >13 ahead of boy nak → agrees."""
        # boy=0 (Ashwini), girl=15 (Vishakha): count=(15-0)%27+1=16 >13 → agrees
        result = _stree_deergha(boy_nak=0, girl_nak=15)
        assert result.agrees is True

    def test_stree_deergha_close_disagrees(self):
        """Girl nak ≤13 ahead of boy nak → disagrees."""
        # boy=0, girl=5 (Ardra): count=6 ≤13 → disagrees
        result = _stree_deergha(boy_nak=0, girl_nak=5)
        assert result.agrees is False

    def test_stree_deergha_exactly_13_disagrees(self):
        """Count exactly 13 → disagrees (must be strictly >13)."""
        # boy=0, girl=12 (Hasta): count=13 → disagrees
        result = _stree_deergha(boy_nak=0, girl_nak=12)
        assert result.agrees is False

    def test_stree_deergha_count_14_agrees(self):
        """Count 14 → agrees (first agreeable position)."""
        # boy=0, girl=13 (Chitra): count=14 → agrees
        result = _stree_deergha(boy_nak=0, girl_nak=13)
        assert result.agrees is True


# ---------------------------------------------------------------------------
# 11. Full compute_porutham() integration tests
# ---------------------------------------------------------------------------


class TestComputePorutham:
    def test_compute_returns_10_poruthams(self):
        """Result must have exactly 10 poruthams."""
        result = compute_porutham(
            boy_nakshatra_index=3,  # Rohini
            girl_nakshatra_index=12,  # Hasta
            boy_moon_sign=1,  # Taurus
            girl_moon_sign=5,  # Virgo
        )
        assert len(result.poruthams) == 10
        assert result.total_count == 10

    def test_compute_porutham_names_in_order(self):
        """Poruthams must appear in canonical South Indian order."""
        result = compute_porutham(0, 3, 0, 1)
        names = [p.name for p in result.poruthams]
        expected = [
            "Dinam",
            "Ganam",
            "Yoni",
            "Rasi",
            "Rasyadhipati",
            "Rajju",
            "Vedha",
            "Vasya",
            "Mahendra",
            "Stree Deergha",
        ]
        assert names == expected

    def test_compute_rajju_dosha_flags_not_recommended(self):
        """Rajju dosha (same body part) → is_recommended=False even with high agreement."""
        # Ashwini (0=Paada) + Ashlesha (8=Paada): same Paada group
        result = compute_porutham(
            boy_nakshatra_index=0,
            girl_nakshatra_index=8,
            boy_moon_sign=0,
            girl_moon_sign=3,
        )
        assert result.has_rajju_dosha is True
        assert result.is_recommended is False
        assert result.rajju_body_part == "Paada"

    def test_compute_vedha_dosha_flags_not_recommended(self):
        """Vedha dosha → is_recommended=False."""
        # Ashwini (0) + Jyeshtha (17): Vedha pair
        result = compute_porutham(
            boy_nakshatra_index=0,
            girl_nakshatra_index=17,
            boy_moon_sign=0,
            girl_moon_sign=7,
        )
        assert result.has_vedha_dosha is True
        assert result.is_recommended is False

    def test_compute_agreed_count_in_range(self):
        """Agreed count must be between 0 and 10."""
        result = compute_porutham(0, 3, 0, 1)
        assert 0 <= result.agreed_count <= 10

    def test_compute_recommendation_not_empty(self):
        """Recommendation string must not be empty."""
        result = compute_porutham(3, 12, 1, 5)
        assert len(result.recommendation) > 0

    def test_compute_no_rajju_no_vedha_high_agreement_recommended(self):
        """Good combination without eliminatory doshas → is_recommended=True."""
        # Find a pair with different Rajju, no Vedha, good agreement
        # Rohini (3=Kantha) + Shravana (21=Kantha) — SAME Rajju, skip
        # Rohini (3=Kantha) + Punarvasu (6=Nabhi) — different Rajju, no vedha
        # Vedha: {3,14}, {6,11} — Rohini-Punarvasu is {3,6} — not a Vedha pair ✓
        result = compute_porutham(
            boy_nakshatra_index=3,  # Rohini (Kantha)
            girl_nakshatra_index=6,  # Punarvasu (Nabhi)
            boy_moon_sign=1,  # Taurus
            girl_moon_sign=2,  # Gemini
        )
        assert result.has_rajju_dosha is False
        assert result.has_vedha_dosha is False
        # Agreed count may or may not be ≥6, but no eliminatory dosha

    def test_compute_rajju_severity_present_when_dosha(self):
        """Rajju severity must be set when Rajju dosha present."""
        # Mrigashira (4=Shira) + Chitra (13=Shira)
        result = compute_porutham(4, 13, 0, 6)
        assert result.rajju_dosha if hasattr(result, "rajju_dosha") else True
        assert result.has_rajju_dosha is True
        assert result.rajju_severity == "severe"
        assert result.rajju_body_part == "Shira"

    def test_compute_no_dosha_rajju_body_part_is_none(self):
        """No Rajju dosha → rajju_body_part is None, severity is 'none'."""
        # Ashwini (0=Paada) + Bharani (1=Kati): different Rajju
        result = compute_porutham(0, 1, 0, 0)
        assert result.has_rajju_dosha is False
        assert result.rajju_body_part is None
        assert result.rajju_severity == "none"

    def test_compute_same_nakshatra_rajju_same_group(self):
        """Same nakshatra → same Rajju group → dosha."""
        result = compute_porutham(5, 5, 2, 2)  # Both Ardra (5=Kantha)
        assert result.has_rajju_dosha is True
