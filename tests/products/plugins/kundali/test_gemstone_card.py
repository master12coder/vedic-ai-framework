"""Tests for the gemstone card PDF renderer."""

from __future__ import annotations

import pytest

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.models.chart import ChartData
from jyotish_products.plugins.kundali.gemstone_card import render_gemstone_card
from jyotish_products.plugins.remedies.gemstone import (
    GemstoneWeightResult,
    compute_gemstone_weights,
)


@pytest.fixture
def manish_chart() -> ChartData:
    """Reference chart: Manish Chaurasia — Mithuna lagna."""
    return compute_chart(
        name="Manish Chaurasia",
        dob="13/03/1989",
        tob="12:17",
        lat=25.3176,
        lon=83.0067,
        tz_name="Asia/Kolkata",
        gender="Male",
    )


@pytest.fixture
def gemstone_results(manish_chart: ChartData) -> list[GemstoneWeightResult]:
    """Pre-computed gemstone weight results for Manish chart."""
    return compute_gemstone_weights(manish_chart, body_weight_kg=78.0)


class TestGemstoneCardBasics:
    """Core rendering tests."""

    def test_returns_flowable_list(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """render_gemstone_card should return a non-empty list of flowables."""
        elements = render_gemstone_card(gemstone_results)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_returns_multiple_flowables(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Should return heading + sections + disclaimer = many flowables."""
        elements = render_gemstone_card(gemstone_results)
        # At minimum: heading + spacer + section + spacer + disclaimer + spacer
        assert len(elements) >= 6

    def test_handles_empty_results(self) -> None:
        """Empty results list should still return flowables (heading + disclaimer)."""
        elements = render_gemstone_card([])
        assert isinstance(elements, list)
        assert len(elements) >= 2  # heading + disclaimer at minimum


class TestRecommendedSection:
    """Tests for the recommended stones section."""

    def test_emerald_in_recommended_section(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Emerald (Panna) must appear in recommended section for Mithuna lagna."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "Emerald" in all_text

    def test_recommended_shows_ratti(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Recommended stones should show ratti weight."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "ratti" in all_text

    def test_recommended_shows_comparison(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Recommended stones should show engine vs website comparison."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "Our engine" in all_text
        assert "Avg website" in all_text


class TestProhibitedSection:
    """Tests for the prohibited stones section."""

    @pytest.mark.safety
    def test_pukhraj_in_prohibited_section(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Yellow Sapphire (Pukhraj) must appear in prohibited section for Mithuna."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        # Pukhraj is the Hindi name for Yellow Sapphire
        assert "Yellow Sapphire" in all_text
        assert "Prohibited" in all_text

    @pytest.mark.safety
    def test_moonga_in_prohibited_section(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Red Coral (Moonga) must appear in prohibited section for Mithuna."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "Red Coral" in all_text

    @pytest.mark.safety
    def test_moti_in_prohibited_section(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Pearl (Moti) must appear in prohibited section for Mithuna."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "Pearl" in all_text

    def test_prohibited_stones_show_reason(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Prohibited stones should include a prohibition reason."""
        prohibited = [r for r in gemstone_results if r.status == "prohibited"]
        assert len(prohibited) > 0
        for r in prohibited:
            assert r.prohibition_reason is not None


class TestFreeAlternatives:
    """Tests for the free alternatives section."""

    def test_free_alternatives_present(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Free alternatives section should be rendered."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "Free Alternatives" in all_text

    def test_free_alternatives_include_mantra(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Free alternatives table should include Mantra column."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "Mantra" in all_text


class TestDisclaimerNote:
    """Tests for the honesty disclaimer."""

    def test_disclaimer_present(
        self,
        gemstone_results: list[GemstoneWeightResult],
    ) -> None:
        """Honesty disclaimer about shastra must be present."""
        elements = render_gemstone_card(gemstone_results)
        all_text = _extract_text(elements)
        assert "No shastra prescribes exact weight" in all_text

    def test_disclaimer_present_even_with_empty_results(self) -> None:
        """Disclaimer should appear even with no results."""
        elements = render_gemstone_card([])
        all_text = _extract_text(elements)
        assert "No shastra prescribes exact weight" in all_text


# ── Helpers ─────────────────────────────────────────────────────────────


def _extract_text(elements: list) -> str:
    """Extract all text content from ReportLab flowable elements.

    Handles Paragraphs (via .text), Tables (via _cellvalues), and
    ignores spacers/other elements gracefully.
    """
    parts: list[str] = []
    for el in elements:
        # Paragraph has a .text attribute
        if hasattr(el, "text"):
            parts.append(el.text)
        # Table stores data in _cellvalues
        if hasattr(el, "_cellvalues"):
            for row in el._cellvalues:
                for cell in row:
                    if cell is not None:
                        parts.append(str(cell))
    return " ".join(parts)
