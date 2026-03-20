"""Tests for Deeptadi and Lajjitadi avastha computations.

Deeptadi now uses PANCHADA (5-fold combined) friendship per BPHS Ch.3 v57-58.
"""

from __future__ import annotations

from daivai_engine.compute.avasthas import (
    compute_deeptadi_avasthas,
    compute_lajjitadi_avasthas,
    compute_panchada_relation,
)
from daivai_engine.models.chart import ChartData


class TestPanchadaFriendship:
    """Test the Panchada (5-fold) friendship computation — BPHS Ch.3 v57-58."""

    def test_panchada_returns_valid_relation(self, manish_chart: ChartData) -> None:
        valid = {"adhimitra", "mitra", "sama", "shatru", "adhishatru"}
        for name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
            p = manish_chart.planets[name]
            relation = compute_panchada_relation(name, p.sign_lord, manish_chart)
            assert relation in valid, f"{name} got invalid relation '{relation}'"

    def test_sun_in_aquarius_panchada(self, manish_chart: ChartData) -> None:
        """Sun in Aquarius: lord=Saturn. Nat=enemy, Temp=friend(dist 11) → sama."""
        relation = compute_panchada_relation("Sun", "Saturn", manish_chart)
        assert relation == "sama"

    def test_mars_in_taurus_panchada(self, manish_chart: ChartData) -> None:
        """Mars in Taurus: lord=Venus. Nat=neutral, Temp=friend(dist 10) → mitra."""
        relation = compute_panchada_relation("Mars", "Venus", manish_chart)
        assert relation == "mitra"

    def test_venus_lord_panchada(self, manish_chart: ChartData) -> None:
        """Venus in Aquarius: lord=Saturn. Nat=friend, Temp=friend → adhimitra."""
        relation = compute_panchada_relation("Venus", "Saturn", manish_chart)
        assert relation == "adhimitra"


class TestDeeptadiAvasthas:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_deeptadi_avasthas(manish_chart)
        assert len(results) == 7

    def test_moon_is_deepta_for_manish(self, manish_chart: ChartData) -> None:
        """Moon exalted in Taurus = Deepta (brilliant) state."""
        results = compute_deeptadi_avasthas(manish_chart)
        moon = next(r for r in results if r.planet == "Moon")
        assert moon.avastha == "deepta"
        assert moon.strength_multiplier == 1.5

    def test_venus_is_vikala_for_manish(self, manish_chart: ChartData) -> None:
        """Venus combust = Vikala (crippled) per BPHS priority."""
        results = compute_deeptadi_avasthas(manish_chart)
        venus = next(r for r in results if r.planet == "Venus")
        assert venus.avastha == "vikala"
        assert venus.strength_multiplier == 0.5

    def test_sun_is_deena_with_panchada(self, manish_chart: ChartData) -> None:
        """Sun: Nat enemy Saturn + Temp friend = sama → Deena. Matches external."""
        results = compute_deeptadi_avasthas(manish_chart)
        sun = next(r for r in results if r.planet == "Sun")
        assert sun.avastha == "deena"

    def test_mars_is_shanta_with_panchada(self, manish_chart: ChartData) -> None:
        """Mars: Nat neutral Venus + Temp friend = mitra → Shanta. Matches external."""
        results = compute_deeptadi_avasthas(manish_chart)
        mars = next(r for r in results if r.planet == "Mars")
        assert mars.avastha == "shanta"

    def test_valid_avastha_names(self, manish_chart: ChartData) -> None:
        valid = {
            "deepta",
            "swastha",
            "mudita",
            "shanta",
            "deena",
            "vikala",
            "dukhita",
            "khal",
            "kopa",
        }
        results = compute_deeptadi_avasthas(manish_chart)
        for r in results:
            assert r.avastha in valid, f"{r.planet} has invalid avastha '{r.avastha}'"

    def test_multiplier_in_range(self, manish_chart: ChartData) -> None:
        results = compute_deeptadi_avasthas(manish_chart)
        for r in results:
            assert 0.0 <= r.strength_multiplier <= 1.5

    def test_debilitated_planet_gets_kopa(self, sample_chart: ChartData) -> None:
        results = compute_deeptadi_avasthas(sample_chart)
        for r in results:
            planet = sample_chart.planets[r.planet]
            if planet.dignity == "debilitated":
                assert r.avastha == "kopa"


class TestLajjitadiAvasthas:
    def test_returns_seven_results(self, manish_chart: ChartData) -> None:
        results = compute_lajjitadi_avasthas(manish_chart)
        assert len(results) == 7

    def test_moon_is_garvita_for_manish(self, manish_chart: ChartData) -> None:
        results = compute_lajjitadi_avasthas(manish_chart)
        moon = next(r for r in results if r.planet == "Moon")
        assert moon.avastha == "garvita"
        assert moon.is_positive is True

    def test_all_have_valid_states(self, manish_chart: ChartData) -> None:
        valid = {"lajjita", "garvita", "kshudhita", "trushita", "mudita", "kshobhita"}
        results = compute_lajjitadi_avasthas(manish_chart)
        for r in results:
            assert r.avastha in valid
