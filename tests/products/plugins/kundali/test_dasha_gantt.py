"""Tests for the Dasha Gantt chart renderer."""
from __future__ import annotations

import pytest

from jyotish_engine.compute.chart import compute_chart
from jyotish_engine.compute.dasha import (
    compute_antardashas,
    compute_mahadashas,
    find_current_dasha,
)
from jyotish_engine.models.chart import ChartData
from jyotish_products.interpret.context import build_lordship_context
from jyotish_products.plugins.kundali.dasha_gantt import render_dasha_gantt


@pytest.fixture
def manish_chart() -> ChartData:
    """Manish Chaurasia — Mithuna lagna, current MD = Jupiter."""
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
def mithuna_ctx() -> dict:
    """Lordship context for Mithuna lagna."""
    return build_lordship_context("Mithuna")


@pytest.fixture
def dasha_data(manish_chart: ChartData) -> dict:
    """Pre-computed dasha periods for Manish's chart."""
    mahadashas = compute_mahadashas(manish_chart)
    current_md, current_ad, _pd = find_current_dasha(manish_chart)
    antardashas = compute_antardashas(current_md)
    return {
        "mahadashas": mahadashas,
        "current_md": current_md,
        "current_ad": current_ad,
        "antardashas": antardashas,
    }


class TestDashaGantt:
    """Tests for render_dasha_gantt."""

    def test_returns_png_bytes(
        self, manish_chart: ChartData, dasha_data: dict, mithuna_ctx: dict,
    ) -> None:
        """Should return valid PNG bytes when no output_path given."""
        result = render_dasha_gantt(
            chart=manish_chart,
            mahadashas=dasha_data["mahadashas"],
            current_md=dasha_data["current_md"],
            current_ad=dasha_data["current_ad"],
            antardashas=dasha_data["antardashas"],
            lordship_ctx=mithuna_ctx,
        )
        assert result is not None
        assert isinstance(result, bytes)
        # PNG magic bytes
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_saves_to_file(
        self, manish_chart: ChartData, dasha_data: dict, mithuna_ctx: dict, tmp_path,
    ) -> None:
        """Should save PNG to disk and return None."""
        out = tmp_path / "dasha_gantt.png"
        result = render_dasha_gantt(
            chart=manish_chart,
            mahadashas=dasha_data["mahadashas"],
            current_md=dasha_data["current_md"],
            current_ad=dasha_data["current_ad"],
            antardashas=dasha_data["antardashas"],
            lordship_ctx=mithuna_ctx,
            output_path=out,
        )
        assert result is None
        assert out.exists()
        assert out.stat().st_size > 1000
        # Verify PNG header on disk
        assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    def test_with_empty_antardashas(
        self, manish_chart: ChartData, dasha_data: dict, mithuna_ctx: dict,
    ) -> None:
        """Should handle empty antardasha list gracefully."""
        result = render_dasha_gantt(
            chart=manish_chart,
            mahadashas=dasha_data["mahadashas"],
            current_md=dasha_data["current_md"],
            current_ad=dasha_data["current_ad"],
            antardashas=[],
            lordship_ctx=mithuna_ctx,
        )
        assert result is not None
        assert isinstance(result, bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_with_empty_lordship_ctx(
        self, manish_chart: ChartData, dasha_data: dict,
    ) -> None:
        """Should handle missing lordship context (all bars gray)."""
        result = render_dasha_gantt(
            chart=manish_chart,
            mahadashas=dasha_data["mahadashas"],
            current_md=dasha_data["current_md"],
            current_ad=dasha_data["current_ad"],
            antardashas=dasha_data["antardashas"],
            lordship_ctx={},
        )
        assert result is not None
        assert result[:8] == b"\x89PNG\r\n\x1a\n"

    def test_current_md_is_jupiter_for_manish(
        self, dasha_data: dict,
    ) -> None:
        """Manish's current Mahadasha lord should be Jupiter."""
        assert dasha_data["current_md"].lord == "Jupiter"

    def test_nine_mahadashas(self, dasha_data: dict) -> None:
        """Should have exactly 9 Mahadasha periods."""
        assert len(dasha_data["mahadashas"]) == 9

    def test_returns_none_for_empty_mahadashas(
        self, manish_chart: ChartData, dasha_data: dict, mithuna_ctx: dict,
    ) -> None:
        """Should return None if no mahadashas are provided."""
        result = render_dasha_gantt(
            chart=manish_chart,
            mahadashas=[],
            current_md=dasha_data["current_md"],
            current_ad=dasha_data["current_ad"],
            antardashas=dasha_data["antardashas"],
            lordship_ctx=mithuna_ctx,
        )
        assert result is None
