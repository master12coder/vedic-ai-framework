"""Tests for Ashtakavarga computation — BPHS chapters 66-72."""

from __future__ import annotations

import pytest

from daivai_engine.compute.ashtakavarga import compute_ashtakavarga, get_transit_strength
from daivai_engine.models.chart import ChartData, PlanetData


# ---------------------------------------------------------------------------
# Fixture: a synthetic chart with known sign positions for deterministic tests.
# Planets placed at fixed sign indices so results are reproducible.
# ---------------------------------------------------------------------------


def _make_planet(name: str, sign_index: int) -> PlanetData:
    """Create a minimal PlanetData for testing."""
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
    """Create a synthetic chart with planets spread across signs."""
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
    # Place planets at specific signs for reproducibility.
    positions = {
        "Sun": 9,  # Capricorn
        "Moon": 3,  # Cancer
        "Mars": 0,  # Aries
        "Mercury": 10,  # Aquarius
        "Jupiter": 5,  # Virgo
        "Venus": 11,  # Pisces
        "Saturn": 8,  # Sagittarius
        "Rahu": 6,  # Libra
        "Ketu": 0,  # Aries
    }
    for name, sign_idx in positions.items():
        chart.planets[name] = _make_planet(name, sign_idx)
    return chart


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAshtakavarga:
    """Core Ashtakavarga computation tests."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.chart = _make_chart()
        self.result = compute_ashtakavarga(self.chart)

    def test_sarva_total_337(self):
        """Sarvashtakavarga total must always equal 337 (BPHS invariant)."""
        assert self.result.total == 337
        assert sum(self.result.sarva) == 337

    def test_bhinna_count(self):
        """There must be exactly 7 Bhinnashtakavarga tables (Sun-Saturn)."""
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert set(self.result.bhinna.keys()) == expected
        assert len(self.result.bhinna) == 7

    def test_bindu_range(self):
        """Each bindu value must be between 0 and 8 (8 possible sources)."""
        for planet, bindus in self.result.bhinna.items():
            assert len(bindus) == 12, f"{planet} should have 12 sign entries"
            for i, value in enumerate(bindus):
                assert 0 <= value <= 8, f"{planet} sign {i}: bindu {value} out of range 0-8"

    def test_sarva_is_sum_of_bhinna(self):
        """Sarvashtakavarga must equal column-wise sum of all Bhinna tables."""
        for sign in range(12):
            expected = sum(self.result.bhinna[p][sign] for p in self.result.bhinna)
            assert self.result.sarva[sign] == expected, (
                f"Sign {sign}: sarva {self.result.sarva[sign]} != bhinna sum {expected}"
            )

    def test_sarva_length(self):
        """Sarvashtakavarga must have exactly 12 entries."""
        assert len(self.result.sarva) == 12

    def test_bhinna_values_are_twelve(self):
        """Each Bhinna table must have exactly 12 values."""
        for _planet, bindus in self.result.bhinna.items():
            assert len(bindus) == 12


class TestTransitStrength:
    """Tests for transit strength categorization."""

    def test_strong(self):
        """28+ bindus should be 'strong'."""
        sarva = [28] * 12
        assert get_transit_strength(sarva, 0) == "strong"
        assert get_transit_strength(sarva, 11) == "strong"

    def test_strong_boundary(self):
        sarva = [28, 35, 40, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        assert get_transit_strength(sarva, 0) == "strong"
        assert get_transit_strength(sarva, 1) == "strong"
        assert get_transit_strength(sarva, 2) == "strong"

    def test_moderate(self):
        """21-27 bindus should be 'moderate'."""
        sarva = [21, 24, 27, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        assert get_transit_strength(sarva, 0) == "moderate"
        assert get_transit_strength(sarva, 1) == "moderate"
        assert get_transit_strength(sarva, 2) == "moderate"

    def test_weak(self):
        """0-20 bindus should be 'weak'."""
        sarva = [0, 10, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        assert get_transit_strength(sarva, 0) == "weak"
        assert get_transit_strength(sarva, 1) == "weak"
        assert get_transit_strength(sarva, 2) == "weak"

    def test_boundary_values(self):
        """Exact boundary checks: 20 -> weak, 21 -> moderate, 27 -> moderate, 28 -> strong."""
        sarva = [20, 21, 27, 28, 0, 0, 0, 0, 0, 0, 0, 0]
        assert get_transit_strength(sarva, 0) == "weak"
        assert get_transit_strength(sarva, 1) == "moderate"
        assert get_transit_strength(sarva, 2) == "moderate"
        assert get_transit_strength(sarva, 3) == "strong"


class TestMultipleCharts:
    """Verify the 337 invariant holds for different planetary configurations."""

    @pytest.mark.parametrize(
        "lagna_sign,sun_sign,moon_sign",
        [
            (0, 0, 6),  # Aries lagna, Sun in Aries, Moon in Libra
            (4, 9, 1),  # Leo lagna, Sun in Capricorn, Moon in Taurus
            (11, 5, 8),  # Pisces lagna, Sun in Virgo, Moon in Sagittarius
        ],
    )
    def test_337_invariant_across_charts(self, lagna_sign, sun_sign, moon_sign):
        """Total must be 337 regardless of planetary positions."""
        base = _make_chart()
        chart = base.model_copy(update={"lagna_sign_index": lagna_sign})
        chart.planets["Sun"] = _make_planet("Sun", sun_sign)
        chart.planets["Moon"] = _make_planet("Moon", moon_sign)
        result = compute_ashtakavarga(chart)
        assert result.total == 337
