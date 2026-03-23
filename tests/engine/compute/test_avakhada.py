"""Tests for Avakhada Chakra computation.

Primary fixture: manish_chart (Manish Chaurasia — verified reference chart).
  DOB: 13/03/1989  TOB: 12:17  Place: Varanasi
  Lagna: Mithuna (Gemini)   Moon: Rohini Pada 2

Expected Avakhada values (cross-verified with InstaAstro):
  nakshatra      = Rohini         nakshatra_lord  = Moon
  sign           = Vrishabha      sign_lord       = Venus
  charan         = 2              tatva           = Earth   ✓ InstaAstro
  paya           = Iron           ✓ InstaAstro
  yunja          = Poorva         (Rohini = nakshatra 4, in range 1-9)
  gan            = Manushya       (Rohini's gana)
  nadi           = Madhya         (Rohini's nadi per NAKSHATRA_NADIS)
  yoni           = Serpent        (Rohini's animal)
  varna          = Vaishya        (Taurus = Earth sign → Vaishya)
  vashya         = Chatushpad     (Taurus → four-legged)
  ascendant      = Mithuna        ascendant_lord  = Mercury
  name_alphabet  = Va             (Rohini pada 2)
"""

from __future__ import annotations

from daivai_engine.compute.avakhada import (
    _paya,
    _tatva,
    _yunja,
    compute_avakhada,
)
from daivai_engine.models.avakhada import AvakhadaChakra


# ---------------------------------------------------------------------------
# Unit tests for pure helper functions (no chart needed)
# ---------------------------------------------------------------------------


class TestPayaHelper:
    """Paya is nakshatra_number % 4 mapped to Gold/Silver/Copper/Iron."""

    def test_rohini_iron(self):
        """Rohini = nakshatra 4, 4 % 4 = 0 → Iron. Verified by InstaAstro."""
        assert _paya(4) == "Iron"

    def test_ashwini_gold(self):
        assert _paya(1) == "Gold"

    def test_bharani_silver(self):
        assert _paya(2) == "Silver"

    def test_krittika_copper(self):
        assert _paya(3) == "Copper"

    def test_cycle_repeats_correctly(self):
        """Cycle repeats every 4 nakshatras."""
        assert _paya(5) == "Gold"  # Mrigashira = 5, 5%4=1
        assert _paya(6) == "Silver"  # Ardra = 6, 6%4=2
        assert _paya(7) == "Copper"  # Punarvasu = 7, 7%4=3
        assert _paya(8) == "Iron"  # Pushya = 8, 8%4=0

    def test_all_27_nakshatras_return_valid_metal(self):
        valid = {"Gold", "Silver", "Copper", "Iron"}
        for n in range(1, 28):
            result = _paya(n)
            assert result in valid, f"nakshatra {n} returned invalid paya: {result}"


class TestTatvaHelper:
    """Tatva is strictly determined by pada (1-4)."""

    def test_pada_1_fire(self):
        assert _tatva(1) == "Fire"

    def test_pada_2_earth(self):
        """Rohini Pada 2 → Earth. Verified by InstaAstro."""
        assert _tatva(2) == "Earth"

    def test_pada_3_air(self):
        assert _tatva(3) == "Air"

    def test_pada_4_water(self):
        assert _tatva(4) == "Water"


class TestYunjaHelper:
    """Yunja divides 27 nakshatras into three groups of 9."""

    def test_poorva_range(self):
        for n in range(1, 10):
            assert _yunja(n) == "Poorva", f"nakshatra {n} should be Poorva"

    def test_madhya_range(self):
        for n in range(10, 19):
            assert _yunja(n) == "Madhya", f"nakshatra {n} should be Madhya"

    def test_uttara_range(self):
        for n in range(19, 28):
            assert _yunja(n) == "Uttara", f"nakshatra {n} should be Uttara"

    def test_rohini_poorva(self):
        """Rohini = nakshatra 4 → Poorva."""
        assert _yunja(4) == "Poorva"

    def test_boundaries(self):
        assert _yunja(9) == "Poorva"  # last in group 1
        assert _yunja(10) == "Madhya"  # first in group 2
        assert _yunja(18) == "Madhya"  # last in group 2
        assert _yunja(19) == "Uttara"  # first in group 3
        assert _yunja(27) == "Uttara"  # last in group 3


# ---------------------------------------------------------------------------
# Integration tests using the Manish reference chart
# ---------------------------------------------------------------------------


class TestComputeAvakhada:
    """Full compute_avakhada integration tests against the reference chart."""

    def test_returns_avakhada_chakra(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert isinstance(result, AvakhadaChakra)

    # Moon nakshatra data
    def test_nakshatra_rohini(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.nakshatra == "Rohini"

    def test_nakshatra_lord_moon(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.nakshatra_lord == "Moon"

    def test_nakshatra_number_four(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.nakshatra_number == 4

    # Moon sign data
    def test_sign_vrishabha(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.sign == "Vrishabha"

    def test_sign_lord_venus(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.sign_lord == "Venus"

    # Pada
    def test_charan_two(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.charan == 2

    # Tatva — Earth verified by InstaAstro
    def test_tatva_earth(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.tatva == "Earth"

    # Paya — Iron verified by InstaAstro
    def test_paya_iron(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.paya == "Iron"

    # Yunja
    def test_yunja_poorva(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.yunja == "Poorva"

    # Nakshatra-based qualities
    def test_gan_manushya(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.gan == "Manushya"

    def test_nadi_madhya(self, manish_chart):
        """Rohini's nadi per NAKSHATRA_NADIS (constants.py) is Madhya."""
        result = compute_avakhada(manish_chart)
        assert result.nadi == "Madhya"

    def test_yoni_serpent(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.yoni == "Serpent"

    def test_varna_vaishya(self, manish_chart):
        """Taurus (Earth sign) → Vaishya."""
        result = compute_avakhada(manish_chart)
        assert result.varna == "Vaishya"

    def test_vashya_chatushpad(self, manish_chart):
        """Taurus → Chatushpad (four-legged)."""
        result = compute_avakhada(manish_chart)
        assert result.vashya == "Chatushpad"

    # Lagna
    def test_ascendant_mithuna(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.ascendant == "Mithuna"

    def test_ascendant_lord_mercury(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert result.ascendant_lord == "Mercury"

    # Name alphabet
    def test_name_alphabet_va(self, manish_chart):
        """Rohini Pada 2 → 'Va'."""
        result = compute_avakhada(manish_chart)
        assert result.name_alphabet == "Va"

    # Panchang fields are non-empty strings
    def test_tithi_nonempty(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert isinstance(result.tithi, str) and len(result.tithi) > 0

    def test_karan_nonempty(self, manish_chart):
        result = compute_avakhada(manish_chart)
        assert isinstance(result.karan, str) and len(result.karan) > 0

    # All 18 fields populated
    def test_all_fields_populated(self, manish_chart):
        result = compute_avakhada(manish_chart)
        for field_name, value in result.model_dump().items():
            assert value is not None and value != "", f"Field '{field_name}' is empty"


class TestAvakhadaEdgeCases:
    """Edge case: secondary chart (01/01/2000, New Delhi)."""

    def test_returns_valid_avakhada(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert isinstance(result, AvakhadaChakra)

    def test_paya_in_valid_set(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert result.paya in {"Gold", "Silver", "Copper", "Iron"}

    def test_tatva_in_valid_set(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert result.tatva in {"Fire", "Earth", "Air", "Water"}

    def test_yunja_in_valid_set(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert result.yunja in {"Poorva", "Madhya", "Uttara"}

    def test_gan_in_valid_set(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert result.gan in {"Deva", "Manushya", "Rakshasa"}

    def test_nadi_in_valid_set(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert result.nadi in {"Aadi", "Madhya", "Antya"}

    def test_charan_in_valid_range(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert 1 <= result.charan <= 4

    def test_nakshatra_number_in_valid_range(self, sample_chart):
        result = compute_avakhada(sample_chart)
        assert 1 <= result.nakshatra_number <= 27
