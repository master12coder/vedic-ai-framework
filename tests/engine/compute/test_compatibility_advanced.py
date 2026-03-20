"""Tests for advanced compatibility — Mangal Dosha, Nadi Dosha, Rajju Dosha."""

from __future__ import annotations

from daivai_engine.compute.compatibility_advanced import (
    analyze_nadi_dosha,
    check_rajju_dosha,
    compute_mangal_dosha_detailed,
)
from daivai_engine.models.chart import ChartData


class TestMangalDoshaDetailed:
    def test_returns_result(self, manish_chart: ChartData) -> None:
        result = compute_mangal_dosha_detailed(manish_chart)
        assert isinstance(result.is_present, bool)
        assert 0 <= result.severity <= 10

    def test_net_effect_valid(self, manish_chart: ChartData) -> None:
        result = compute_mangal_dosha_detailed(manish_chart)
        valid = {"none", "cancelled", "mild", "moderate", "severe"}
        assert result.net_effect in valid

    def test_cancellations_list(self, manish_chart: ChartData) -> None:
        result = compute_mangal_dosha_detailed(manish_chart)
        assert isinstance(result.cancellations, list)


class TestNadiDosha:
    def test_same_chart_has_dosha(self, manish_chart: ChartData) -> None:
        """Same person's chart compared with itself should have Nadi dosha."""
        result = analyze_nadi_dosha(manish_chart, manish_chart)
        assert result.is_present  # Same nadi = dosha

    def test_different_charts(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = analyze_nadi_dosha(manish_chart, sample_chart)
        # May or may not have dosha, just verify structure
        assert result.person1_nadi in ("Aadi", "Madhya", "Antya")
        assert result.person2_nadi in ("Aadi", "Madhya", "Antya")

    def test_severity_valid(self, manish_chart: ChartData, sample_chart: ChartData) -> None:
        result = analyze_nadi_dosha(manish_chart, sample_chart)
        assert result.net_severity in ("none", "mild", "severe")


class TestRajjuDosha:
    # Rajju groups: Paada=[0,8,9,17,18,26] Kati=[1,7,10,16,19,25]
    # Nabhi=[2,6,11,15,20,24] Kantha=[3,5,12,14,21,23] Shira=[4,13,22]

    def test_same_nakshatra_has_dosha(self) -> None:
        """Same nakshatra = same Rajju = dosha present."""
        result = check_rajju_dosha(3, 3)  # Rohini + Rohini = Kantha Rajju
        assert result.has_dosha is True
        assert result.body_part == "Kantha"
        assert result.severity == "severe"

    def test_paada_rajju_ashwini_ashlesha(self) -> None:
        """Ashwini (0) and Ashlesha (8) are both Paada Rajju."""
        result = check_rajju_dosha(0, 8)
        assert result.has_dosha is True
        assert result.body_part == "Paada"
        assert result.severity == "mild"

    def test_shira_rajju_mrigashira_chitra(self) -> None:
        """Mrigashira (4) and Chitra (13) are both Shira Rajju — most severe."""
        result = check_rajju_dosha(4, 13)
        assert result.has_dosha is True
        assert result.body_part == "Shira"
        assert result.severity == "severe"

    def test_kantha_rajju_rohini_ardra(self) -> None:
        """Rohini (3) and Ardra (5) are both Kantha Rajju."""
        result = check_rajju_dosha(3, 5)
        assert result.has_dosha is True
        assert result.body_part == "Kantha"

    def test_no_dosha_for_different_rajju(self) -> None:
        """Ashwini (Paada) and Rohini (Kantha) = different Rajju = no dosha."""
        result = check_rajju_dosha(0, 3)
        assert result.has_dosha is False
        assert result.body_part is None
        assert result.severity == "none"

    def test_nabhi_rajju_moderate_severity(self) -> None:
        """Nabhi Rajju (navel) = moderate severity."""
        result = check_rajju_dosha(2, 6)  # Krittika + Punarvasu = Nabhi
        assert result.has_dosha is True
        assert result.severity == "moderate"
        assert result.body_part == "Nabhi"

    def test_returns_nakshatra_names(self) -> None:
        """Result includes nakshatra names for display."""
        result = check_rajju_dosha(3, 3)  # Rohini + Rohini
        assert result.nakshatra1 == "Rohini"
        assert result.nakshatra2 == "Rohini"

    def test_manish_rohini_pada2_rajju(self) -> None:
        """Manish has Moon in Rohini (index 3) = Kantha Rajju."""
        result = check_rajju_dosha(3, 5)  # Rohini vs Ardra (both Kantha)
        assert result.has_dosha is True
        assert result.body_part == "Kantha"
        # Different Rajju = no dosha
        result2 = check_rajju_dosha(3, 0)  # Rohini (Kantha) vs Ashwini (Paada)
        assert result2.has_dosha is False
