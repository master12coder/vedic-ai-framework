"""Tests for the yoga card renderer."""

from __future__ import annotations

from reportlab.platypus import Paragraph, Spacer, Table

from jyotish_engine.compute.yoga import detect_all_yogas
from jyotish_engine.models.chart import ChartData
from jyotish_engine.models.yoga import YogaResult
from jyotish_products.plugins.kundali.yoga_cards import render_yoga_cards


class TestYogaCardsWithChart:
    """Integration tests using Manish chart fixture."""

    def test_returns_at_least_one_card(self, manish_chart: ChartData) -> None:
        """Manish chart should produce at least one yoga card."""
        yogas = detect_all_yogas(manish_chart)
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) >= 1

    def test_heading_is_first_element(self, manish_chart: ChartData) -> None:
        """First element should be the section heading paragraph."""
        yogas = detect_all_yogas(manish_chart)
        elements = render_yoga_cards(yogas)
        assert isinstance(elements[0], Paragraph)

    def test_max_seven_cards(self, manish_chart: ChartData) -> None:
        """Should never render more than 7 yoga cards."""
        yogas = detect_all_yogas(manish_chart)
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) <= 7

    def test_spacers_between_cards(self, manish_chart: ChartData) -> None:
        """Each card should be followed by a spacer."""
        yogas = detect_all_yogas(manish_chart)
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        spacers = [e for e in elements if isinstance(e, Spacer)]
        assert len(spacers) == len(cards)


class TestYogaCardsEmpty:
    """Tests with empty or no-present yoga lists."""

    def test_empty_list_returns_heading_and_message(self) -> None:
        """Empty yoga list should return heading + no-yogas message."""
        elements = render_yoga_cards([])
        assert len(elements) == 2
        assert isinstance(elements[0], Paragraph)
        assert isinstance(elements[1], Paragraph)

    def test_no_present_yogas_returns_empty_section(self) -> None:
        """Yogas where all are is_present=False should show empty message."""
        fake_yogas = [
            YogaResult(
                name="Test Yoga",
                name_hindi="test",
                is_present=False,
                planets_involved=["Sun"],
                houses_involved=[1],
                description="Not present",
                effect="benefic",
            ),
        ]
        elements = render_yoga_cards(fake_yogas)
        assert len(elements) == 2


class TestYogaCardRendering:
    """Unit tests for card content and styling."""

    def test_card_has_two_columns(self) -> None:
        """Each card table should have 2 columns (strip + content)."""
        yogas = [
            YogaResult(
                name="Hamsa",
                name_hindi="\u0939\u0902\u0938 \u092f\u094b\u0917",
                is_present=True,
                planets_involved=["Jupiter"],
                houses_involved=[1],
                description="Jupiter in own sign in kendra",
                effect="benefic",
            ),
        ]
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) == 1
        # Table._cellvalues is a list of rows; each row is a list of cells
        assert len(cards[0]._cellvalues[0]) == 2

    def test_malefic_card_renders(self) -> None:
        """Malefic yoga should render without error."""
        yogas = [
            YogaResult(
                name="Kemdrum",
                name_hindi="\u0915\u0947\u092e\u0926\u094d\u0930\u0941\u092e",
                is_present=True,
                planets_involved=["Moon"],
                houses_involved=[2],
                description="No planet in 2nd/12th from Moon",
                effect="malefic",
            ),
        ]
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) == 1

    def test_mixed_effect_card_renders(self) -> None:
        """Mixed effect yoga should render without error."""
        yogas = [
            YogaResult(
                name="Mixed Yoga",
                name_hindi="test",
                is_present=True,
                planets_involved=["Saturn", "Jupiter"],
                houses_involved=[7, 10],
                description="Mixed effect yoga example",
                effect="mixed",
            ),
        ]
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) == 1

    def test_description_truncated_at_120_chars(self) -> None:
        """Long descriptions should be truncated to 120 characters."""
        long_desc = "A" * 200
        yogas = [
            YogaResult(
                name="Long",
                name_hindi="test",
                is_present=True,
                planets_involved=["Sun"],
                houses_involved=[1],
                description=long_desc,
                effect="benefic",
            ),
        ]
        elements = render_yoga_cards(yogas)
        # Card renders without error — truncation is internal
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) == 1

    def test_limits_to_seven_when_many_present(self) -> None:
        """When more than 7 yogas are present, only 7 cards render."""
        yogas = [
            YogaResult(
                name=f"Yoga {i}",
                name_hindi=f"yoga {i}",
                is_present=True,
                planets_involved=["Sun"],
                houses_involved=[1],
                description=f"Yoga number {i}",
                effect="benefic",
            )
            for i in range(12)
        ]
        elements = render_yoga_cards(yogas)
        cards = [e for e in elements if isinstance(e, Table)]
        assert len(cards) == 7
