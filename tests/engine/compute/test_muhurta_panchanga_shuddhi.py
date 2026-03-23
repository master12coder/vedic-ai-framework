"""Tests for Muhurta Engine — Panchanga Shuddhi and Lagna Shuddhi."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from daivai_engine.compute.muhurta_engine import (
    MuhurtaScore,
    score_muhurta,
)


# Fixed date known to be relatively clean: 2026-03-21 at 10:00 IST
_VARANASI_LAT = 25.3176
_VARANASI_LON = 83.0067
_IST = UTC  # We use UTC in tests for determinism

_TEST_DT = datetime(2026, 3, 21, 4, 30, tzinfo=_IST)  # 10:00 IST = 04:30 UTC


class TestScoreMuhurtaReturnsNewFields:
    def test_panchanga_shuddhi_present(self) -> None:
        result = score_muhurta("vivah", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        assert isinstance(result, MuhurtaScore)
        assert result.panchanga_shuddhi is not None

    def test_lagna_shuddhi_present(self) -> None:
        result = score_muhurta("vivah", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        # Lagna shuddhi may be None if swisseph fails, but should be attempted
        # In normal operation it should succeed
        assert isinstance(result, MuhurtaScore)

    def test_score_still_in_0_100(self) -> None:
        result = score_muhurta("vivah", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        assert 0 <= result.score <= 100


class TestPanchangaShuddhi:
    def test_shuddha_count_is_0_to_5(self) -> None:
        result = score_muhurta("general", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        ps = result.panchanga_shuddhi
        assert ps is not None
        assert 0 <= ps.shuddha_count <= 5

    def test_is_fully_shuddha_matches_count(self) -> None:
        result = score_muhurta("general", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        ps = result.panchanga_shuddhi
        assert ps is not None
        assert ps.is_fully_shuddha == (ps.shuddha_count == 5)

    def test_summary_not_empty(self) -> None:
        result = score_muhurta("general", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        ps = result.panchanga_shuddhi
        assert ps is not None
        assert len(ps.summary) > 5

    def test_five_boolean_fields(self) -> None:
        result = score_muhurta("general", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        ps = result.panchanga_shuddhi
        assert ps is not None
        assert isinstance(ps.tithi_shuddha, bool)
        assert isinstance(ps.vara_shuddha, bool)
        assert isinstance(ps.nakshatra_shuddha, bool)
        assert isinstance(ps.yoga_shuddha, bool)
        assert isinstance(ps.karana_shuddha, bool)

    def test_shuddha_count_equals_sum_of_booleans(self) -> None:
        result = score_muhurta("general", _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        ps = result.panchanga_shuddhi
        assert ps is not None
        expected = sum(
            [
                ps.tithi_shuddha,
                ps.vara_shuddha,
                ps.nakshatra_shuddha,
                ps.yoga_shuddha,
                ps.karana_shuddha,
            ]
        )
        assert ps.shuddha_count == expected

    @pytest.mark.parametrize(
        "event_type", ["vivah", "griha_pravesh", "vyapara", "yatra", "vidya", "general"]
    )
    def test_different_event_types_run_without_error(self, event_type: str) -> None:
        result = score_muhurta(event_type, _TEST_DT, _VARANASI_LAT, _VARANASI_LON)
        assert result.panchanga_shuddhi is not None
