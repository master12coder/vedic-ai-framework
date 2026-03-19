"""Tests for the advanced muhurta engine."""

from __future__ import annotations

from datetime import UTC, datetime

from daivai_engine.compute.muhurta_engine import score_muhurta


class TestMuhurtaEngine:
    def test_score_returns_result(self) -> None:
        dt = datetime(2026, 3, 19, 10, 0, tzinfo=UTC)
        result = score_muhurta("vivah", dt, 25.3176, 83.0067)
        assert 0 <= result.score <= 100
        assert result.event_type == "vivah"

    def test_has_doshas(self) -> None:
        dt = datetime(2026, 3, 19, 10, 0, tzinfo=UTC)
        result = score_muhurta("general", dt, 25.3176, 83.0067)
        assert len(result.doshas) >= 5

    def test_auspicious_flag(self) -> None:
        dt = datetime(2026, 3, 19, 10, 0, tzinfo=UTC)
        result = score_muhurta("vyapara", dt, 25.3176, 83.0067)
        assert result.is_auspicious == (result.score >= 70)

    def test_dosha_count_consistent(self) -> None:
        dt = datetime(2026, 6, 15, 9, 0, tzinfo=UTC)
        result = score_muhurta("griha_pravesh", dt, 28.6139, 77.209)
        assert result.doshas_present + result.doshas_absent == len(result.doshas)

    def test_different_events_may_score_differently(self) -> None:
        dt = datetime(2026, 4, 10, 10, 0, tzinfo=UTC)
        vivah = score_muhurta("vivah", dt, 25.3176, 83.0067)
        vyapara = score_muhurta("vyapara", dt, 25.3176, 83.0067)
        # Same panchang but different event rules
        assert isinstance(vivah.score, int)
        assert isinstance(vyapara.score, int)
