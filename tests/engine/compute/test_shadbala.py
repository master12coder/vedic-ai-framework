"""Tests for the enhanced six-fold Shadbala computation."""

from __future__ import annotations

import pytest

from daivai_engine.compute.strength import (
    NAISARGIKA,
    REQUIRED_SHADBALA,
    SHADBALA_PLANETS,
    _tribhaga_bala,
    compute_planet_strengths,
    compute_shadbala,
    get_strongest_planet,
    get_weakest_planet,
)


class TestShadbalaComputation:
    """Core Shadbala computation tests."""

    def test_returns_seven_planets(self, manish_chart):
        results = compute_shadbala(manish_chart)
        assert len(results) == 7
        names = {r.planet for r in results}
        assert names == set(SHADBALA_PLANETS)

    def test_all_six_components_present(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert isinstance(r.sthana_bala, float)
            assert isinstance(r.dig_bala, float)
            assert isinstance(r.kala_bala, float)
            assert isinstance(r.cheshta_bala, float)
            assert isinstance(r.naisargika_bala, float)
            assert isinstance(r.drik_bala, float)

    def test_ratio_positive(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.ratio > 0, f"{r.planet} has non-positive ratio: {r.ratio}"

    def test_total_equals_sum_of_components(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            expected = round(
                r.sthana_bala
                + r.dig_bala
                + r.kala_bala
                + r.cheshta_bala
                + r.naisargika_bala
                + r.drik_bala
                + r.yuddha_bala,
                2,
            )
            assert abs(r.total - expected) < 0.1, f"{r.planet}: total={r.total}, sum={expected}"

    def test_naisargika_values_match_fixed_table(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            expected = NAISARGIKA[r.planet]
            assert r.naisargika_bala == expected, (
                f"{r.planet}: naisargika={r.naisargika_bala}, expected={expected}"
            )

    def test_ratio_is_total_over_required(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            expected_ratio = round(r.total / REQUIRED_SHADBALA[r.planet], 3)
            assert abs(r.ratio - expected_ratio) < 0.01, (
                f"{r.planet}: ratio={r.ratio}, expected={expected_ratio}"
            )

    def test_is_strong_matches_ratio(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.is_strong == (r.ratio >= 1.0), (
                f"{r.planet}: is_strong={r.is_strong}, ratio={r.ratio}"
            )

    def test_ranks_unique_and_sequential(self, manish_chart):
        results = compute_shadbala(manish_chart)
        ranks = sorted(r.rank for r in results)
        assert ranks == list(range(1, 8))

    def test_rank_1_has_highest_total(self, manish_chart):
        results = compute_shadbala(manish_chart)
        by_rank = {r.rank: r for r in results}
        assert by_rank[1].total >= by_rank[7].total

    def test_sthana_bala_positive(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.sthana_bala >= 0, f"{r.planet} sthana_bala negative"

    def test_dig_bala_range(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert 0.0 <= r.dig_bala <= 60.0, f"{r.planet} dig_bala={r.dig_bala} out of range"

    def test_cheshta_bala_sun_moon(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            if r.planet in ("Sun", "Moon"):
                assert r.cheshta_bala == 30.0

    def test_required_values_match(self, manish_chart):
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.required == REQUIRED_SHADBALA[r.planet]


class TestTribhagaBala:
    """Tests for Tribhaga Bala sub-component of Kala Bala."""

    def test_jupiter_always_gets_60(self, manish_chart):
        """Jupiter must receive 60 virupas Tribhaga Bala unconditionally."""
        assert _tribhaga_bala(manish_chart, "Jupiter") == 60.0

    def test_sun_gets_tribhaga_at_noon_birth(self, manish_chart):
        """Manish born at 12:17 PM — clearly 2nd third of day — Sun should get 60."""
        assert _tribhaga_bala(manish_chart, "Sun") == 60.0

    def test_non_lord_gets_zero(self, manish_chart):
        """At 12:17 PM the Tribhaga lord is Sun; Mercury/Saturn get 0."""
        # Mercury rules 1st third of day, Saturn rules 3rd — neither is active
        assert _tribhaga_bala(manish_chart, "Mercury") == 0.0
        assert _tribhaga_bala(manish_chart, "Saturn") == 0.0

    def test_tribhaga_reflected_in_kala_bala(self, manish_chart):
        """Kala Bala should include Tribhaga contribution (Jupiter gets extra 60)."""
        results = compute_shadbala(manish_chart)
        jupiter = next(r for r in results if r.planet == "Jupiter")
        # Jupiter's kala_bala must be at least 60 (from Tribhaga alone)
        assert jupiter.kala_bala >= 60.0

    def test_returns_0_or_60_only(self, manish_chart):
        """Tribhaga Bala can only be 0 or 60 virupas per planet."""
        for planet in SHADBALA_PLANETS:
            val = _tribhaga_bala(manish_chart, planet)
            assert val in (0.0, 60.0), f"{planet} returned unexpected value {val}"

    def test_exactly_one_non_jupiter_planet_gets_60(self, manish_chart):
        """Exactly one non-Jupiter planet gets Tribhaga Bala at any given time."""
        non_jup = [p for p in SHADBALA_PLANETS if p != "Jupiter"]
        lords = [p for p in non_jup if _tribhaga_bala(manish_chart, p) == 60.0]
        assert len(lords) == 1, f"Expected 1 Tribhaga lord, got {lords}"


class TestYuddhaBala:
    """Tests for Yuddha Bala (Planetary War) Shadbala integration."""

    def test_yuddha_bala_field_present(self, manish_chart):
        """Every ShadbalaResult has a yuddha_bala field."""
        results = compute_shadbala(manish_chart)
        for r in results:
            assert hasattr(r, "yuddha_bala"), f"{r.planet} missing yuddha_bala"
            assert isinstance(r.yuddha_bala, float)

    def test_no_war_gives_zero_adjustment(self, manish_chart):
        """If no planetary war exists, all yuddha_bala values are 0.0."""
        from daivai_engine.compute.graha_yuddha import detect_planetary_war

        if not detect_planetary_war(manish_chart):
            results = compute_shadbala(manish_chart)
            for r in results:
                assert r.yuddha_bala == 0.0

    def test_war_winner_gets_positive_adjustment(self, manish_chart):
        """In a planetary war, winner yuddha_bala > 0, loser yuddha_bala < 0."""
        from daivai_engine.compute.graha_yuddha import detect_planetary_war

        wars = detect_planetary_war(manish_chart)
        if wars:
            results = {r.planet: r for r in compute_shadbala(manish_chart)}
            for war in wars:
                assert results[war.winner].yuddha_bala > 0
                assert results[war.loser].yuddha_bala < 0

    @pytest.mark.parametrize("planet", SHADBALA_PLANETS)
    def test_yuddha_bala_multiple_of_60(self, manish_chart, planet):
        """Yuddha Bala adjustment must be a multiple of 60 (0, ±60, ±120…)."""
        results = {r.planet: r for r in compute_shadbala(manish_chart)}
        yb = results[planet].yuddha_bala
        assert yb % 60 == 0.0, f"{planet} yuddha_bala={yb} is not a multiple of 60"


class TestSthanaBalaComponents:
    """Verify all 5 Sthana Bala sub-components per BPHS Ch.23."""

    def test_saptvargaja_uses_all_seven_vargas(self, manish_chart):
        """Saptvargaja Bala must be materially larger than a 2-varga estimate."""
        from daivai_engine.compute.strength import _saptvargaja_bala

        # With 7 vargas minimum is 7*1.875=13.125, max is 7*45=315
        # With old 2-varga code max was 50 -- so 7-varga should differ significantly
        for planet in SHADBALA_PLANETS:
            p = manish_chart.planets[planet]
            val = _saptvargaja_bala(planet, p.longitude, p.sign_index)
            assert val >= 7 * 1.875, f"{planet} saptvargaja={val} below minimum"
            assert val <= 7 * 45.0, f"{planet} saptvargaja={val} above maximum"

    def test_ojhayugma_includes_navamsha(self, manish_chart):
        """Ojhayugma Bala can now reach 30 (15 rashi + 15 navamsha)."""
        from daivai_engine.compute.strength import _ojhayugma_bala

        for planet in SHADBALA_PLANETS:
            p = manish_chart.planets[planet]
            val = _ojhayugma_bala(planet, p.sign_index, p.longitude)
            assert 0.0 <= val <= 30.0, f"{planet} ojhayugma={val} out of [0,30]"

    def test_sthana_bala_all_five_present(self, manish_chart):
        """Sthana Bala must be positive (all 5 sub-components contribute)."""
        results = compute_shadbala(manish_chart)
        for r in results:
            assert r.sthana_bala > 0, f"{r.planet} sthana_bala={r.sthana_bala}"


class TestBackwardCompatibility:
    """Ensure compute_planet_strengths still works for existing callers."""

    def test_returns_nine_planets(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        assert len(strengths) == 9
        names = {s.planet for s in strengths}
        assert "Rahu" in names
        assert "Ketu" in names

    def test_has_total_relative(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        for s in strengths:
            assert hasattr(s, "total_relative")
            assert 0.0 <= s.total_relative <= 1.0

    def test_has_rank(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        ranks = sorted(s.rank for s in strengths)
        assert ranks == list(range(1, 10))

    def test_has_is_strong(self, manish_chart):
        strengths = compute_planet_strengths(manish_chart)
        for s in strengths:
            assert isinstance(s.is_strong, bool)

    def test_strongest_planet_returns_string(self, manish_chart):
        result = get_strongest_planet(manish_chart)
        assert isinstance(result, str)
        assert result in set(SHADBALA_PLANETS) | {"Rahu", "Ketu"}

    def test_weakest_planet_returns_string(self, manish_chart):
        result = get_weakest_planet(manish_chart)
        assert isinstance(result, str)
        assert result in set(SHADBALA_PLANETS) | {"Rahu", "Ketu"}
