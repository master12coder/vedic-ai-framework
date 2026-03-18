"""Tests for the Ashtakavarga heatmap renderer."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from jyotish_engine.compute.ashtakavarga import compute_ashtakavarga
from jyotish_engine.models.ashtakavarga import AshtakavargaResult
from jyotish_engine.models.chart import ChartData
from jyotish_products.plugins.kundali.ashtakavarga_heatmap import (
    render_ashtakavarga_heatmap,
)


@pytest.fixture
def manish_ashtakavarga(manish_chart: ChartData) -> AshtakavargaResult:
    """Pre-computed Ashtakavarga for Manish's chart."""
    return compute_ashtakavarga(manish_chart)


class TestAshtakavargaHeatmapRendering:
    """Core rendering tests."""

    def test_returns_png_bytes(
        self,
        manish_chart: ChartData,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """render_ashtakavarga_heatmap should return non-empty PNG bytes."""
        result = render_ashtakavarga_heatmap(manish_chart, manish_ashtakavarga)
        assert result is not None
        assert isinstance(result, bytes)
        assert len(result) > 1000

    def test_png_has_valid_header(
        self,
        manish_chart: ChartData,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """PNG bytes must start with the PNG magic header."""
        result = render_ashtakavarga_heatmap(manish_chart, manish_ashtakavarga)
        assert result is not None
        assert result[:4] == b"\x89PNG"

    def test_saves_to_file(
        self,
        manish_chart: ChartData,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """With output_path should save file and return None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_heatmap.png"
            result = render_ashtakavarga_heatmap(
                manish_chart,
                manish_ashtakavarga,
                output_path=str(path),
            )
            assert result is None
            assert path.exists()
            assert path.stat().st_size > 1000

    def test_creates_parent_dirs(
        self,
        manish_chart: ChartData,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Should create parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sub" / "dir" / "heatmap.png"
            render_ashtakavarga_heatmap(
                manish_chart,
                manish_ashtakavarga,
                output_path=str(path),
            )
            assert path.exists()

    def test_image_is_reproducible(
        self,
        manish_chart: ChartData,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Two renders of same data should produce same-size images."""
        img1 = render_ashtakavarga_heatmap(manish_chart, manish_ashtakavarga)
        img2 = render_ashtakavarga_heatmap(manish_chart, manish_ashtakavarga)
        assert img1 is not None and img2 is not None
        assert abs(len(img1) - len(img2)) < 200


class TestAshtakavargaData:
    """Test that the underlying data is correct for Manish's chart."""

    def test_sav_total_is_337(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Sarvashtakavarga total must always equal 337."""
        assert manish_ashtakavarga.total == 337

    def test_sarva_sum_equals_total(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Sum of sarva list must equal the total field."""
        assert sum(manish_ashtakavarga.sarva) == manish_ashtakavarga.total

    def test_bhinna_has_seven_planets(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Bhinna tables must contain exactly 7 planets (no Rahu/Ketu)."""
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        assert set(manish_ashtakavarga.bhinna.keys()) == expected

    def test_each_bhinna_has_twelve_signs(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Each planet's bhinna table must have 12 values."""
        for planet, values in manish_ashtakavarga.bhinna.items():
            assert len(values) == 12, f"{planet} has {len(values)} values"

    def test_bhinna_values_in_valid_range(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Each bhinna bindu must be 0-8 (8 possible contributors)."""
        for planet, values in manish_ashtakavarga.bhinna.items():
            for i, v in enumerate(values):
                assert 0 <= v <= 8, f"{planet} sign {i}: bindu {v} out of range"

    def test_sarva_has_twelve_signs(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Sarvashtakavarga must have 12 values."""
        assert len(manish_ashtakavarga.sarva) == 12

    def test_sarva_is_sum_of_bhinna(
        self,
        manish_ashtakavarga: AshtakavargaResult,
    ) -> None:
        """Each SAV value must equal sum of bhinna values for that sign."""
        planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        for sign_idx in range(12):
            expected = sum(manish_ashtakavarga.bhinna[p][sign_idx] for p in planets)
            assert manish_ashtakavarga.sarva[sign_idx] == expected, (
                f"Sign {sign_idx}: SAV {manish_ashtakavarga.sarva[sign_idx]} != sum {expected}"
            )
