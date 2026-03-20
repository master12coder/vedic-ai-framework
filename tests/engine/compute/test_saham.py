"""Tests for Saham (sensitive points) computation."""

from __future__ import annotations

from daivai_engine.compute.saham import compute_sahams
from daivai_engine.models.chart import ChartData


_EXPECTED_NAMES = {
    # Original 6
    "Punya Saham",
    "Vivaha Saham",
    "Putra Saham",
    "Karma Saham",
    "Vidya Saham",
    "Mrityu Saham",
    # Health & Body
    "Roga Saham",
    "Sharira Saham",
    # Relationships
    "Bandhu Saham",
    "Matri Saham",
    "Pitri Saham",
    "Bhratri Saham",
    # Wealth & Career
    "Rajya Saham",
    "Dhana Saham",
    "Vyapara Saham",
    "Labha Saham",
    # Spiritual
    "Dharma Saham",
    "Guru Saham",
    "Mantra Saham",
    # Events
    "Yatra Saham",
    "Vitta Saham",
    "Paradesa Saham",
    "Santana Saham",
    # Danger
    "Apamrityu Saham",
    "Kali Saham",
    "Rog Saham",
    # Additional classical
    "Jalapatana Saham",
    "Shatru Saham",
    "Gajakesari Saham",
}


class TestSahams:
    def test_returns_29_sahams(self, manish_chart: ChartData) -> None:
        results = compute_sahams(manish_chart)
        assert len(results) == 29

    def test_all_names_present(self, manish_chart: ChartData) -> None:
        results = compute_sahams(manish_chart)
        names = {r.name for r in results}
        assert names == _EXPECTED_NAMES

    def test_longitudes_valid(self, manish_chart: ChartData) -> None:
        results = compute_sahams(manish_chart)
        for s in results:
            assert 0 <= s.longitude < 360
            assert 0 <= s.sign_index <= 11
            assert 0 <= s.degree_in_sign < 30
            assert s.nakshatra

    def test_has_hindi_names(self, manish_chart: ChartData) -> None:
        results = compute_sahams(manish_chart)
        for s in results:
            assert s.name_hi

    def test_has_sign_info(self, manish_chart: ChartData) -> None:
        results = compute_sahams(manish_chart)
        for s in results:
            assert s.sign_en
            assert s.sign_hi

    def test_punya_saham_present(self, manish_chart: ChartData) -> None:
        """Punya Saham must always be in the result set."""
        results = compute_sahams(manish_chart)
        punya = next((s for s in results if s.name == "Punya Saham"), None)
        assert punya is not None
        assert 0 <= punya.longitude < 360

    def test_dharma_and_yatra_same_formula(self, manish_chart: ChartData) -> None:
        """Dharma and Yatra Sahams share the 9th-cusp formula — longitudes must match."""
        results = compute_sahams(manish_chart)
        dharma = next(s for s in results if s.name == "Dharma Saham")
        yatra = next(s for s in results if s.name == "Yatra Saham")
        assert dharma.longitude == yatra.longitude

    def test_roga_vyapara_shatru_same_formula(self, manish_chart: ChartData) -> None:
        """Roga, Vyapara, and Shatru all use the Mars-Saturn (day) formula."""
        results = compute_sahams(manish_chart)
        roga = next(s for s in results if s.name == "Roga Saham")
        vyapara = next(s for s in results if s.name == "Vyapara Saham")
        shatru = next(s for s in results if s.name == "Shatru Saham")
        assert roga.longitude == vyapara.longitude == shatru.longitude
