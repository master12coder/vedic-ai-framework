"""Tests for the Shadbala horizontal bar chart renderer."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.compute.strength import compute_shadbala
from jyotish_engine.models.chart import ChartData
from jyotish_engine.models.strength import ShadbalaResult
from jyotish_products.plugins.kundali.shadbala_chart import (
    _find_extremes,
    render_shadbala_chart,
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
def manish_shadbala(manish_chart: ChartData) -> list[ShadbalaResult]:
    """Pre-computed Shadbala for Manish's chart."""
    return compute_shadbala(manish_chart)


class TestShadbalaChartRendering:
    """Core rendering tests."""

    def test_returns_png_bytes(
        self,
        manish_chart: ChartData,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """render_shadbala_chart should return non-empty PNG bytes."""
        result = render_shadbala_chart(manish_chart, manish_shadbala)
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_png_has_valid_header(
        self,
        manish_chart: ChartData,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """PNG bytes must start with the PNG magic header."""
        result = render_shadbala_chart(manish_chart, manish_shadbala)
        assert result is not None
        assert result[:4] == b"\x89PNG"

    def test_saves_to_file(
        self,
        manish_chart: ChartData,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """render_shadbala_chart with output_path should save file and return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_shadbala.png"
            result = render_shadbala_chart(
                manish_chart,
                manish_shadbala,
                output_path=str(path),
            )
            assert result is None
            assert path.exists()
            assert path.stat().st_size > 1000

    def test_creates_parent_dirs(
        self,
        manish_chart: ChartData,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """Should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "shadbala.png"
            render_shadbala_chart(
                manish_chart,
                manish_shadbala,
                output_path=str(path),
            )
            assert path.exists()


class TestShadbalaChartContent:
    """Test that chart data is correctly processed."""

    def test_seven_planets_computed(
        self,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """Shadbala should have exactly 7 classical planet results."""
        assert len(manish_shadbala) == 7

    def test_all_planets_present(
        self,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """All 7 classical planets must be in the results."""
        planet_names = {s.planet for s in manish_shadbala}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert planet_names == expected

    def test_strongest_planet_detected(
        self,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """Strongest planet should have rank 1."""
        strongest, _ = _find_extremes(manish_shadbala)
        assert strongest is not None
        assert strongest.rank == 1

    def test_weakest_planet_detected(
        self,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """Weakest planet should have the highest rank number."""
        _, weakest = _find_extremes(manish_shadbala)
        assert weakest is not None
        assert weakest.rank == 7

    def test_strongest_different_from_weakest(
        self,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """Strongest and weakest must be different planets."""
        strongest, weakest = _find_extremes(manish_shadbala)
        assert strongest is not None and weakest is not None
        assert strongest.planet != weakest.planet

    def test_ratios_are_positive(
        self,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """All Shadbala ratios should be positive."""
        for sb in manish_shadbala:
            assert sb.ratio > 0, f"{sb.planet} has non-positive ratio {sb.ratio}"


class TestShadbalaChartEdgeCases:
    """Edge case and robustness tests."""

    def test_empty_shadbala_list(self, manish_chart: ChartData) -> None:
        """Should handle empty shadbala list without error."""
        result = render_shadbala_chart(manish_chart, [])
        assert result is not None
        assert result[:4] == b"\x89PNG"

    def test_find_extremes_empty_list(self) -> None:
        """_find_extremes should return (None, None) for empty input."""
        strongest, weakest = _find_extremes([])
        assert strongest is None
        assert weakest is None

    def test_chart_image_is_reproducible(
        self,
        manish_chart: ChartData,
        manish_shadbala: list[ShadbalaResult],
    ) -> None:
        """Two renders of the same data should produce same-size images."""
        img1 = render_shadbala_chart(manish_chart, manish_shadbala)
        img2 = render_shadbala_chart(manish_chart, manish_shadbala)
        assert img1 is not None and img2 is not None
        assert abs(len(img1) - len(img2)) < 100
