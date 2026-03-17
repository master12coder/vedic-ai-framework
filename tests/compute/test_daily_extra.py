"""Additional tests for the daily suggestion engine."""

from __future__ import annotations

from datetime import date

from jyotish.compute.daily import (
    VARA_PLANETS,
    DailySuggestion,
    TransitImpact,
    _compute_day_rating,
    compute_daily_suggestion,
)
from jyotish.domain.constants.astro import MAX_DAY_RATING


class TestDailySuggestionDataclass:
    """Tests for DailySuggestion structure and field validity."""

    def test_returns_daily_suggestion_instance(self, manish_chart) -> None:
        """compute_daily_suggestion should return a DailySuggestion dataclass."""
        result = compute_daily_suggestion(manish_chart, target_date=date(2026, 3, 17))
        assert isinstance(result, DailySuggestion)

    def test_day_rating_within_bounds(self, manish_chart) -> None:
        """day_rating should be between 1 and MAX_DAY_RATING inclusive."""
        result = compute_daily_suggestion(manish_chart, target_date=date(2026, 3, 17))
        assert 1 <= result.day_rating <= MAX_DAY_RATING

    def test_vara_matches_day_of_week(self, manish_chart) -> None:
        """vara should match the actual day name of the target date."""
        target = date(2026, 3, 17)  # Tuesday
        result = compute_daily_suggestion(manish_chart, target_date=target)
        assert result.vara == target.strftime("%A")

    def test_vara_planet_matches_vara(self, manish_chart) -> None:
        """vara_planet should correspond to the vara via VARA_PLANETS."""
        target = date(2026, 3, 17)  # Tuesday
        result = compute_daily_suggestion(manish_chart, target_date=target)
        expected_planet = VARA_PLANETS[result.vara]
        assert result.vara_planet == expected_planet

    def test_good_for_is_list(self, manish_chart) -> None:
        """good_for should be a non-empty list of strings."""
        result = compute_daily_suggestion(manish_chart, target_date=date(2026, 3, 17))
        assert isinstance(result.good_for, list)
        assert len(result.good_for) >= 1
        assert all(isinstance(item, str) for item in result.good_for)

    def test_avoid_is_list(self, manish_chart) -> None:
        """avoid should be a non-empty list of strings."""
        result = compute_daily_suggestion(manish_chart, target_date=date(2026, 3, 17))
        assert isinstance(result.avoid, list)
        assert len(result.avoid) >= 1
        assert all(isinstance(item, str) for item in result.avoid)

    def test_transit_impacts_are_transit_impact(self, manish_chart) -> None:
        """Each transit impact should be a TransitImpact instance."""
        result = compute_daily_suggestion(manish_chart, target_date=date(2026, 3, 17))
        for impact in result.transit_impacts:
            assert isinstance(impact, TransitImpact)

    def test_recommended_color_is_string(self, manish_chart) -> None:
        """recommended_color should be a non-empty string."""
        result = compute_daily_suggestion(manish_chart, target_date=date(2026, 3, 17))
        assert isinstance(result.recommended_color, str)
        assert len(result.recommended_color) > 0


class TestComputeDayRating:
    """Tests for the internal _compute_day_rating helper."""

    def test_empty_impacts_returns_5(self) -> None:
        """No transit impacts should default to rating 5."""
        assert _compute_day_rating([]) == 5

    def test_high_bindus_gives_high_rating(self) -> None:
        """High bindu averages should yield a high day rating."""
        impacts = [
            TransitImpact(
                planet="Jupiter", transit_sign="Mesha",
                natal_house=1, bindus=7, is_favorable=True,
                description="test",
            ),
            TransitImpact(
                planet="Venus", transit_sign="Vrishabha",
                natal_house=2, bindus=6, is_favorable=True,
                description="test",
            ),
        ]
        rating = _compute_day_rating(impacts)
        assert rating >= 7

    def test_low_bindus_gives_low_rating(self) -> None:
        """Low bindu averages should yield a low day rating."""
        impacts = [
            TransitImpact(
                planet="Saturn", transit_sign="Kanya",
                natal_house=6, bindus=0, is_favorable=False,
                description="test",
            ),
            TransitImpact(
                planet="Mars", transit_sign="Vrischika",
                natal_house=8, bindus=1, is_favorable=False,
                description="test",
            ),
        ]
        rating = _compute_day_rating(impacts)
        assert rating <= 3

    def test_rating_never_exceeds_max(self) -> None:
        """Rating should never exceed MAX_DAY_RATING even with extreme bindus."""
        impacts = [
            TransitImpact(
                planet="Jupiter", transit_sign="Mesha",
                natal_house=1, bindus=8, is_favorable=True,
                description="test",
            ),
        ]
        rating = _compute_day_rating(impacts)
        assert rating <= MAX_DAY_RATING

    def test_rating_never_below_1(self) -> None:
        """Rating should never go below 1 even with zero bindus."""
        impacts = [
            TransitImpact(
                planet="Saturn", transit_sign="Kanya",
                natal_house=6, bindus=0, is_favorable=False,
                description="test",
            ),
        ]
        rating = _compute_day_rating(impacts)
        assert rating >= 1
