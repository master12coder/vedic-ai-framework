"""Tests for synchronised family dasha timeline."""

from __future__ import annotations

from daivai_engine.compute.dasha_sync import compute_dasha_sync
from daivai_engine.models.chart import ChartData


def test_dasha_sync_returns_result(manish_chart: ChartData):
    """compute_dasha_sync produces a valid DashaSyncResult for one chart."""
    result = compute_dasha_sync([manish_chart])
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.name == manish_chart.name
    assert entry.current_md_lord != ""
    assert entry.md_nature.planet == entry.current_md_lord
    assert entry.md_start < entry.md_end
    assert len(result.summary) > 0


def test_dasha_sync_multiple_charts(manish_chart: ChartData, sample_chart: ChartData):
    """Two charts produce two entries."""
    result = compute_dasha_sync([manish_chart, sample_chart])
    assert len(result.entries) == 2
    names = {e.name for e in result.entries}
    assert manish_chart.name in names
    assert sample_chart.name in names


def test_dasha_sync_md_nature_classified(manish_chart: ChartData):
    """MD lord's functional nature should have a valid classification."""
    result = compute_dasha_sync([manish_chart])
    entry = result.entries[0]
    assert entry.md_nature.classification in (
        "benefic", "malefic", "yogakaraka", "maraka", "neutral"
    )
    assert entry.md_nature.lagna_sign == manish_chart.lagna_sign


def test_dasha_sync_windows_are_lists(manish_chart: ChartData, sample_chart: ChartData):
    """Favorable and challenging windows should be string lists."""
    result = compute_dasha_sync([manish_chart, sample_chart])
    assert isinstance(result.favorable_windows, list)
    assert isinstance(result.challenging_windows, list)
    for w in result.favorable_windows + result.challenging_windows:
        assert isinstance(w, str)


def test_dasha_sync_summary_contains_names(manish_chart: ChartData):
    """Summary should mention each member's name."""
    result = compute_dasha_sync([manish_chart])
    assert manish_chart.name in result.summary
