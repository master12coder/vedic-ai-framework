"""Tests for the content plugin social media card generator."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from daivai_products.plugins.content.cards import (
    ContentCard,
    format_all_cards_text,
    format_card_text,
    generate_all_cards,
    generate_card,
)
from daivai_products.plugins.content.rashifal import (
    DailyRashifal,
    SignRashifal,
    generate_rashifal,
)


_TEST_DATE = "15/01/2026"


@pytest.fixture
def rashifal() -> DailyRashifal:
    """Generate rashifal for a fixed date."""
    return generate_rashifal(_TEST_DATE)


@pytest.fixture
def single_sign(rashifal: DailyRashifal) -> SignRashifal:
    """First sign from the rashifal (Aries)."""
    return rashifal.signs[0]


@pytest.fixture
def card(single_sign: SignRashifal) -> ContentCard:
    """A single card generated from Aries rashifal."""
    return generate_card(single_sign)


@pytest.fixture
def all_cards(rashifal: DailyRashifal) -> list[ContentCard]:
    """Cards for all 12 signs."""
    return generate_all_cards(rashifal)


class TestCardGeneration:
    """Core card generation tests."""

    def test_card_has_headline(self, card: ContentCard) -> None:
        """Card must have a non-empty Hindi headline."""
        assert card.headline
        # Should contain Devanagari
        assert any("\u0900" <= ch <= "\u097f" for ch in card.headline)

    def test_card_has_stars(self, card: ContentCard) -> None:
        """Card must have a star rating string."""
        assert card.rating_stars
        assert len(card.rating_stars) == 10  # 10 characters (filled + empty)

    def test_card_has_one_liner(self, card: ContentCard) -> None:
        """Card must have a Hindi one-liner prediction."""
        assert card.one_liner
        assert any("\u0900" <= ch <= "\u097f" for ch in card.one_liner)

    def test_card_has_color(self, card: ContentCard) -> None:
        """Card must have a color field."""
        assert card.color

    def test_card_has_mantra(self, card: ContentCard) -> None:
        """Card must have a mantra."""
        assert card.mantra

    def test_card_preserves_sign_info(self, card: ContentCard, single_sign: SignRashifal) -> None:
        """Card sign and sign_hindi must match the input rashifal."""
        assert card.sign == single_sign.sign
        assert card.sign_hindi == single_sign.sign_hindi


class TestAllCards:
    """Tests for batch card generation."""

    def test_all_cards_generated(self, all_cards: list[ContentCard]) -> None:
        """Must generate exactly 12 cards."""
        assert len(all_cards) == 12

    def test_all_cards_unique_signs(self, all_cards: list[ContentCard]) -> None:
        """Each card must be for a different sign."""
        signs = {c.sign for c in all_cards}
        assert len(signs) == 12

    def test_all_cards_have_headlines(self, all_cards: list[ContentCard]) -> None:
        """Every card must have a headline."""
        for card in all_cards:
            assert card.headline, f"{card.sign} card missing headline"


class TestCardFormatting:
    """Tests for text formatting functions."""

    def test_format_card_text_multiline(self, card: ContentCard) -> None:
        """Formatted card text must be multi-line."""
        text = format_card_text(card)
        assert "\n" in text
        assert len(text) > 50

    def test_format_card_text_contains_headline(self, card: ContentCard) -> None:
        """Formatted text must include the headline."""
        text = format_card_text(card)
        assert card.headline in text

    def test_format_card_text_contains_mantra(self, card: ContentCard) -> None:
        """Formatted text must include the mantra."""
        text = format_card_text(card)
        assert card.mantra in text

    def test_format_all_cards_text(self, all_cards: list[ContentCard]) -> None:
        """All-cards text must contain all 12 signs."""
        text = format_all_cards_text(all_cards)
        for card in all_cards:
            assert card.headline in text

    def test_format_all_cards_has_separators(self, all_cards: list[ContentCard]) -> None:
        """All-cards text must have separators between signs."""
        text = format_all_cards_text(all_cards)
        # 12 cards with 11 separators
        separator = "\u2500" * 30
        assert text.count(separator) == 11


class TestCardModelFrozen:
    """Verify card model is immutable."""

    def test_content_card_frozen(self, card: ContentCard) -> None:
        """ContentCard should be immutable."""
        with pytest.raises(ValidationError):
            card.sign = "Changed"  # type: ignore[misc]
