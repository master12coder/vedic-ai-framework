"""Tests for multi-ayanamsha computation.

Reference values cross-verified against:
  - engine/knowledge/ayanamsha_reference.yaml (internal)
  - Swiss Ephemeris documentation
  - Independent online calculators (verified within 2.2 arcseconds of Lahiri)

Key fixture:
  Manish Chaurasia: 13/03/1989, 12:17 PM IST, Varanasi
  Julian Day: 2447598.783 (13 Mar 1989 06:47 UTC)
  Lahiri ayanamsha: 23°42'22.23" (23.70617398°) — VERIFIED

Reference ordering at any modern date:
  Fagan-Bradley > Lahiri ≈ True-Chitra > KP > Raman ≈ Yukteshwar
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.ayanamsha import (
    _degrees_to_dms,
    compute_all_ayanamshas,
    compute_ayanamsha,
    compute_ayanamsha_value,
    get_ayanamsha_info,
)
from daivai_engine.models.ayanamsha import AyanamshaInfo, AyanamshaType, AyanamshaValue


# ── Reference Julian Days ─────────────────────────────────────────────────────
# 13 March 1989, 12:17 PM IST = 06:47 UTC → JD 2447598.783
# Verified: Lahiri = 23°42'22.23" (23.70617398°) per ayanamsha_reference.yaml
JD_MANISH = 2447598.783

# J2000.0: 1 January 2000, 12:00 TT — standard astronomical reference epoch
JD_J2000 = 2451545.0

# 1 January 1950, 00:00 UT
JD_1950 = 2433282.5

# 1 January 2024, 00:00 UT
JD_2024 = 2460310.5


# ─────────────────────────────────────────────────────────────────────────────
class TestAyanamshaTypeEnum:
    """AyanamshaType enum structure and membership."""

    def test_exactly_six_types_defined(self) -> None:
        """Exactly 6 ayanamsha types must be defined — one per supported system."""
        assert len(list(AyanamshaType)) == 6

    def test_all_required_types_present(self) -> None:
        """All six required systems must be enumerated."""
        types = set(AyanamshaType)
        assert AyanamshaType.LAHIRI in types
        assert AyanamshaType.KRISHNAMURTI in types
        assert AyanamshaType.RAMAN in types
        assert AyanamshaType.TRUE_CHITRAPAKSHA in types
        assert AyanamshaType.YUKTESHWAR in types
        assert AyanamshaType.FAGAN_BRADLEY in types

    def test_enum_inherits_from_str(self) -> None:
        """AyanamshaType inherits str — values usable directly in JSON and dicts."""
        assert AyanamshaType.LAHIRI == "lahiri"
        assert AyanamshaType.KRISHNAMURTI == "krishnamurti"
        assert AyanamshaType.RAMAN == "raman"
        assert AyanamshaType.TRUE_CHITRAPAKSHA == "true_chitrapaksha"

    def test_enum_roundtrip_from_string(self) -> None:
        """AyanamshaType can be constructed from its string value."""
        assert AyanamshaType("lahiri") == AyanamshaType.LAHIRI
        assert AyanamshaType("krishnamurti") == AyanamshaType.KRISHNAMURTI


# ─────────────────────────────────────────────────────────────────────────────
class TestComputeAyanamshaVerifiedValues:
    """Ayanamsha values verified against published tables and cross-sources."""

    def test_lahiri_manish_dob_within_tolerance(self) -> None:
        """Lahiri for 13 Mar 1989 matches verified 23.70617° within 18 arcseconds."""
        result = compute_ayanamsha(JD_MANISH, AyanamshaType.LAHIRI)
        # Verified value from ayanamsha_reference.yaml: 23.70617398°
        # Tolerance: 0.005° = 18 arcseconds (generous for minor JD rounding)
        assert abs(result - 23.70617) < 0.005

    def test_lahiri_default_matches_explicit(self) -> None:
        """compute_ayanamsha() with no type arg equals explicit LAHIRI call."""
        result_default = compute_ayanamsha(JD_J2000)
        result_explicit = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        assert result_default == pytest.approx(result_explicit, abs=1e-9)

    def test_raman_manish_dob_matches_published_table(self) -> None:
        """Raman for 13 Mar 1989 ≈ 22°15'35\"-22°15'40\" per reference.yaml."""
        # Documented: source_1 = "22°15'40\"" = 22.2611°
        #             source_2 = "22°15'35\"" = 22.2597°
        result = compute_ayanamsha(JD_MANISH, AyanamshaType.RAMAN)
        assert 22.25 < result < 22.28

    def test_kp_manish_dob_matches_published_table(self) -> None:
        """KP for 13 Mar 1989 ≈ 23°36'42\"-23°36'57\" per reference.yaml."""
        # Documented: kp_old = "23°36'42\"" = 23.6117°
        #             kp_new = "23°36'57\"" = 23.6158°
        result = compute_ayanamsha(JD_MANISH, AyanamshaType.KRISHNAMURTI)
        assert 23.60 < result < 23.63

    def test_lahiri_j2000_approx_23deg51min(self) -> None:
        """Lahiri at J2000.0 ≈ 23°51' (~23.85°) per task specification."""
        result = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        # Known value: ~23°51' = 23.85°. Allow ±0.1° for tolerance.
        assert 23.75 < result < 23.95

    def test_kp_j2000_approximately_6min_less_than_lahiri(self) -> None:
        """KP at J2000.0 differs from Lahiri by ~6 arcminutes as documented."""
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        kp = compute_ayanamsha(JD_J2000, AyanamshaType.KRISHNAMURTI)
        delta_arcmin = (lahiri - kp) * 60.0
        # Documented: ~6 arcminutes. Allow 3-10 arcminute range.
        assert 3.0 < delta_arcmin < 10.0

    def test_raman_manish_delta_from_lahiri_1deg26min(self) -> None:
        """Raman differs from Lahiri by ~1°26' on Manish's DOB per reference.yaml."""
        lahiri = compute_ayanamsha(JD_MANISH, AyanamshaType.LAHIRI)
        raman = compute_ayanamsha(JD_MANISH, AyanamshaType.RAMAN)
        delta_deg = lahiri - raman
        # Documented: delta = "1°26'40\"" ≈ 1.444°
        assert 1.40 < delta_deg < 1.50

    def test_kp_manish_delta_from_lahiri_5to6min(self) -> None:
        """KP differs from Lahiri by 5-6 arcminutes on Manish's DOB."""
        lahiri = compute_ayanamsha(JD_MANISH, AyanamshaType.LAHIRI)
        kp = compute_ayanamsha(JD_MANISH, AyanamshaType.KRISHNAMURTI)
        delta_arcmin = (lahiri - kp) * 60.0
        # Documented: kp_old delta = 5'38", kp_new delta = 5'23"
        assert 4.0 < delta_arcmin < 7.0


# ─────────────────────────────────────────────────────────────────────────────
class TestComputeAyanamshaSystematicProperties:
    """Mathematical and astronomical properties that all ayanamsha systems share."""

    def test_all_values_in_modern_era_range(self) -> None:
        """All six systems at J2000 fall between 20° and 26° (modern era band)."""
        for ayan_type in AyanamshaType:
            result = compute_ayanamsha(JD_J2000, ayan_type)
            assert 20.0 < result < 26.0, (
                f"{ayan_type.value}: {result:.4f} deg outside expected 20-26 deg range"
            )

    def test_all_values_increase_over_time_due_to_precession(self) -> None:
        """Precession increases ayanamsha monotonically: 2024 value > 1950 value."""
        for ayan_type in AyanamshaType:
            val_1950 = compute_ayanamsha(JD_1950, ayan_type)
            val_2024 = compute_ayanamsha(JD_2024, ayan_type)
            assert val_2024 > val_1950, (
                f"{ayan_type.value}: ayanamsha did not increase from 1950 to 2024 "
                f"({val_1950:.4f}° → {val_2024:.4f}°)"
            )

    def test_lahiri_precession_rate_approximately_50arcsec_per_year(self) -> None:
        """Lahiri precession rate is ~50.27 arcseconds/year (≈0.01396°/year)."""
        jd_1 = JD_J2000
        jd_2 = JD_J2000 + 365.25 * 10  # 10 years later
        val_1 = compute_ayanamsha(jd_1, AyanamshaType.LAHIRI)
        val_2 = compute_ayanamsha(jd_2, AyanamshaType.LAHIRI)
        annual_rate_deg = (val_2 - val_1) / 10
        # 50.27 arcsec/yr = 0.013964°/yr. Allow ±0.001° for model variation.
        assert 0.013 < annual_rate_deg < 0.015, (
            f"Annual precession rate {annual_rate_deg:.6f}°/yr outside expected range"
        )

    def test_six_systems_produce_six_distinct_values(self) -> None:
        """All 6 ayanamsha systems give different values — none are duplicates."""
        values = [round(compute_ayanamsha(JD_J2000, t), 3) for t in AyanamshaType]
        assert len(set(values)) == 6, f"Duplicate values found: {values}"

    def test_fagan_bradley_ahead_of_lahiri(self) -> None:
        """Fagan-Bradley > Lahiri (Western sidereal zodiac is ahead of Indian)."""
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        fb = compute_ayanamsha(JD_J2000, AyanamshaType.FAGAN_BRADLEY)
        assert fb > lahiri, f"Fagan-Bradley ({fb:.4f}°) should exceed Lahiri ({lahiri:.4f}°)"

    def test_lahiri_greater_than_raman(self) -> None:
        """Lahiri > Raman by ~1°27' — Raman uses a later zero year (397 CE vs 285 CE)."""
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        raman = compute_ayanamsha(JD_J2000, AyanamshaType.RAMAN)
        assert lahiri > raman, f"Lahiri ({lahiri:.4f}°) should exceed Raman ({raman:.4f}°)"

    def test_lahiri_greater_than_kp(self) -> None:
        """Lahiri > KP — KP uses a slightly later zero year (291 CE vs 285 CE)."""
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        kp = compute_ayanamsha(JD_J2000, AyanamshaType.KRISHNAMURTI)
        assert lahiri > kp, f"Lahiri ({lahiri:.4f}°) should exceed KP ({kp:.4f}°)"

    def test_true_chitrapaksha_within_2min_of_lahiri(self) -> None:
        """True Chitra differs from Lahiri by < 2 arcminutes (< 0.033°)."""
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        true_citra = compute_ayanamsha(JD_J2000, AyanamshaType.TRUE_CHITRAPAKSHA)
        delta_arcmin = abs(lahiri - true_citra) * 60.0
        assert delta_arcmin < 2.0, (
            f"True Chitra delta {delta_arcmin:.2f}' from Lahiri exceeds 2 arcminutes"
        )

    def test_raman_gap_from_lahiri_approximately_1deg27min(self) -> None:
        """Raman gap from Lahiri ≈ 1°27' at J2000, confirming zero-year difference."""
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        raman = compute_ayanamsha(JD_J2000, AyanamshaType.RAMAN)
        delta_deg = lahiri - raman
        assert 1.35 < delta_deg < 1.55, (
            f"Lahiri-Raman gap {delta_deg:.4f}° outside expected ~1°27' range"
        )

    def test_lahiri_mode_restored_after_non_lahiri_computation(self) -> None:
        """After computing a non-Lahiri value, Lahiri mode is restored for chart.py."""
        # Compute Raman (changes global swe mode internally)
        compute_ayanamsha(JD_J2000, AyanamshaType.RAMAN)
        # Subsequent Lahiri computation should still be correct
        lahiri = compute_ayanamsha(JD_J2000, AyanamshaType.LAHIRI)
        assert 23.75 < lahiri < 23.95, (
            f"Lahiri value {lahiri:.4f}° incorrect after Raman computation — mode not restored"
        )

    def test_smooth_precession_no_discontinuities(self) -> None:
        """Annual ayanamsha change is smooth (no discontinuities) over a decade."""
        for i in range(9):
            jd1 = JD_J2000 + i * 365.25
            jd2 = JD_J2000 + (i + 1) * 365.25
            v1 = compute_ayanamsha(jd1, AyanamshaType.LAHIRI)
            v2 = compute_ayanamsha(jd2, AyanamshaType.LAHIRI)
            annual_change = v2 - v1
            assert 0.013 < annual_change < 0.015, (
                f"Year {i}: annual change {annual_change:.6f}° shows discontinuity"
            )


# ─────────────────────────────────────────────────────────────────────────────
class TestComputeAyanamshaValue:
    """AyanamshaValue model returned by compute_ayanamsha_value()."""

    def test_returns_ayanamsha_value_instance(self) -> None:
        """Return type is AyanamshaValue."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.LAHIRI)
        assert isinstance(result, AyanamshaValue)

    def test_julian_day_preserved_in_result(self) -> None:
        """AyanamshaValue.julian_day matches the input JD exactly."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.LAHIRI)
        assert result.julian_day == JD_J2000

    def test_type_field_matches_requested_type(self) -> None:
        """AyanamshaValue.type matches the requested AyanamshaType."""
        for ayan_type in AyanamshaType:
            result = compute_ayanamsha_value(JD_J2000, ayan_type)
            assert result.type == ayan_type

    def test_lahiri_delta_is_exactly_zero(self) -> None:
        """Lahiri delta_from_lahiri is 0.0 (reference system has zero gap with itself)."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.LAHIRI)
        assert result.delta_from_lahiri == 0.0

    def test_kp_delta_is_small_negative(self) -> None:
        """KP delta from Lahiri is negative (~-0.09 deg) -- KP is behind Lahiri."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.KRISHNAMURTI)
        assert result.delta_from_lahiri is not None
        assert -0.20 < result.delta_from_lahiri < -0.02

    def test_raman_delta_is_large_negative(self) -> None:
        """Raman delta from Lahiri is approximately -1.44 deg (large gap)."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.RAMAN)
        assert result.delta_from_lahiri is not None
        assert -1.60 < result.delta_from_lahiri < -1.30

    def test_fagan_bradley_delta_is_positive(self) -> None:
        """Fagan-Bradley delta from Lahiri is positive (ahead of Lahiri)."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.FAGAN_BRADLEY)
        assert result.delta_from_lahiri is not None
        assert result.delta_from_lahiri > 0.0

    def test_dms_string_contains_degree_prime_doubleprime(self) -> None:
        """DMS value_dms string contains °, ', and \" symbols."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.LAHIRI)
        assert "\u00b0" in result.value_dms  # °
        assert "'" in result.value_dms
        assert '"' in result.value_dms

    def test_lahiri_j2000_dms_starts_with_23deg(self) -> None:
        """Lahiri at J2000 ≈ 23°51' — DMS string must start with '23°'."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.LAHIRI)
        assert result.value_dms.startswith("23\u00b0"), (
            f"Expected DMS to start with '23°', got: {result.value_dms!r}"
        )

    def test_value_degrees_matches_compute_ayanamsha(self) -> None:
        """value_degrees in AyanamshaValue matches standalone compute_ayanamsha()."""
        for ayan_type in AyanamshaType:
            direct = compute_ayanamsha(JD_J2000, ayan_type)
            rich = compute_ayanamsha_value(JD_J2000, ayan_type)
            assert rich.value_degrees == pytest.approx(direct, abs=1e-9)

    def test_include_delta_false_gives_none_for_non_lahiri(self) -> None:
        """include_delta=False → delta_from_lahiri is None for non-Lahiri systems."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.RAMAN, include_delta=False)
        assert result.delta_from_lahiri is None

    def test_include_delta_false_lahiri_still_zero(self) -> None:
        """include_delta=False still sets delta=0.0 for LAHIRI (it's always known)."""
        result = compute_ayanamsha_value(JD_J2000, AyanamshaType.LAHIRI, include_delta=False)
        assert result.delta_from_lahiri == 0.0


# ─────────────────────────────────────────────────────────────────────────────
class TestGetAyanamshaInfo:
    """AyanamshaInfo metadata returned by get_ayanamsha_info()."""

    def test_returns_ayanamsha_info_instance(self) -> None:
        """Return type is AyanamshaInfo."""
        info = get_ayanamsha_info(AyanamshaType.LAHIRI)
        assert isinstance(info, AyanamshaInfo)

    def test_all_types_have_complete_metadata(self) -> None:
        """Every AyanamshaType has non-empty name, description, and reference_epoch."""
        for ayan_type in AyanamshaType:
            info = get_ayanamsha_info(ayan_type)
            assert info.name, f"{ayan_type.value}: name is empty"
            assert info.description, f"{ayan_type.value}: description is empty"
            assert info.reference_epoch, f"{ayan_type.value}: reference_epoch is empty"
            assert info.usage, f"{ayan_type.value}: usage is empty"

    def test_info_type_field_matches_requested_type(self) -> None:
        """AyanamshaInfo.type matches the requested AyanamshaType."""
        for ayan_type in AyanamshaType:
            info = get_ayanamsha_info(ayan_type)
            assert info.type == ayan_type

    def test_lahiri_info_name_contains_lahiri(self) -> None:
        """Lahiri metadata name contains 'Lahiri'."""
        info = get_ayanamsha_info(AyanamshaType.LAHIRI)
        assert "Lahiri" in info.name

    def test_lahiri_zero_year_is_285_ce(self) -> None:
        """Lahiri zero year (tropical = sidereal) is 285 CE per Calendar Reform Committee."""
        info = get_ayanamsha_info(AyanamshaType.LAHIRI)
        assert info.zero_year_ce == 285

    def test_raman_zero_year_is_397_ce(self) -> None:
        """Raman zero year is 397 CE — later than Lahiri's 285 CE explains the gap."""
        info = get_ayanamsha_info(AyanamshaType.RAMAN)
        assert info.zero_year_ce == 397

    def test_kp_info_mentions_sub_lord(self) -> None:
        """KP metadata description mentions sub-lord or KP system specifics."""
        info = get_ayanamsha_info(AyanamshaType.KRISHNAMURTI)
        combined = info.name + info.description + (info.notes or "")
        assert "KP" in combined or "sub-lord" in combined or "Krishnamurti" in combined

    def test_fagan_bradley_info_not_vedic(self) -> None:
        """Fagan-Bradley metadata clarifies it is NOT from Vedic tradition."""
        info = get_ayanamsha_info(AyanamshaType.FAGAN_BRADLEY)
        combined = info.description + (info.notes or "")
        assert "Vedic" in combined or "Western" in combined

    def test_reference_value_j2000_in_plausible_range(self) -> None:
        """All reference_value_j2000 values fall in the 22-25 deg modern-era band."""
        for ayan_type in AyanamshaType:
            info = get_ayanamsha_info(ayan_type)
            assert 20.0 < info.reference_value_j2000 < 26.0, (
                f"{ayan_type.value}: reference_value_j2000={info.reference_value_j2000} "
                "outside plausible 20-26 deg range"
            )


# ─────────────────────────────────────────────────────────────────────────────
class TestComputeAllAyanamshas:
    """compute_all_ayanamshas() returns all six types together."""

    def test_returns_all_six_types(self) -> None:
        """compute_all_ayanamshas returns exactly 6 entries."""
        result = compute_all_ayanamshas(JD_J2000)
        assert len(result) == 6

    def test_all_types_present_as_keys(self) -> None:
        """Every AyanamshaType is a key in the returned dict."""
        result = compute_all_ayanamshas(JD_J2000)
        for ayan_type in AyanamshaType:
            assert ayan_type in result

    def test_all_values_are_ayanamsha_value_instances(self) -> None:
        """Every value in the returned dict is an AyanamshaValue."""
        result = compute_all_ayanamshas(JD_J2000)
        for ayan_type, value in result.items():
            assert isinstance(value, AyanamshaValue), (
                f"{ayan_type.value}: expected AyanamshaValue, got {type(value)}"
            )

    def test_lahiri_delta_is_zero_in_combined_result(self) -> None:
        """Lahiri entry in compute_all_ayanamshas has delta_from_lahiri=0.0."""
        result = compute_all_ayanamshas(JD_J2000)
        assert result[AyanamshaType.LAHIRI].delta_from_lahiri == 0.0

    def test_all_deltas_populated(self) -> None:
        """All entries have delta_from_lahiri set (not None)."""
        result = compute_all_ayanamshas(JD_J2000)
        for ayan_type, value in result.items():
            assert value.delta_from_lahiri is not None, (
                f"{ayan_type.value}: delta_from_lahiri is None in compute_all_ayanamshas"
            )


# ─────────────────────────────────────────────────────────────────────────────
class TestDegreesToDms:
    """_degrees_to_dms() internal formatting utility."""

    def test_zero_degrees(self) -> None:
        """0.0° → '0°00'00.00\"'."""
        assert _degrees_to_dms(0.0) == "0\u00b000'00.00\""

    def test_exactly_one_degree(self) -> None:
        """1.0° → '1°00'00.00\"'."""
        assert _degrees_to_dms(1.0) == "1\u00b000'00.00\""

    def test_thirty_minutes(self) -> None:
        """0.5° = 0°30' → starts with '0°30''."""
        result = _degrees_to_dms(0.5)
        assert result.startswith("0\u00b030'")

    def test_verified_lahiri_1989(self) -> None:
        """23.70617° ≈ 23°42'22\" — DMS should start with '23°42''."""
        result = _degrees_to_dms(23.70617)
        assert result.startswith("23\u00b042'"), f"Expected '23°42'...', got: {result!r}"

    def test_known_value_seconds_precision(self) -> None:
        """23.70617° → seconds part is approximately 22.21\"."""
        result = _degrees_to_dms(23.70617)
        # Format: "23°42'22.21\""
        # Extract seconds part from the string
        after_min = result.split("'")[1]  # "22.21\""
        seconds = float(after_min.rstrip('"'))
        assert abs(seconds - 22.21) < 0.1

    def test_returns_string_type(self) -> None:
        """Return type is always str."""
        assert isinstance(_degrees_to_dms(23.5), str)

    def test_contains_required_symbols(self) -> None:
        """DMS string always contains degree, arcminute, arcsecond symbols."""
        result = _degrees_to_dms(23.70617)
        assert "\u00b0" in result  # °
        assert "'" in result
        assert '"' in result
