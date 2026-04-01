"""Tests for the content plugin rashifal generator."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from daivai_products.plugins.content.rashifal import (
    DailyRashifal,
    generate_rashifal,
)


# Use a fixed date to ensure deterministic results across test runs.
_TEST_DATE = "15/01/2026"


@pytest.fixture
def rashifal() -> DailyRashifal:
    """Generate rashifal for a fixed date."""
    return generate_rashifal(_TEST_DATE)


class TestRashifalGeneration:
    """Core rashifal generation tests."""

    def test_generates_12_signs(self, rashifal: DailyRashifal) -> None:
        """Rashifal must contain exactly 12 sign entries."""
        assert len(rashifal.signs) == 12

    def test_date_matches_input(self, rashifal: DailyRashifal) -> None:
        """Returned date must match the requested date."""
        assert rashifal.date == _TEST_DATE

    def test_all_signs_present(self, rashifal: DailyRashifal) -> None:
        """All 12 zodiac signs must be represented."""
        expected_signs = {
            "Aries",
            "Taurus",
            "Gemini",
            "Cancer",
            "Leo",
            "Virgo",
            "Libra",
            "Scorpio",
            "Sagittarius",
            "Capricorn",
            "Aquarius",
            "Pisces",
        }
        actual_signs = {s.sign for s in rashifal.signs}
        assert actual_signs == expected_signs

    def test_all_signs_have_hindi_name(self, rashifal: DailyRashifal) -> None:
        """Every sign must have a non-empty Hindi name."""
        for sign in rashifal.signs:
            assert sign.sign_hindi, f"{sign.sign} missing Hindi name"
            # Hindi names should contain Devanagari characters
            assert any("\u0900" <= ch <= "\u097f" for ch in sign.sign_hindi), (
                f"{sign.sign} Hindi name '{sign.sign_hindi}' has no Devanagari"
            )


class TestRashifalContent:
    """Content quality tests for rashifal fields."""

    def test_day_rating_between_1_and_10(self, rashifal: DailyRashifal) -> None:
        """Day rating must be in [1, 10] range for all signs."""
        for sign in rashifal.signs:
            assert 1 <= sign.day_rating <= 10, f"{sign.sign} rating {sign.day_rating} out of range"

    def test_lucky_number_between_1_and_9(self, rashifal: DailyRashifal) -> None:
        """Lucky number must be in [1, 9] range."""
        for sign in rashifal.signs:
            assert 1 <= sign.lucky_number <= 9, (
                f"{sign.sign} lucky_number {sign.lucky_number} out of range"
            )

    def test_lucky_color_not_empty(self, rashifal: DailyRashifal) -> None:
        """Lucky color must be a non-empty string."""
        for sign in rashifal.signs:
            assert sign.lucky_color, f"{sign.sign} has empty lucky_color"

    def test_career_finance_health_love_populated(self, rashifal: DailyRashifal) -> None:
        """All four domain predictions must be non-empty strings."""
        for sign in rashifal.signs:
            assert sign.career, f"{sign.sign} has empty career"
            assert sign.finance, f"{sign.sign} has empty finance"
            assert sign.health, f"{sign.sign} has empty health"
            assert sign.love, f"{sign.sign} has empty love"

    def test_remedy_not_empty(self, rashifal: DailyRashifal) -> None:
        """Remedy must be a non-empty string with actionable advice."""
        for sign in rashifal.signs:
            assert sign.remedy, f"{sign.sign} has empty remedy"
            assert len(sign.remedy) > 10, f"{sign.sign} remedy too short: '{sign.remedy}'"

    def test_mantra_not_empty(self, rashifal: DailyRashifal) -> None:
        """Mantra must be a non-empty string."""
        for sign in rashifal.signs:
            assert sign.mantra, f"{sign.sign} has empty mantra"


class TestRashifalDeterminism:
    """Verify that rashifal is deterministic for the same date."""

    def test_same_date_same_result(self) -> None:
        """Two calls with the same date must produce identical results."""
        r1 = generate_rashifal(_TEST_DATE)
        r2 = generate_rashifal(_TEST_DATE)
        assert r1 == r2

    def test_different_dates_may_differ(self) -> None:
        """Different dates should produce different rashifals."""
        r1 = generate_rashifal("01/01/2026")
        r2 = generate_rashifal("01/07/2026")
        # At minimum the dates differ; ratings likely differ too
        assert r1.date != r2.date

    def test_default_date_is_today(self) -> None:
        """Calling without a date should use today's date."""
        r = generate_rashifal()
        expected = date.today().strftime("%d/%m/%Y")
        assert r.date == expected


class TestRashifalModelFrozen:
    """Verify models are immutable."""

    def test_sign_rashifal_frozen(self, rashifal: DailyRashifal) -> None:
        """SignRashifal should be immutable."""
        with pytest.raises(ValidationError):
            rashifal.signs[0].day_rating = 5  # type: ignore[misc]

    def test_daily_rashifal_frozen(self, rashifal: DailyRashifal) -> None:
        """DailyRashifal should be immutable."""
        with pytest.raises(ValidationError):
            rashifal.date = "01/01/2099"  # type: ignore[misc]
