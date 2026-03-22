"""Tests for Medical Astrology (Vaidya Jyotish) computation.

Covers:
  - BodyPartVulnerability (Kala Purusha mapping)
  - TridoshaBalance computation
  - DiseaseYoga detection (13 yogas)
  - SphutalResult (Prana/Deha/Mrityu Sphuta)
  - HealthAnalysis (full integration)

Primary fixture: Manish Chaurasia (13/03/1989, 12:17, Varanasi)
  Lagna: Mithuna (Gemini), Moon: Rohini, current MD: Jupiter (maraka).
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.chart import compute_chart
from daivai_engine.compute.medical import (
    analyze_body_part_vulnerabilities,
    analyze_health,
    compute_prana_deha_mrityu_sphuta,
    detect_disease_yogas,
)
from daivai_engine.compute.medical_dosha import compute_tridosha
from daivai_engine.models.medical import (
    BodyPartVulnerability,
    DiseaseYoga,
    HealthAnalysis,
    SphutalResult,
    TridoshaBalance,
)


# ── Model Structure Tests ─────────────────────────────────────


class TestMedicalModelStructure:
    """Verify Pydantic model fields and invariants."""

    def test_health_analysis_returns_correct_type(self, manish_chart):
        """analyze_health must return a HealthAnalysis instance."""
        result = analyze_health(manish_chart)
        assert isinstance(result, HealthAnalysis)

    def test_health_analysis_has_12_body_vulnerabilities(self, manish_chart):
        """One BodyPartVulnerability per sign — exactly 12."""
        result = analyze_health(manish_chart)
        assert len(result.body_part_vulnerabilities) == 12

    def test_health_analysis_has_13_disease_yogas(self, manish_chart):
        """Exactly 13 disease yogas checked (per BPHS Ch.68-70)."""
        result = analyze_health(manish_chart)
        assert len(result.disease_yogas) == 13

    def test_body_vulnerability_fields(self, manish_chart):
        """Each BodyPartVulnerability must have required fields with valid values."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        valid_levels = {"high", "moderate", "low", "none"}
        for v in vulns:
            assert isinstance(v, BodyPartVulnerability)
            assert 0 <= v.sign_index <= 11
            assert isinstance(v.sign, str) and v.sign
            assert isinstance(v.sign_hi, str) and v.sign_hi
            assert isinstance(v.body_parts, list) and v.body_parts
            assert isinstance(v.body_parts_hi, list) and v.body_parts_hi
            assert v.vulnerability_level in valid_levels
            assert isinstance(v.reason, str) and v.reason

    def test_disease_yoga_fields(self, manish_chart):
        """Each DiseaseYoga must have required fields with valid severities."""
        yogas = detect_disease_yogas(manish_chart)
        valid_severities = {"high", "moderate", "low", "none"}
        for y in yogas:
            assert isinstance(y, DiseaseYoga)
            assert isinstance(y.name, str) and y.name
            assert isinstance(y.name_hindi, str) and y.name_hindi
            assert isinstance(y.is_present, bool)
            assert y.severity in valid_severities
            assert isinstance(y.planets_involved, list)
            assert isinstance(y.houses_involved, list)
            assert isinstance(y.body_system_affected, str) and y.body_system_affected
            assert isinstance(y.disease_indicated, str) and y.disease_indicated
            assert isinstance(y.description, str) and y.description
            assert isinstance(y.source, str) and y.source

    def test_disease_yoga_absent_has_severity_none(self, manish_chart):
        """Absent yogas (is_present=False) must have severity='none'."""
        yogas = detect_disease_yogas(manish_chart)
        for y in yogas:
            if not y.is_present:
                assert y.severity == "none", (
                    f"Absent yoga '{y.name}' should have severity='none', got '{y.severity}'"
                )

    def test_sphuta_result_fields(self, manish_chart):
        """SphutalResult must have all three sputas with valid ranges."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        assert isinstance(sphuta, SphutalResult)
        assert 0.0 <= sphuta.prana_sphuta < 360.0
        assert 0.0 <= sphuta.deha_sphuta < 360.0
        assert 0.0 <= sphuta.mrityu_sphuta < 360.0
        assert 0 <= sphuta.prana_sphuta_sign_index <= 11
        assert 0 <= sphuta.deha_sphuta_sign_index <= 11
        assert 0 <= sphuta.mrityu_sphuta_sign_index <= 11
        assert sphuta.prana_deha_concordance in {"favorable", "neutral", "challenging"}
        assert sphuta.prana_sphuta_nakshatra
        assert sphuta.deha_sphuta_nakshatra
        assert sphuta.mrityu_sphuta_nakshatra

    def test_tridosha_percentages_sum_to_100(self, manish_chart):
        """Vata + Pitta + Kapha percentages must sum to 100 ± 0.5 (rounding)."""
        tridosha = compute_tridosha(manish_chart)
        total = tridosha.vata_percentage + tridosha.pitta_percentage + tridosha.kapha_percentage
        assert abs(total - 100.0) <= 0.5, f"Percentages sum to {total}, expected ~100"

    def test_tridosha_scores_non_negative(self, manish_chart):
        """All tridosha raw scores must be non-negative."""
        tridosha = compute_tridosha(manish_chart)
        assert tridosha.vata_score >= 0.0
        assert tridosha.pitta_score >= 0.0
        assert tridosha.kapha_score >= 0.0

    def test_tridosha_dominant_is_highest_percentage(self, manish_chart):
        """Dominant dosha must correspond to the highest percentage score."""
        tridosha = compute_tridosha(manish_chart)
        scores = {
            "Vata": tridosha.vata_percentage,
            "Pitta": tridosha.pitta_percentage,
            "Kapha": tridosha.kapha_percentage,
        }
        expected_dominant = max(scores, key=lambda k: scores[k])
        assert tridosha.dominant_dosha == expected_dominant, (
            f"Dominant should be {expected_dominant}, got {tridosha.dominant_dosha}"
        )

    def test_tridosha_constitution_type_valid(self, manish_chart):
        """Constitution type must be one of the 7 recognized types."""
        tridosha = compute_tridosha(manish_chart)
        valid_types = {
            "Vata", "Pitta", "Kapha",
            "Vata-Pitta", "Pitta-Vata",
            "Pitta-Kapha", "Kapha-Pitta",
            "Vata-Kapha", "Kapha-Vata",
            "Tridoshic",
        }
        assert tridosha.constitution_type in valid_types, (
            f"Invalid constitution type: {tridosha.constitution_type}"
        )

    def test_tridosha_planet_lists_non_empty(self, manish_chart):
        """Each dosha planet list must contain at least one planet."""
        tridosha = compute_tridosha(manish_chart)
        assert tridosha.vata_planets, "Vata planets list should not be empty"
        assert tridosha.pitta_planets, "Pitta planets list should not be empty"
        assert tridosha.kapha_planets, "Kapha planets list should not be empty"


# ── Kala Purusha Body Mapping Tests ──────────────────────────


class TestBodyPartVulnerability:
    """Tests for Kala Purusha sign → body part mapping."""

    def test_sign_indices_are_sequential_0_to_11(self, manish_chart):
        """Body vulnerabilities must cover signs 0 through 11 in order."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        indices = [v.sign_index for v in vulns]
        assert indices == list(range(12))

    def test_high_vulnerability_has_afflicting_planets(self, manish_chart):
        """High-vulnerability zones must list at least one afflicting planet."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        for v in vulns:
            if v.vulnerability_level == "high":
                assert v.afflicting_planets, (
                    f"High vulnerability zone {v.sign} has no afflicting planets listed"
                )

    def test_none_vulnerability_has_no_afflicting_planets(self, manish_chart):
        """Zones with 'none' vulnerability must have empty afflicting_planets list."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        for v in vulns:
            if v.vulnerability_level == "none":
                assert not v.afflicting_planets, (
                    f"Zone {v.sign} has 'none' vulnerability but lists planets: {v.afflicting_planets}"
                )

    def test_aries_zone_governs_head(self, manish_chart):
        """Aries (sign index 0) must govern head/skull/brain (Kala Purusha rule)."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        aries = next(v for v in vulns if v.sign_index == 0)
        head_terms = {"Head", "Skull", "Brain", "Eyes"}
        assert any(part in head_terms for part in aries.body_parts), (
            f"Aries should govern head area, got: {aries.body_parts}"
        )

    def test_pisces_zone_governs_feet(self, manish_chart):
        """Pisces (sign index 11) must govern feet/lymphatic (Kala Purusha rule)."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        pisces = next(v for v in vulns if v.sign_index == 11)
        feet_terms = {"Feet", "Toes", "Lymphatic system", "Immune system"}
        assert any(part in feet_terms for part in pisces.body_parts), (
            f"Pisces should govern feet area, got: {pisces.body_parts}"
        )

    def test_leo_zone_governs_heart(self, manish_chart):
        """Leo (sign index 4) must govern heart/spine (Kala Purusha rule)."""
        vulns = analyze_body_part_vulnerabilities(manish_chart)
        leo = next(v for v in vulns if v.sign_index == 4)
        heart_terms = {"Heart", "Spine", "Upper back", "Aorta", "Pericardium"}
        assert any(part in heart_terms for part in leo.body_parts), (
            f"Leo should govern heart, got: {leo.body_parts}"
        )


# ── Disease Yoga Detection Tests ──────────────────────────────


class TestDiseaseYogaDetection:
    """Tests for classical disease yoga detection from BPHS Ch.68-70."""

    def test_all_13_yogas_detected(self, manish_chart):
        """All 13 disease yogas must be checked and returned."""
        yogas = detect_disease_yogas(manish_chart)
        assert len(yogas) == 13

    def test_yoga_names_are_unique(self, manish_chart):
        """Each yoga name must be unique in the result set."""
        yogas = detect_disease_yogas(manish_chart)
        names = [y.name for y in yogas]
        assert len(names) == len(set(names)), "Duplicate yoga names found"

    def test_saturn_dusthana_yoga_present_when_saturn_in_dusthana(self, manish_chart):
        """Saturn in Dusthana yoga must be present iff Saturn is in 6/8/12."""
        yogas = detect_disease_yogas(manish_chart)
        saturn_yoga = next(y for y in yogas if y.name == "Saturn in Dusthana")
        saturn_house = manish_chart.planets["Saturn"].house
        if saturn_house in {6, 8, 12}:
            assert saturn_yoga.is_present
        else:
            assert not saturn_yoga.is_present

    def test_mars_yoga_present_when_mars_in_6_or_8(self, manish_chart):
        """Mars in 6th or 8th yoga must match Mars house placement."""
        yogas = detect_disease_yogas(manish_chart)
        mars_yoga = next(y for y in yogas if y.name == "Mars in 6th or 8th")
        mars_house = manish_chart.planets["Mars"].house
        expected = mars_house in {6, 8}
        assert mars_yoga.is_present == expected, (
            f"Mars in house {mars_house}; yoga.is_present={mars_yoga.is_present}, expected={expected}"
        )

    def test_lagna_lord_yoga_matches_lagnesh_house(self, manish_chart):
        """Lagna Lord in Dusthana yoga must match actual lagnesh house."""
        yogas = detect_disease_yogas(manish_chart)
        lagnesh_yoga = next(y for y in yogas if y.name == "Lagna Lord in Dusthana")
        # For Mithuna lagna, Mercury is lagnesh
        mercury_house = manish_chart.planets["Mercury"].house
        expected = mercury_house in {6, 8, 12}
        assert lagnesh_yoga.is_present == expected, (
            f"Mercury in house {mercury_house}; yoga.is_present={lagnesh_yoga.is_present}"
        )

    def test_mars_saturn_conjunction_yoga_requires_same_sign(self, manish_chart):
        """Mars-Saturn Conjunction yoga requires them in same sign AND in dusthana."""
        yogas = detect_disease_yogas(manish_chart)
        ms_yoga = next(y for y in yogas if y.name == "Mars-Saturn Conjunction in Dusthana")
        mars = manish_chart.planets["Mars"]
        saturn = manish_chart.planets["Saturn"]
        same_sign = mars.sign_index == saturn.sign_index
        in_dusthana = mars.house in {6, 8, 12}
        expected = same_sign and in_dusthana
        assert ms_yoga.is_present == expected

    @pytest.mark.safety
    def test_high_severity_yogas_have_correct_severity_string(self, manish_chart):
        """Active yogas for Saturn in 8th, Rahu in 6/8, Both Luminaries must be 'high'."""
        yogas = detect_disease_yogas(manish_chart)

        saturn_yoga = next(y for y in yogas if y.name == "Saturn in Dusthana")
        if saturn_yoga.is_present and manish_chart.planets["Saturn"].house == 8:
            assert saturn_yoga.severity == "high"

        rahu_yoga = next(y for y in yogas if y.name == "Rahu in 6th or 8th")
        if rahu_yoga.is_present:
            assert rahu_yoga.severity == "high"

        both_yoga = next(y for y in yogas if y.name == "Both Luminaries Afflicted")
        if both_yoga.is_present:
            assert both_yoga.severity == "high"

    def test_venus_yoga_present_when_venus_in_6_or_8(self, manish_chart):
        """Venus in 6th or 8th yoga must match Venus house placement."""
        yogas = detect_disease_yogas(manish_chart)
        venus_yoga = next(y for y in yogas if y.name == "Venus in 6th or 8th")
        venus_house = manish_chart.planets["Venus"].house
        expected = venus_house in {6, 8}
        assert venus_yoga.is_present == expected

    def test_yoga_sources_reference_bphs_or_classical(self, manish_chart):
        """Every disease yoga source must cite a classical text."""
        yogas = detect_disease_yogas(manish_chart)
        classical_texts = {"BPHS", "Saravali", "Phaladeepika", "Hora Sara", "Jataka Parijata"}
        for y in yogas:
            assert any(text in y.source for text in classical_texts), (
                f"Yoga '{y.name}' source missing classical citation: {y.source}"
            )


# ── Trisphuta Tests ───────────────────────────────────────────


class TestSphutalResult:
    """Tests for Prana/Deha/Mrityu Sphuta computation."""

    def test_prana_sphuta_formula(self, manish_chart):
        """Prana Sphuta = (Lagna + Sun + Moon) mod 360."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        expected = (
            manish_chart.lagna_longitude
            + manish_chart.planets["Sun"].longitude
            + manish_chart.planets["Moon"].longitude
        ) % 360.0
        assert abs(sphuta.prana_sphuta - round(expected, 4)) < 0.01

    def test_deha_sphuta_formula(self, manish_chart):
        """Deha Sphuta = (Lagna + Mars + Moon) mod 360."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        expected = (
            manish_chart.lagna_longitude
            + manish_chart.planets["Mars"].longitude
            + manish_chart.planets["Moon"].longitude
        ) % 360.0
        assert abs(sphuta.deha_sphuta - round(expected, 4)) < 0.01

    def test_mrityu_sphuta_formula(self, manish_chart):
        """Mrityu Sphuta = (Lagna + Saturn + Moon) mod 360."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        expected = (
            manish_chart.lagna_longitude
            + manish_chart.planets["Saturn"].longitude
            + manish_chart.planets["Moon"].longitude
        ) % 360.0
        assert abs(sphuta.mrityu_sphuta - round(expected, 4)) < 0.01

    def test_sphuta_sign_derived_from_longitude(self, manish_chart):
        """Prana Sphuta sign index must match floor(prana_sphuta / 30)."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        expected_sign = int(sphuta.prana_sphuta / 30) % 12
        assert sphuta.prana_sphuta_sign_index == expected_sign

    def test_all_three_sputas_differ(self, manish_chart):
        """Prana, Deha, and Mrityu Sphuta must generally differ (different planet inputs)."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        # Only Prana == Deha would require Sun == Mars exactly — very rare
        # They can coincide in sign, but not all three at the same longitude
        values = {sphuta.prana_sphuta, sphuta.deha_sphuta, sphuta.mrityu_sphuta}
        assert len(values) >= 2, "All three sputas are identical — likely a computation bug"

    def test_concordance_challenging_when_prana_in_dusthana(self, manish_chart):
        """When Prana Sphuta falls in dusthana relative to lagna, concordance is 'challenging'."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        prana_house = ((sphuta.prana_sphuta_sign_index - manish_chart.lagna_sign_index) % 12) + 1
        if prana_house in {6, 8, 12}:
            assert sphuta.prana_deha_concordance == "challenging"

    def test_concordance_favorable_when_prana_in_trikona(self, manish_chart):
        """When Prana Sphuta falls in trikona relative to lagna, concordance is 'favorable'."""
        sphuta = compute_prana_deha_mrityu_sphuta(manish_chart)
        prana_house = ((sphuta.prana_sphuta_sign_index - manish_chart.lagna_sign_index) % 12) + 1
        if prana_house in {1, 5, 9} and sphuta.prana_sphuta_sign_index != sphuta.mrityu_sphuta_sign_index:
            assert sphuta.prana_deha_concordance == "favorable"


# ── Tridosha Tests ────────────────────────────────────────────


class TestTridoshaBalance:
    """Tests for Ayurvedic Tridosha balance computation."""

    def test_tridosha_runs_on_manish_chart(self, manish_chart):
        """compute_tridosha must return a TridoshaBalance without error."""
        result = compute_tridosha(manish_chart)
        assert isinstance(result, TridoshaBalance)

    def test_tridosha_imbalance_risk_is_valid(self, manish_chart):
        """Imbalance risk must be one of: 'high', 'moderate', 'low'."""
        result = compute_tridosha(manish_chart)
        assert result.imbalance_risk in {"high", "moderate", "low"}

    def test_tridosha_description_contains_constitution(self, manish_chart):
        """TridoshaBalance description must mention the constitution type."""
        result = compute_tridosha(manish_chart)
        assert result.constitution_type in result.description

    def test_tridosha_runs_on_secondary_chart(self, sample_chart):
        """compute_tridosha must work for a different chart as well."""
        result = compute_tridosha(sample_chart)
        assert isinstance(result, TridoshaBalance)
        total = result.vata_percentage + result.pitta_percentage + result.kapha_percentage
        assert abs(total - 100.0) <= 0.5

    def test_exalted_planets_increase_dosha_score(self):
        """Exalted planet should produce higher dosha score than debilitated.

        Saturn exalted (Libra) → higher Vata score than Saturn debilitated (Aries).
        We test this indirectly by using two different charts.
        """
        # Chart 1: approximate chart where Saturn is exalted (Libra)
        chart_sat_exalt = compute_chart(
            name="Saturn Exalt Test",
            dob="15/10/1980",
            tob="12:00",
            lat=28.6139,
            lon=77.2090,
            tz_name="Asia/Kolkata",
        )
        # Chart 2: approximate chart where Saturn is debilitated (Aries)
        chart_sat_debil = compute_chart(
            name="Saturn Debil Test",
            dob="15/04/2000",
            tob="12:00",
            lat=28.6139,
            lon=77.2090,
            tz_name="Asia/Kolkata",
        )
        sat_exalt_sig = chart_sat_exalt.planets["Saturn"].sign_index
        sat_debil_sig = chart_sat_debil.planets["Saturn"].sign_index

        td1 = compute_tridosha(chart_sat_exalt)
        td2 = compute_tridosha(chart_sat_debil)

        # If Saturn is actually exalted (Libra=6) in chart1 and debilitated (Aries=0) in chart2
        # then Vata score for chart1 should be higher — we only assert this if conditions hold
        if sat_exalt_sig == 6 and sat_debil_sig == 0:
            assert td1.vata_score >= td2.vata_score, (
                "Exalted Saturn should give higher Vata score than debilitated"
            )


# ── Health Analysis Integration Tests ────────────────────────


class TestHealthAnalysis:
    """Integration tests for the full analyze_health function."""

    def test_analyze_health_manish_returns_complete_result(self, manish_chart):
        """analyze_health must return HealthAnalysis with all components populated."""
        result = analyze_health(manish_chart)
        assert isinstance(result, HealthAnalysis)
        assert result.body_part_vulnerabilities
        assert result.disease_yogas
        assert isinstance(result.tridosha_balance, TridoshaBalance)
        assert isinstance(result.sphuta_result, SphutalResult)
        assert isinstance(result.health_house_analysis, dict)
        assert isinstance(result.health_summary, str) and result.health_summary
        assert isinstance(result.dominant_health_concerns, list)

    def test_health_house_analysis_keys_are_6_8_12(self, manish_chart):
        """health_house_analysis must have keys 6, 8, 12."""
        result = analyze_health(manish_chart)
        assert set(result.health_house_analysis.keys()) == {6, 8, 12}

    def test_health_house_analysis_lists_planets_in_correct_house(self, manish_chart):
        """Planets listed in house 6 must actually be in 6th house in chart."""
        result = analyze_health(manish_chart)
        for house_num, planets in result.health_house_analysis.items():
            for planet_name in planets:
                actual_house = manish_chart.planets[planet_name].house
                assert actual_house == house_num, (
                    f"{planet_name} listed in house {house_num} but is in house {actual_house}"
                )

    def test_health_summary_mentions_constitution_type(self, manish_chart):
        """health_summary must mention the constitution type from TridoshaBalance."""
        result = analyze_health(manish_chart)
        assert result.tridosha_balance.constitution_type in result.health_summary

    def test_analyze_health_runs_without_error_on_secondary_chart(self, sample_chart):
        """analyze_health must complete without error for a second chart."""
        result = analyze_health(sample_chart)
        assert isinstance(result, HealthAnalysis)
        assert len(result.body_part_vulnerabilities) == 12
        assert len(result.disease_yogas) == 13

    def test_dominant_health_concerns_max_10(self, manish_chart):
        """dominant_health_concerns must be capped at 10 items."""
        result = analyze_health(manish_chart)
        assert len(result.dominant_health_concerns) <= 10

    @pytest.mark.safety
    def test_mithuna_lagna_mercury_is_lagnesh_yoga(self, manish_chart):
        """For Mithuna lagna, Mercury is lagnesh; its house determines lagna lord yoga."""
        assert manish_chart.lagna_sign_index == 2, "Manish chart must be Mithuna lagna"
        yogas = detect_disease_yogas(manish_chart)
        lagnesh_yoga = next(y for y in yogas if y.name == "Lagna Lord in Dusthana")
        # Mercury (lagnesh) must be in the planets_involved
        assert "Mercury" in lagnesh_yoga.planets_involved, (
            "For Mithuna lagna, Mercury (lagnesh) must be involved in Lagna Lord yoga"
        )
