"""Tests for the D1 North Indian diamond chart visual renderer."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.models.chart import ChartData
from jyotish_products.interpret.context import build_lordship_context
from jyotish_products.plugins.kundali.diamond import render_d1_chart


@pytest.fixture
def manish_chart() -> ChartData:
    """Reference chart: Manish Chaurasia — Mithuna lagna."""
    return compute_chart(
        name="Manish Chaurasia", dob="13/03/1989", tob="12:17",
        lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata", gender="Male",
    )


@pytest.fixture
def mithuna_ctx() -> dict:
    """Lordship context for Mithuna lagna."""
    return build_lordship_context("Mithuna")


class TestD1ChartRendering:
    """Core rendering tests."""

    def test_returns_png_bytes(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        """render_d1_chart should return non-empty PNG bytes."""
        result = render_d1_chart(manish_chart, mithuna_ctx)
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 1000  # Minimum viable PNG size

    def test_png_has_valid_header(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        """PNG bytes must start with the PNG magic header."""
        result = render_d1_chart(manish_chart, mithuna_ctx)
        assert result is not None
        assert result[:4] == b"\x89PNG"

    def test_saves_to_file(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        """render_d1_chart with output_path should save file and return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_d1.png"
            result = render_d1_chart(manish_chart, mithuna_ctx, output_path=str(path))
            assert result is None
            assert path.exists()
            assert path.stat().st_size > 1000

    def test_creates_parent_dirs(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        """Should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "chart.png"
            render_d1_chart(manish_chart, mithuna_ctx, output_path=str(path))
            assert path.exists()


class TestD1ChartContent:
    """Test that chart contains correct data."""

    def test_all_nine_planets_in_houses(self, manish_chart: ChartData, mithuna_ctx: dict) -> None:
        """All 9 planets must be assigned to houses 1-12."""
        for p in manish_chart.planets.values():
            assert 1 <= p.house <= 12, f"{p.name} in invalid house {p.house}"

    def test_lagna_is_mithuna(self, manish_chart: ChartData) -> None:
        """Verify Manish's lagna is Mithuna."""
        assert manish_chart.lagna_sign == "Mithuna"

    def test_lordship_context_has_benefics(self, mithuna_ctx: dict) -> None:
        """Mithuna lordship context should have functional benefics."""
        benefics = {e["planet"] for e in mithuna_ctx.get("functional_benefics", [])}
        assert "Mercury" in benefics  # Lagnesh

    @pytest.mark.safety
    def test_lordship_context_has_malefics(self, mithuna_ctx: dict) -> None:
        """Jupiter must be a functional malefic for Mithuna."""
        malefics = {e["planet"] for e in mithuna_ctx.get("functional_malefics", [])}
        assert "Jupiter" in malefics
        assert "Mars" in malefics

    def test_chart_image_is_reproducible(
        self, manish_chart: ChartData, mithuna_ctx: dict,
    ) -> None:
        """Two renders of same chart should produce same-size images."""
        img1 = render_d1_chart(manish_chart, mithuna_ctx)
        img2 = render_d1_chart(manish_chart, mithuna_ctx)
        assert img1 is not None and img2 is not None
        # Size should be very close (matplotlib can have tiny variations)
        assert abs(len(img1) - len(img2)) < 100


class TestD1ChartWithDifferentCharts:
    """Test with non-Mithuna charts."""

    def test_renders_different_lagna(self) -> None:
        """Should render any lagna, not just Mithuna."""
        chart = compute_chart(
            name="Test Person", dob="01/01/2000", tob="06:00",
            lat=28.6139, lon=77.2090, tz_name="Asia/Kolkata", gender="Female",
        )
        ctx = build_lordship_context(chart.lagna_sign)
        result = render_d1_chart(chart, ctx)
        assert result is not None
        assert len(result) > 1000

    def test_renders_with_empty_lordship_ctx(self, manish_chart: ChartData) -> None:
        """Should handle empty/missing lordship context gracefully."""
        result = render_d1_chart(manish_chart, {})
        assert result is not None
        assert len(result) > 1000
