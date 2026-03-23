"""Tests for the HTML kundali context builder."""

from __future__ import annotations

from daivai_engine.models.chart import ChartData
from daivai_products.plugins.kundali.html_context import build_kundali_context


class TestBuildKundaliContext:
    def test_context_has_all_required_keys(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        required_keys = [
            "chart",
            "lordship_ctx",
            "benefics",
            "malefics",
            "yogakaraka",
            "md",
            "ad",
            "mahadashas",
            "antardashas",
            "yogas",
            "shadbala",
            "avk",
            "d1_svg",
            "d9_svg",
            "dasha_bars",
            "ad_bars",
            "shadbala_data",
            "avk_grid",
            "planet_rows",
            "golden",
            "recommended_stones",
            "prohibited_stones",
            "gemstone_results",
            "fmt",
            "signs_hi",
            "planet_hi",
        ]
        for key in required_keys:
            assert key in ctx, f"Missing key '{key}' in context"

    def test_d1_svg_is_valid(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        assert ctx["d1_svg"].startswith("<svg")
        assert ctx["d1_svg"].strip().endswith("</svg>")

    def test_d9_svg_is_valid(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        assert ctx["d9_svg"].startswith("<svg")

    def test_dasha_bars_sum_to_100(self, manish_chart: ChartData) -> None:
        """Dasha bar percentages should sum close to 100%."""
        ctx = build_kundali_context(manish_chart)
        total = sum(bar["pct"] for bar in ctx["dasha_bars"])
        assert 98.0 <= total <= 102.0, f"Dasha bars sum to {total}%"

    def test_ad_bars_sum_to_100(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        total = sum(bar["pct"] for bar in ctx["ad_bars"])
        assert 98.0 <= total <= 102.0, f"AD bars sum to {total}%"

    def test_dasha_bars_have_one_current(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        current_count = sum(1 for bar in ctx["dasha_bars"] if bar["is_current"])
        assert current_count == 1

    def test_shadbala_data_has_seven_planets(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        assert len(ctx["shadbala_data"]) == 7

    def test_shadbala_colors_correct(self, manish_chart: ChartData) -> None:
        """Strong planets should have green bars, weak ones red."""
        ctx = build_kundali_context(manish_chart)
        for s in ctx["shadbala_data"]:
            if s["is_strong"]:
                assert s["bar_color"] == "#2E7D32"
            else:
                assert s["bar_color"] == "#C62828"

    def test_avk_grid_has_eight_rows(self, manish_chart: ChartData) -> None:
        """7 planets + SAV row."""
        ctx = build_kundali_context(manish_chart)
        assert len(ctx["avk_grid"]["rows"]) == 8

    def test_avk_grid_has_twelve_cells_per_row(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        for row in ctx["avk_grid"]["rows"]:
            assert len(row["cells"]) == 12

    def test_planet_rows_has_nine_planets(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        assert len(ctx["planet_rows"]) == 9

    def test_planet_rows_have_motion_symbols(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        for row in ctx["planet_rows"]:
            assert row["motion"] in ("→", "↩ वक्री", "☀ अस्त")

    def test_mithuna_has_prohibited_stones(self, manish_chart: ChartData) -> None:
        """Mithuna lagna should have prohibited stones."""
        ctx = build_kundali_context(manish_chart)
        assert len(ctx["prohibited_stones"]) > 0

    def test_summary_format(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart, fmt="summary")
        assert ctx["fmt"] == "summary"

    def test_golden_period_present(self, manish_chart: ChartData) -> None:
        ctx = build_kundali_context(manish_chart)
        # Golden period may or may not be found, but the key should exist
        assert "golden" in ctx
