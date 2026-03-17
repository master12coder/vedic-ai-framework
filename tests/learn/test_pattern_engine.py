"""Tests for the statistical pattern engine."""

import tempfile
from pathlib import Path

import pytest

from jyotish.learn.life_events_db import ChartRecord, LifeEvent, LifeEventsDB
from jyotish.learn.pattern_engine import (
    DEFAULT_MIN_SAMPLE,
    analyze_dasha_patterns,
    analyze_planet_house_patterns,
    analyze_remedy_effectiveness,
    analyze_yoga_patterns,
    format_pattern_report,
    get_all_patterns,
    _compute_confidence,
)


@pytest.fixture
def temp_db():
    """Provide a temporary LifeEventsDB that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_patterns.db")
        db = LifeEventsDB(db_path=db_path)
        yield db, db_path
        db.close()


@pytest.fixture
def populated_db(temp_db):
    """Provide a database pre-loaded with sample charts and events."""
    db, db_path = temp_db

    # Three charts with different lagnas
    cid1 = db.add_chart(ChartRecord(name="A", dob="01/01/1985", tob="06:00", lagna="Mithuna"))
    cid2 = db.add_chart(ChartRecord(name="B", dob="15/06/1990", tob="14:30", lagna="Mithuna"))
    cid3 = db.add_chart(ChartRecord(name="C", dob="20/11/1988", tob="21:00", lagna="Karka"))

    # Planet-house events: Jupiter in house 12 for three people
    db.add_event(LifeEvent(
        chart_id=cid1, event_date="2015-03-01", event_type="career",
        description="Promotion at work", dasha_lord="Jupiter",
        planets_involved="Jupiter", houses_involved="12", outcome="positive",
    ))
    db.add_event(LifeEvent(
        chart_id=cid2, event_date="2016-07-15", event_type="career",
        description="Lost job", dasha_lord="Jupiter",
        planets_involved="Jupiter", houses_involved="12", outcome="negative",
    ))
    db.add_event(LifeEvent(
        chart_id=cid3, event_date="2017-01-10", event_type="career",
        description="Lateral move", dasha_lord="Jupiter",
        planets_involved="Jupiter", houses_involved="12", outcome="positive",
    ))

    # Dasha events: Saturn mahadasha
    db.add_event(LifeEvent(
        chart_id=cid1, event_date="2010-05-01", event_type="health",
        dasha_lord="Saturn", outcome="negative",
    ))
    db.add_event(LifeEvent(
        chart_id=cid2, event_date="2011-08-01", event_type="health",
        dasha_lord="Saturn", outcome="negative",
    ))
    db.add_event(LifeEvent(
        chart_id=cid3, event_date="2012-02-01", event_type="career",
        dasha_lord="Saturn", outcome="neutral",
    ))

    # Yoga-related events via description
    db.add_event(LifeEvent(
        chart_id=cid1, event_date="2018-01-01", event_type="career",
        description="Gajakesari yoga activated — new authority role",
        outcome="positive",
    ))
    db.add_event(LifeEvent(
        chart_id=cid2, event_date="2019-04-01", event_type="education",
        description="Higher studies during Gajakesari period",
        outcome="positive",
    ))
    db.add_event(LifeEvent(
        chart_id=cid3, event_date="2020-09-01", event_type="career",
        description="Gajakesari effect — public recognition",
        outcome="positive",
    ))

    # Remedy events
    db.add_event(LifeEvent(
        chart_id=cid1, event_date="2019-06-01", event_type="remedy",
        description="Wore Yellow Sapphire for Jupiter", outcome="positive",
    ))
    db.add_event(LifeEvent(
        chart_id=cid2, event_date="2020-01-01", event_type="remedy",
        description="Hanuman Chalisa for Saturn", outcome="positive",
    ))
    db.add_event(LifeEvent(
        chart_id=cid3, event_date="2020-06-01", event_type="remedy",
        description="Blue Sapphire for Saturn", outcome="neutral",
    ))

    yield db, db_path


class TestEmptyDatabase:
    """Pattern analysis with no data should return empty results."""

    def test_empty_planet_house(self, temp_db):
        """Planet-house analysis on empty DB returns None."""
        _, db_path = temp_db
        assert analyze_planet_house_patterns(db_path, "Jupiter", 12) is None

    def test_empty_get_all_patterns(self, temp_db):
        """get_all_patterns on empty DB returns empty list."""
        _, db_path = temp_db
        assert get_all_patterns(db_path) == []


class TestPlanetHousePatterns:
    """Planet-house pattern analysis."""

    def test_jupiter_in_12th(self, populated_db):
        """Jupiter in 12th house should return a valid pattern."""
        _, db_path = populated_db
        result = analyze_planet_house_patterns(db_path, "Jupiter", 12)
        assert result is not None
        assert result.pattern_type == "planet_house"
        assert result.sample_size == 3
        assert result.positive_count == 2
        assert result.negative_count == 1
        assert result.neutral_count == 0
        assert result.description == "Jupiter in house 12"

    def test_below_min_sample(self, populated_db):
        """Pattern below minimum sample size should return None."""
        _, db_path = populated_db
        assert analyze_planet_house_patterns(db_path, "Jupiter", 12, min_sample=10) is None


class TestDashaPatterns:
    """Dasha-event pattern analysis."""

    def test_saturn_dasha(self, populated_db):
        """Saturn mahadasha should show negative-leaning pattern."""
        _, db_path = populated_db
        result = analyze_dasha_patterns(db_path, "Saturn")
        assert result is not None
        assert result.pattern_type == "dasha_event"
        assert result.sample_size == 3
        assert result.negative_count == 2
        assert result.description == "Mahadasha of Saturn"

    def test_jupiter_dasha(self, populated_db):
        """Jupiter mahadasha should be detected from career events."""
        _, db_path = populated_db
        result = analyze_dasha_patterns(db_path, "Jupiter")
        assert result is not None
        assert result.sample_size == 3


class TestYogaPatterns:
    """Yoga-outcome pattern analysis."""

    def test_gajakesari(self, populated_db):
        """Gajakesari yoga should show strongly positive pattern."""
        _, db_path = populated_db
        result = analyze_yoga_patterns(db_path, "Gajakesari")
        assert result is not None
        assert result.pattern_type == "yoga_outcome"
        assert result.sample_size == 3
        assert result.positive_count == 3
        assert result.dominant_outcome == "positive"


class TestRemedyEffectiveness:
    """Remedy effectiveness analysis."""

    def test_remedies(self, populated_db):
        """Remedy events should produce an effectiveness pattern."""
        _, db_path = populated_db
        result = analyze_remedy_effectiveness(db_path)
        assert result is not None
        assert result.pattern_type == "remedy_effectiveness"
        assert result.sample_size == 3
        assert result.positive_count == 2


class TestConfidenceCalculation:
    """Confidence scoring logic."""

    def test_zero_sample(self):
        """Zero-sample confidence should be 0.0."""
        assert _compute_confidence(0, 0) == 0.0

    def test_perfect_consistency_small_sample(self):
        """3/3 unanimous should produce moderate confidence (small sample)."""
        conf = _compute_confidence(3, 3)
        assert 0.3 < conf < 0.6  # consistent but sample is small

    def test_large_sample_high_consistency(self):
        """30/30 unanimous with large sample should yield high confidence."""
        conf = _compute_confidence(30, 30)
        assert conf > 0.9

    def test_split_outcomes_lower_confidence(self):
        """50-50 split should yield lower confidence than unanimity."""
        split_conf = _compute_confidence(10, 5)
        unanimous_conf = _compute_confidence(10, 10)
        assert split_conf < unanimous_conf


class TestGetAllPatterns:
    """Full discovery via get_all_patterns."""

    def test_discovers_patterns(self, populated_db):
        """get_all_patterns should find multiple pattern types."""
        _, db_path = populated_db
        patterns = get_all_patterns(db_path, min_sample=3)
        assert len(patterns) > 0
        types_found = {p.pattern_type for p in patterns}
        assert "planet_house" in types_found
        assert "dasha_event" in types_found

    def test_min_sample_filters(self, populated_db):
        """Raising min_sample should reduce the number of patterns."""
        _, db_path = populated_db
        patterns_low = get_all_patterns(db_path, min_sample=1)
        patterns_high = get_all_patterns(db_path, min_sample=100)
        assert len(patterns_low) >= len(patterns_high)
        assert patterns_high == []

    def test_nonexistent_db(self, tmp_path):
        """Non-existent database path should return empty list."""
        fake = str(tmp_path / "does_not_exist.db")
        assert get_all_patterns(fake) == []


class TestFormatReport:
    """Report formatting."""

    def test_empty_report(self):
        """Empty pattern list should produce a 'no patterns' message."""
        report = format_pattern_report([])
        assert "No statistical patterns" in report

    def test_populated_report(self, populated_db):
        """Report from real data should contain table headers and details."""
        _, db_path = populated_db
        patterns = get_all_patterns(db_path, min_sample=3)
        report = format_pattern_report(patterns)
        assert "# Statistical Pattern Report" in report
        assert "Confidence" in report
        assert "Patterns discovered" in report
