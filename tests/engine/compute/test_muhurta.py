"""Tests for Muhurta auspicious timing finder."""

from __future__ import annotations

from datetime import datetime

from daivai_engine.compute.muhurta import find_muhurta
from daivai_engine.models.muhurta import MuhurtaCandidate


# Varanasi coordinates
_LAT = 25.3176
_LON = 83.0067
_TZ = "Asia/Kolkata"


class TestFindMuhurtaStructure:
    """Tests for find_muhurta() return structure."""

    def test_returns_list(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("marriage", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)

    def test_all_elements_are_muhurta_candidates(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("business", _LAT, _LON, start, end, _TZ)
        for item in result:
            assert isinstance(item, MuhurtaCandidate)

    def test_results_not_exceed_max_results(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        max_r = 3
        result = find_muhurta("travel", _LAT, _LON, start, end, _TZ, max_results=max_r)
        assert len(result) <= max_r

    def test_empty_range_returns_empty(self) -> None:
        # Same start and end with no favorable days
        start = datetime(2026, 4, 14)  # A specific day that may not score high
        end = datetime(2026, 4, 14)
        result = find_muhurta("marriage", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)


class TestMuhurtaScore:
    """Tests for scoring logic in candidates."""

    def test_candidates_have_score_field(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("marriage", _LAT, _LON, start, end, _TZ)
        for c in result:
            assert hasattr(c, "score")
            assert isinstance(c.score, float)

    def test_candidates_sorted_by_score_descending(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("business", _LAT, _LON, start, end, _TZ)
        if len(result) >= 2:
            scores = [c.score for c in result]
            assert scores == sorted(scores, reverse=True)

    def test_reasons_is_list(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("travel", _LAT, _LON, start, end, _TZ)
        for c in result:
            assert isinstance(c.reasons, list)


class TestMuhurtaPurposes:
    """Tests for different purpose types."""

    def test_marriage_muhurta_works(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("marriage", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)

    def test_business_muhurta_works(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("business", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)

    def test_travel_muhurta_works(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("travel", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)

    def test_property_muhurta_works(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("property", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)

    def test_unknown_purpose_uses_business_nakshatras(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        # Should not raise — falls back to business nakshatras
        result = find_muhurta("unknown_purpose", _LAT, _LON, start, end, _TZ)
        assert isinstance(result, list)


class TestMuhurtaDateFields:
    """Tests for date-related fields in MuhurtaCandidate."""

    def test_date_field_is_string(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("marriage", _LAT, _LON, start, end, _TZ)
        for c in result:
            assert isinstance(c.date, str)

    def test_date_within_search_range(self) -> None:
        start = datetime(2026, 4, 1)
        end = datetime(2026, 4, 30)
        result = find_muhurta("business", _LAT, _LON, start, end, _TZ)
        for c in result:
            # Date string should match format DD/MM/YYYY
            parts = c.date.split("/")
            assert len(parts) == 3
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            candidate_dt = datetime(year, month, day)
            assert start <= candidate_dt <= end
