"""Tests for Ashtakavarga Shodhana reductions — BPHS Ch.71.

Covers:
  - trikona_shodhana: pure function, known inputs/outputs, invariants
  - ekadhipatya_shodhana: node rules, bindu comparison, equal-value tiebreaker
  - compute_shodhana: integration with a synthetic chart and manish_chart
  - compute_shodhya_pinda: Rasi/Graha Pinda arithmetic, structural validity
"""

from __future__ import annotations

import pytest

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga
from daivai_engine.compute.ashtakavarga_shodhana import (
    compute_shodhana,
    compute_shodhya_pinda,
    ekadhipatya_shodhana,
    trikona_shodhana,
)
from daivai_engine.constants import GRAHA_GUNAKARA, RASI_GUNAKARA
from daivai_engine.models.chart import ChartData, PlanetData


# ---------------------------------------------------------------------------
# Helpers — reuse the same synthetic chart factory from test_ashtakavarga.py
# ---------------------------------------------------------------------------


def _make_planet(name: str, sign_index: int) -> PlanetData:
    """Minimal PlanetData for testing purposes."""
    return PlanetData(
        name=name,
        name_hi="",
        longitude=sign_index * 30.0 + 15.0,
        sign_index=sign_index,
        sign="",
        sign_en="",
        sign_hi="",
        degree_in_sign=15.0,
        nakshatra_index=0,
        nakshatra="",
        nakshatra_lord="",
        pada=1,
        house=sign_index + 1,
        is_retrograde=False,
        speed=1.0,
        dignity="neutral",
        avastha="Yuva",
        is_combust=False,
        sign_lord="",
    )


def _make_chart() -> ChartData:
    """Synthetic chart with planets spread across signs for deterministic tests."""
    chart = ChartData(
        name="Test Native",
        dob="15/01/1990",
        tob="06:00",
        place="Delhi",
        gender="Male",
        latitude=28.6139,
        longitude=77.2090,
        timezone_name="Asia/Kolkata",
        julian_day=2447912.5,
        ayanamsha=23.7,
        lagna_longitude=280.0,
        lagna_sign_index=9,  # Capricorn
        lagna_sign="Makara",
        lagna_sign_en="Capricorn",
        lagna_sign_hi="मकर",
        lagna_degree=10.0,
    )
    positions = {
        "Sun": 9,  # Capricorn
        "Moon": 3,  # Cancer
        "Mars": 0,  # Aries
        "Mercury": 10,  # Aquarius
        "Jupiter": 5,  # Virgo
        "Venus": 11,  # Pisces
        "Saturn": 8,  # Sagittarius
        "Rahu": 2,  # Gemini
        "Ketu": 8,  # Sagittarius (Rahu + 6)
    }
    for name, sign_idx in positions.items():
        chart.planets[name] = _make_planet(name, sign_idx)
    return chart


# ---------------------------------------------------------------------------
# TestTrikonaShodhana — pure function tests
# ---------------------------------------------------------------------------


class TestTrikonaShodhana:
    """Verify Trikona Shodhana correctness with known inputs."""

    def test_known_values(self):
        """Exact output for a hand-computed input."""
        #  Input:  [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]
        #  Groups and reductions:
        #    (0,4,8):  [3,5,5] min=3 → [0,2,2]
        #    (1,5,9):  [1,9,3] min=1 → [0,8,2]
        #    (2,6,10): [4,2,5] min=2 → [2,0,3]
        #    (3,7,11): [1,6,8] min=1 → [0,5,7]
        result = trikona_shodhana([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8])
        assert result == [0, 0, 2, 0, 2, 8, 0, 5, 2, 2, 3, 7]

    def test_all_equal_becomes_zero(self):
        """All three values in a trikona group equal → all become 0."""
        # Each group has the same value everywhere → min equals value → all 0.
        result = trikona_shodhana([4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4])
        assert result == [0] * 12

    def test_length_preserved(self):
        """Output always has 12 elements."""
        result = trikona_shodhana([0] * 12)
        assert len(result) == 12

    def test_values_nonnegative(self):
        """No value becomes negative after reduction."""
        import random

        rng = random.Random(42)
        for _ in range(20):
            bindus = [rng.randint(0, 8) for _ in range(12)]
            result = trikona_shodhana(bindus)
            assert all(v >= 0 for v in result)

    def test_each_group_has_zero(self):
        """After reduction, the minimum within every trikona group is 0."""
        import random

        rng = random.Random(99)
        for _ in range(30):
            bindus = [rng.randint(0, 8) for _ in range(12)]
            result = trikona_shodhana(bindus)
            for a, b, c in [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]:
                assert min(result[a], result[b], result[c]) == 0, (
                    f"Group ({a},{b},{c}) still has non-zero minimum: "
                    f"{[result[a], result[b], result[c]]}"
                )

    def test_does_not_mutate_input(self):
        """The original list must not be modified."""
        original = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 8]
        copy = list(original)
        trikona_shodhana(original)
        assert original == copy

    def test_zero_input_stays_zero(self):
        """All-zero input remains all-zero."""
        assert trikona_shodhana([0] * 12) == [0] * 12


# ---------------------------------------------------------------------------
# TestEkadhipatyaShodhana — rule-by-rule verification
# ---------------------------------------------------------------------------


class TestEkadhipatyaShodhana:
    """Verify Ekadhipatya Shodhana rules for every pair and edge case."""

    def _sarva(self, values: dict[int, int]) -> list[int]:
        """Build a 12-element list from a sparse dict of overrides."""
        base = [5] * 12
        for idx, val in values.items():
            base[idx] = val
        return base

    def test_rahu_sign_keeps_other_becomes_zero(self):
        """Sign with Rahu keeps its value; paired sign becomes 0."""
        # Mercury pair (2, 5); Rahu in sign 2 (Gemini).
        sarva = self._sarva({2: 3, 5: 7})  # sign 5 would normally be higher
        result = ekadhipatya_shodhana(sarva, rahu_sign=2, ketu_sign=8)
        assert result[2] == 3  # Rahu sign: unchanged
        assert result[5] == 0  # other Mercury sign: zeroed

    def test_ketu_sign_keeps_other_becomes_zero(self):
        """Sign with Ketu keeps its value; paired sign becomes 0."""
        # Jupiter pair (8, 11); Ketu in sign 8 (Sagittarius).
        sarva = self._sarva({8: 4, 11: 6})
        result = ekadhipatya_shodhana(sarva, rahu_sign=2, ketu_sign=8)
        assert result[8] == 4  # Ketu sign: unchanged
        assert result[11] == 0  # other Jupiter sign: zeroed

    def test_higher_keeps_difference(self):
        """Without nodes, the higher sign keeps (higher - lower)."""
        # Mars pair (0, 7); no node in either.
        sarva = self._sarva({0: 6, 7: 2})
        result = ekadhipatya_shodhana(sarva, rahu_sign=3, ketu_sign=9)
        assert result[0] == 4  # 6 - 2
        assert result[7] == 0

    def test_lower_becomes_zero(self):
        """Without nodes, the lower sign is reduced to 0."""
        # Venus pair (1, 6); sign 6 is higher.
        sarva = self._sarva({1: 3, 6: 7})
        result = ekadhipatya_shodhana(sarva, rahu_sign=4, ketu_sign=10)
        assert result[1] == 0
        assert result[6] == 4  # 7 - 3

    def test_equal_no_nodes_odd_sign_keeps(self):
        """Equal bindus, no node: odd Vedic sign keeps, even becomes 0."""
        # Saturn pair (9=Capricorn=10th Vedic=even, 10=Aquarius=11th Vedic=odd).
        sarva = self._sarva({9: 4, 10: 4})
        # Use nodes far from the Saturn pair so the equal-bindu rule fires.
        result2 = ekadhipatya_shodhana(sarva, rahu_sign=0, ketu_sign=6)
        assert result2[9] == 0  # Capricorn (even Vedic sign) → 0
        assert result2[10] == 4  # Aquarius (odd Vedic sign)  → keeps

    def test_equal_aries_scorpio_aries_keeps(self):
        """Mars pair equal: Aries (1st Vedic=odd) keeps, Scorpio (8th=even) → 0."""
        sarva = self._sarva({0: 3, 7: 3})
        result = ekadhipatya_shodhana(sarva, rahu_sign=5, ketu_sign=11)
        assert result[0] == 3  # Aries (odd) keeps
        assert result[7] == 0  # Scorpio (even) → 0

    def test_cancer_leo_unchanged(self):
        """Single-ruled Cancer and Leo are never modified."""
        sarva = self._sarva({3: 6, 4: 7})
        result = ekadhipatya_shodhana(sarva, rahu_sign=0, ketu_sign=6)
        assert result[3] == 6
        assert result[4] == 7

    def test_known_full_example(self):
        """Full 12-sign example traced by hand."""
        #  Input SAV (after trikona): [5, 3, 2, 4, 6, 1, 7, 2, 3, 4, 5, 2]
        #  Rahu=2 (Gemini), Ketu=8 (Sagittarius)
        #
        #  Mars    (0,7): 5 vs 2, no node → 0→3, 7→0
        #  Venus   (1,6): 3 vs 7, no node → 1→0, 6→4
        #  Mercury (2,5): Rahu in 2 → 2 kept, 5→0
        #  Jupiter (8,11): Ketu in 8 → 8 kept, 11→0
        #  Saturn  (9,10): 4 vs 5, no node → 9→0, 10→1
        sarva = [5, 3, 2, 4, 6, 1, 7, 2, 3, 4, 5, 2]
        result = ekadhipatya_shodhana(sarva, rahu_sign=2, ketu_sign=8)
        expected = [3, 0, 2, 4, 6, 0, 4, 0, 3, 0, 1, 0]
        assert result == expected

    def test_does_not_mutate_input(self):
        """Input list must remain unchanged."""
        sarva = [5] * 12
        copy = list(sarva)
        ekadhipatya_shodhana(sarva, rahu_sign=0, ketu_sign=6)
        assert sarva == copy

    def test_both_signs_zero_stays_zero(self):
        """Both dual-owned signs at 0 bindus with no node → stays 0,0.

        The odd-sign tiebreaker fires (odd sign 'keeps' its 0 value; even → 0).
        Net result: both are 0 regardless.
        """
        # Mars pair (0=Aries[odd], 7=Scorpio[even]); both 0, no node nearby.
        sarva = self._sarva({0: 0, 7: 0})
        result = ekadhipatya_shodhana(sarva, rahu_sign=3, ketu_sign=9)
        assert result[0] == 0
        assert result[7] == 0

    def test_both_nodes_in_same_dual_pair_falls_to_bindu_comparison(self):
        """Rahu in sign a AND Ketu in sign b of the same pair → both_has_node.

        The node-priority rules require exactly ONE sign to have a node.
        When both signs have a node, the code falls through to bindu comparison.
        Higher value keeps (higher - lower); lower → 0.
        """
        # Mercury pair (2=Gemini, 5=Virgo); Rahu in 2, Ketu in 5 → both nodes.
        # Node rules: a_has_node=True, b_has_node=True → neither exclusive rule
        # fires → else branch → compare 6 vs 4 → sign 2 keeps 2, sign 5 → 0.
        sarva = self._sarva({2: 6, 5: 4})
        result = ekadhipatya_shodhana(sarva, rahu_sign=2, ketu_sign=5)
        # Bindu comparison: 6 > 4 → result[2] = 6-4=2, result[5] = 0
        assert result[2] == 2
        assert result[5] == 0

    def test_both_nodes_equal_bindus_odd_sign_wins(self):
        """Both nodes in same pair with equal bindus → odd-sign tiebreaker."""
        # Saturn pair (9=Capricorn[even Vedic], 10=Aquarius[odd Vedic])
        # Rahu in sign 9, Ketu in sign 10 → both have nodes, both have equal bindus.
        # Falls to equal-bindu tiebreaker: sign 10 (Aquarius = 11th Vedic = odd) keeps.
        sarva = self._sarva({9: 3, 10: 3})
        result = ekadhipatya_shodhana(sarva, rahu_sign=9, ketu_sign=10)
        assert result[9] == 0  # Capricorn (even Vedic sign) → 0
        assert result[10] == 3  # Aquarius (odd Vedic sign) → keeps


# ---------------------------------------------------------------------------
# TestComputeShodhana — integration with chart
# ---------------------------------------------------------------------------


class TestComputeShodhana:
    """Integration tests for compute_shodhana using synthetic chart."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.chart = _make_chart()
        av = compute_ashtakavarga(self.chart)
        self.shodha = compute_shodhana(self.chart, av)

    def test_all_seven_planets_present(self):
        """reduced_bhinna must contain exactly the 7 Ashtakavarga planets."""
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert set(self.shodha.reduced_bhinna.keys()) == expected

    def test_reduced_bhinna_length(self):
        """Each planet's reduced BAV must have 12 entries."""
        for planet, bindus in self.shodha.reduced_bhinna.items():
            assert len(bindus) == 12, f"{planet}: expected 12, got {len(bindus)}"

    def test_trikona_sarva_length(self):
        assert len(self.shodha.trikona_sarva) == 12

    def test_reduced_sarva_length(self):
        assert len(self.shodha.reduced_sarva) == 12

    def test_all_values_nonnegative(self):
        """All bindu values in every table must be ≥ 0."""
        for planet, bindus in self.shodha.reduced_bhinna.items():
            for i, v in enumerate(bindus):
                assert v >= 0, f"{planet} sign {i}: negative value {v}"
        assert all(v >= 0 for v in self.shodha.trikona_sarva)
        assert all(v >= 0 for v in self.shodha.reduced_sarva)

    def test_trikona_groups_have_zero_in_bhinna(self):
        """After Trikona Shodhana each trikona group must have min = 0."""
        for planet, bindus in self.shodha.reduced_bhinna.items():
            for a, b, c in [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]:
                assert min(bindus[a], bindus[b], bindus[c]) == 0, (
                    f"{planet} group ({a},{b},{c}): values {[bindus[a], bindus[b], bindus[c]]}"
                )

    def test_trikona_groups_have_zero_in_sarva(self):
        """After Trikona Shodhana, trikona_sarva groups also have min = 0."""
        ts = self.shodha.trikona_sarva
        for a, b, c in [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]:
            assert min(ts[a], ts[b], ts[c]) == 0


# ---------------------------------------------------------------------------
# TestShodhyaPinda — Shodhya Pinda arithmetic
# ---------------------------------------------------------------------------


class TestShodhyaPinda:
    """Verify Shodhya Pinda computation: components and totals."""

    def test_known_values(self):
        """Hand-computed example: Sun with sparse reduced bindus."""
        #  Sun bindus: 1 in Aries(0), 2 in Cancer(3), 1 in Scorpio(7)
        reduced = {
            "Sun": [1, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0],
            "Moon": [0] * 12,
            "Mars": [0] * 12,
            "Mercury": [0] * 12,
            "Jupiter": [0] * 12,
            "Venus": [0] * 12,
            "Saturn": [0] * 12,
        }
        results = compute_shodhya_pinda(reduced)
        sun = results["Sun"]
        # Rasi Pinda: 1*7 + 2*4 + 1*8 = 7 + 8 + 8 = 23
        assert sun.rasi_pinda == 23
        # Graha Pinda: 5 * (1+2+1) = 5 * 4 = 20
        assert sun.graha_pinda == 20
        assert sun.shodhya_pinda == 43

    def test_all_planets_present(self):
        """All 7 planets must appear in the result."""
        reduced = {
            p: [0] * 12 for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        }
        results = compute_shodhya_pinda(reduced)
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert set(results.keys()) == expected

    def test_shodhya_is_sum_of_components(self):
        """shodhya_pinda must equal rasi_pinda + graha_pinda for every planet."""
        reduced = {
            "Sun": [1, 0, 2, 0, 1, 0, 2, 0, 1, 0, 2, 0],
            "Moon": [3, 1, 0, 2, 0, 1, 0, 2, 0, 3, 0, 1],
            "Mars": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "Mercury": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
            "Jupiter": [0, 1, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0],
            "Venus": [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            "Saturn": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        }
        results = compute_shodhya_pinda(reduced)
        for planet, r in results.items():
            assert r.shodhya_pinda == r.rasi_pinda + r.graha_pinda, (
                f"{planet}: {r.shodhya_pinda} ≠ {r.rasi_pinda} + {r.graha_pinda}"
            )

    def test_all_zero_input_gives_zero_pinda(self):
        """All-zero reduced BAV → all Pinda values are 0."""
        reduced = {
            p: [0] * 12 for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        }
        results = compute_shodhya_pinda(reduced)
        for _planet, r in results.items():
            assert r.rasi_pinda == 0
            assert r.graha_pinda == 0
            assert r.shodhya_pinda == 0

    def test_graha_multipliers_applied(self):
        """Graha Pinda uses the correct per-planet multiplier."""
        # Each planet has exactly 1 bindu in sign 0; Graha Pinda = multiplier * 1.
        reduced = {
            p: ([1] + [0] * 11)
            for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        }
        results = compute_shodhya_pinda(reduced)
        for planet in reduced:
            assert results[planet].graha_pinda == GRAHA_GUNAKARA[planet], (
                f"{planet}: expected graha_pinda={GRAHA_GUNAKARA[planet]}, "
                f"got {results[planet].graha_pinda}"
            )

    def test_rasi_multipliers_applied(self):
        """Rasi Pinda uses the correct per-sign multiplier."""
        # Sun has 1 bindu in each sign — Rasi Pinda = sum of all RASI_GUNAKARA.
        reduced = {
            p: [0] * 12 for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        }
        reduced["Sun"] = [1] * 12
        results = compute_shodhya_pinda(reduced)
        expected_rasi = sum(RASI_GUNAKARA)  # 7+10+8+4+10+6+7+8+9+5+11+12 = 97
        assert results["Sun"].rasi_pinda == expected_rasi


# ---------------------------------------------------------------------------
# TestShodhanaWithManishChart — real chart integration
# ---------------------------------------------------------------------------


class TestShodhanaWithManishChart:
    """Structural validity of Shodhana on the canonical Manish Chaurasia chart."""

    @pytest.fixture(autouse=True)
    def setup(self, manish_chart):
        av = compute_ashtakavarga(manish_chart)
        self.shodha = compute_shodhana(manish_chart, av)
        self.pinda = compute_shodhya_pinda(self.shodha.reduced_bhinna)

    def test_structural_validity(self):
        """Shodhana result has correct shapes and non-negative values."""
        assert len(self.shodha.trikona_sarva) == 12
        assert len(self.shodha.reduced_sarva) == 12
        assert all(v >= 0 for v in self.shodha.trikona_sarva)
        assert all(v >= 0 for v in self.shodha.reduced_sarva)
        for planet, bindus in self.shodha.reduced_bhinna.items():
            assert len(bindus) == 12, f"{planet}: length {len(bindus)}"
            assert all(v >= 0 for v in bindus), f"{planet}: negative bindu"

    def test_trikona_invariant_holds(self):
        """Each trikona group in both bhinna and sarva has minimum 0."""
        groups = [(0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)]
        ts = self.shodha.trikona_sarva
        for a, b, c in groups:
            assert min(ts[a], ts[b], ts[c]) == 0
        for planet, bindus in self.shodha.reduced_bhinna.items():
            for a, b, c in groups:
                assert min(bindus[a], bindus[b], bindus[c]) == 0, f"{planet} group ({a},{b},{c})"

    def test_shodhya_pinda_structural_validity(self):
        """All 7 Shodhya Pinda results are non-negative and internally consistent."""
        expected_planets = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert set(self.pinda.keys()) == expected_planets
        for _planet, r in self.pinda.items():
            assert r.rasi_pinda >= 0
            assert r.graha_pinda >= 0
            assert r.shodhya_pinda == r.rasi_pinda + r.graha_pinda
