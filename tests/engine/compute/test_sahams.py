"""Tests for Tajaka Sahams (16 classical Arabic Parts)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from daivai_engine.compute.sahams import (
    TajakaSaham,
    TajakaSahamsResult,
    compute_tajaka_sahams,
    get_saham_by_name,
)
from daivai_engine.models.chart import ChartData


# The 17 expected sahams (16 classical + Pasha)
_EXPECTED_NAMES = {
    "Punya Saham",
    "Vidya Saham",
    "Yasha Saham",
    "Mitra Saham",
    "Mahatmya Saham",
    "Asha Saham",
    "Samartha Saham",
    "Bhratri Saham",
    "Gaurava Saham",
    "Pitri Saham",
    "Rajya Saham",
    "Matri Saham",
    "Putra Saham",
    "Jeeva Saham",
    "Karman Saham",
    "Kali Saham",
    "Pasha Saham",
}


class TestTajakaSahamsResult:
    def test_returns_pydantic_model(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        assert isinstance(result, TajakaSahamsResult)

    def test_returns_17_sahams(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        assert len(result.sahams) == 17

    def test_all_expected_names_present(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        names = {s.name for s in result.sahams}
        assert names == _EXPECTED_NAMES

    def test_yasha_saham_present(self, manish_chart: ChartData) -> None:
        """Yasha Saham must be in the result (Fame indicator — key Tajaka saham)."""
        result = compute_tajaka_sahams(manish_chart)
        yasha = get_saham_by_name(result, "Yasha Saham")
        assert yasha is not None
        assert 0 <= yasha.longitude < 360

    def test_mitra_saham_present(self, manish_chart: ChartData) -> None:
        """Mitra Saham must be in the result (Friends indicator)."""
        result = compute_tajaka_sahams(manish_chart)
        mitra = get_saham_by_name(result, "Mitra Saham")
        assert mitra is not None

    def test_punya_saham_present(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        punya = get_saham_by_name(result, "Punya Saham")
        assert punya is not None

    def test_all_longitudes_valid(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        for s in result.sahams:
            assert 0.0 <= s.longitude < 360.0, f"{s.name} longitude out of range"

    def test_all_sign_indices_valid(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        for s in result.sahams:
            assert 0 <= s.sign_index <= 11, f"{s.name} sign_index invalid"

    def test_all_degrees_in_sign_valid(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        for s in result.sahams:
            assert 0.0 <= s.degree_in_sign < 30.0, f"{s.name} degree_in_sign invalid"

    def test_all_have_hindi_names(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        for s in result.sahams:
            assert len(s.name_hi) > 0

    def test_all_have_signification(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        for s in result.sahams:
            assert len(s.signification) > 5

    def test_all_have_formula_day(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        for s in result.sahams:
            assert "Lagna" in s.formula_day

    def test_all_have_nakshatra(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        from daivai_engine.constants import NAKSHATRAS
        for s in result.sahams:
            assert s.nakshatra in NAKSHATRAS

    def test_all_have_sign_en(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        from daivai_engine.constants import SIGNS_EN
        for s in result.sahams:
            assert s.sign_en in SIGNS_EN

    def test_is_day_birth_flag(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        assert isinstance(result.is_day_birth, bool)

    def test_get_saham_by_name_found(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        vidya = get_saham_by_name(result, "Vidya Saham")
        assert vidya is not None
        assert isinstance(vidya, TajakaSaham)

    def test_get_saham_by_name_not_found_returns_none(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        missing = get_saham_by_name(result, "Nonexistent Saham")
        assert missing is None

    def test_rajya_inverse_of_pitri_formula(self, manish_chart: ChartData) -> None:
        """Rajya Saham = Lagna + Saturn - Sun; Pitri Saham = Lagna + Sun - Saturn.
        For day birth, their difference from L must be symmetric (modular inverse)."""
        result = compute_tajaka_sahams(manish_chart)
        rajya = get_saham_by_name(result, "Rajya Saham")
        pitri = get_saham_by_name(result, "Pitri Saham")
        assert rajya is not None and pitri is not None
        # For day birth: Rajya = L+Sat-Sun, Pitri = L+Sun-Sat. Sum mod 360 = 2L mod 360.
        expected = (2 * manish_chart.lagna_longitude) % 360.0
        actual = (rajya.longitude + pitri.longitude) % 360.0
        assert abs(actual - expected) < 0.01

    def test_model_is_frozen(self, manish_chart: ChartData) -> None:
        result = compute_tajaka_sahams(manish_chart)
        with pytest.raises(ValidationError):
            result.is_day_birth = not result.is_day_birth  # type: ignore[misc]
