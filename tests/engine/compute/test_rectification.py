"""Tests for birth time rectification — KP Ruling Planets, events, Tattwa.

Primary fixture: manish_chart (Manish Chaurasia — verified reference chart).
  DOB: 13/03/1989  TOB: 12:17  Place: Varanasi
  Lagna: Mithuna (Gemini)   Moon: Rohini Pada 2

Source: BPHS Ch.4, KP system.
"""

from __future__ import annotations

import swisseph as swe

from daivai_engine.compute.rectification import (
    _compute_lagna_for_time,
    _expected_lords_for_event,
    _house_lord,
    _nak_index_from_longitude,
    _weekday_lord,
    get_ruling_planets,
    rectify_birth_time,
)
from daivai_engine.constants import DAY_PLANET, NAKSHATRA_LORDS, SIGN_LORDS
from daivai_engine.models.chart import ChartData
from daivai_engine.models.rectification import (
    EventVerification,
    LifeEvent,
    RectificationResult,
    RulingPlanets,
)


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestNakIndexFromLongitude:
    """Test nakshatra index derivation from sidereal longitude."""

    def test_zero_longitude_is_ashwini(self) -> None:
        """0 degrees = Ashwini (index 0)."""
        assert _nak_index_from_longitude(0.0) == 0

    def test_rohini_range(self) -> None:
        """Rohini spans 40-53.33 degrees (index 3)."""
        assert _nak_index_from_longitude(45.0) == 3

    def test_revati_range(self) -> None:
        """Revati = last nakshatra, index 26, spans 346.67-360 degrees."""
        assert _nak_index_from_longitude(350.0) == 26

    def test_boundary_at_13_333(self) -> None:
        """At exactly 13.333... degrees, should be Bharani (index 1)."""
        span = 360.0 / 27
        assert _nak_index_from_longitude(span) == 1


class TestWeekdayLord:
    """Test weekday → planet lord mapping."""

    def test_monday_is_moon(self) -> None:
        """2026-03-23 is a Monday — lord = Moon."""
        jd = swe.julday(2026, 3, 23, 12.0)
        assert _weekday_lord(jd) == "Moon"

    def test_sunday_is_sun(self) -> None:
        """2026-03-22 is a Sunday — lord = Sun."""
        jd = swe.julday(2026, 3, 22, 12.0)
        assert _weekday_lord(jd) == "Sun"

    def test_tuesday_is_mars(self) -> None:
        """2026-03-24 is a Tuesday — lord = Mars."""
        jd = swe.julday(2026, 3, 24, 12.0)
        assert _weekday_lord(jd) == "Mars"


# ---------------------------------------------------------------------------
# KP Ruling Planets
# ---------------------------------------------------------------------------


class TestGetRulingPlanets:
    """Test KP ruling planet computation."""

    def test_returns_ruling_planets_model(self) -> None:
        jd = swe.julday(2026, 3, 23, 12.0)
        result = get_ruling_planets(jd, 25.3176, 83.0067)
        assert isinstance(result, RulingPlanets)

    def test_all_five_rulers_are_valid_planets(self) -> None:
        jd = swe.julday(2026, 3, 23, 12.0)
        result = get_ruling_planets(jd, 25.3176, 83.0067)
        valid = set(SIGN_LORDS.values()) | set(NAKSHATRA_LORDS) | set(DAY_PLANET.values())
        assert result.moon_nak_lord in valid
        assert result.moon_sign_lord in valid
        assert result.lagna_nak_lord in valid
        assert result.lagna_sign_lord in valid
        assert result.day_lord in valid

    def test_day_lord_is_moon_on_monday(self) -> None:
        jd = swe.julday(2026, 3, 23, 12.0)
        result = get_ruling_planets(jd, 25.3176, 83.0067)
        assert result.day_lord == "Moon"

    def test_unique_rulers_deduplicated(self) -> None:
        jd = swe.julday(2026, 3, 23, 12.0)
        result = get_ruling_planets(jd, 25.3176, 83.0067)
        assert len(result.unique_rulers) == len(set(result.unique_rulers))
        assert len(result.unique_rulers) <= 5


# ---------------------------------------------------------------------------
# House lord helper
# ---------------------------------------------------------------------------


class TestHouseLord:
    """Test house lord computation from chart."""

    def test_first_house_lord_is_lagna_lord(self, manish_chart: ChartData) -> None:
        """House 1 lord = sign lord of lagna sign."""
        lord = _house_lord(manish_chart, 1)
        expected = SIGN_LORDS[manish_chart.lagna_sign_index]
        assert lord == expected

    def test_seventh_house_lord(self, manish_chart: ChartData) -> None:
        """House 7 lord for Mithuna lagna = Sagittarius lord = Jupiter."""
        lord = _house_lord(manish_chart, 7)
        # Mithuna = index 2, 7th house sign = (2+6) % 12 = 8 (Dhanu/Sagittarius)
        assert lord == "Jupiter"


# ---------------------------------------------------------------------------
# Event verification
# ---------------------------------------------------------------------------


class TestExpectedLordsForEvent:
    """Test expected dasha lords for different event types."""

    def test_marriage_includes_venus(self, manish_chart: ChartData) -> None:
        lords = _expected_lords_for_event(manish_chart, "marriage")
        assert "Venus" in lords

    def test_first_child_includes_jupiter(self, manish_chart: ChartData) -> None:
        lords = _expected_lords_for_event(manish_chart, "first_child")
        assert "Jupiter" in lords

    def test_parent_death_includes_sun(self, manish_chart: ChartData) -> None:
        lords = _expected_lords_for_event(manish_chart, "parent_death")
        assert "Sun" in lords


# ---------------------------------------------------------------------------
# Lagna computation for candidate times
# ---------------------------------------------------------------------------


class TestComputeLagnaForTime:
    """Test sidereal lagna computation at offset times."""

    def test_zero_offset_matches_chart(self, manish_chart: ChartData) -> None:
        """Zero offset should give lagna close to the chart's lagna."""
        _, sign_idx, _ = _compute_lagna_for_time(
            manish_chart.julian_day,
            0.0,
            manish_chart.latitude,
            manish_chart.longitude,
        )
        assert sign_idx == manish_chart.lagna_sign_index

    def test_large_offset_may_change_sign(self, manish_chart: ChartData) -> None:
        """A large offset (e.g., 120 min) may produce a different lagna sign."""
        _, sign_idx_120, _ = _compute_lagna_for_time(
            manish_chart.julian_day,
            120.0,
            manish_chart.latitude,
            manish_chart.longitude,
        )
        assert 0 <= sign_idx_120 <= 11

    def test_sign_index_valid_range(self, manish_chart: ChartData) -> None:
        for offset in (-30, -10, 0, 10, 30):
            _, sign_idx, deg = _compute_lagna_for_time(
                manish_chart.julian_day,
                float(offset),
                manish_chart.latitude,
                manish_chart.longitude,
            )
            assert 0 <= sign_idx <= 11
            assert 0 <= deg < 30


# ---------------------------------------------------------------------------
# Full rectification
# ---------------------------------------------------------------------------


class TestRectifyBirthTime:
    """Integration tests for rectify_birth_time."""

    def test_result_type(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        assert isinstance(result, RectificationResult)

    def test_original_time_preserved(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        assert result.original_birth_time == "12:17"
        assert result.original_lagna == "Gemini"

    def test_candidates_are_sorted_by_score(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        scores = [c.total_score for c in result.candidates]
        assert scores == sorted(scores, reverse=True)

    def test_best_candidate_is_first(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        if result.candidates:
            assert result.best_candidate == result.candidates[0]

    def test_confidence_is_valid(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        assert result.confidence in ("high", "medium", "low")

    def test_ruling_planets_present(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        assert result.ruling_planets_now is not None
        assert isinstance(result.ruling_planets_now, RulingPlanets)

    def test_with_tattwa_filter(self, manish_chart: ChartData) -> None:
        """Tattwa 'vayu' should boost Air sign lagnas."""
        result = rectify_birth_time(
            manish_chart,
            time_range_minutes=10,
            tattwa="vayu",
        )
        assert isinstance(result, RectificationResult)
        # Best candidate should have lagna in an Air sign if available
        if result.best_candidate:
            assert result.best_candidate.method in ("tattwa", "combined")

    def test_with_events(self, manish_chart: ChartData) -> None:
        """Event-based rectification should produce event verifications."""
        events = [
            LifeEvent(
                event_type="career_start",
                date="01/01/2012",
                description="Started first job",
            ),
        ]
        result = rectify_birth_time(
            manish_chart,
            time_range_minutes=10,
            events=events,
        )
        assert isinstance(result, RectificationResult)
        assert len(result.event_verifications) == 1
        assert isinstance(result.event_verifications[0], EventVerification)

    def test_summary_nonempty(self, manish_chart: ChartData) -> None:
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        assert len(result.summary) > 0
        assert "Rectification" in result.summary

    def test_candidate_count(self, manish_chart: ChartData) -> None:
        """With range=10 and step=2, expect 11 candidates (-10,-8,...,8,10)."""
        result = rectify_birth_time(manish_chart, time_range_minutes=10)
        expected_count = len(range(-10, 11, 2))
        assert len(result.candidates) == expected_count
