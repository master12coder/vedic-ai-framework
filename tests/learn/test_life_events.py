"""Test SQLite life events database."""

import pytest
import tempfile
from pathlib import Path
from jyotish.learn.life_events_db import LifeEventsDB, ChartRecord, LifeEvent


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db = LifeEventsDB(db_path=Path(tmpdir) / "test.db")
        yield db
        db.close()


class TestLifeEventsDB:
    def test_add_chart(self, temp_db):
        chart = ChartRecord(name="Test", dob="15/08/1990", tob="06:30", place="Jaipur", lagna="Karka")
        chart_id = temp_db.add_chart(chart)
        assert chart_id > 0

    def test_get_chart(self, temp_db):
        chart = ChartRecord(name="Rajesh", dob="15/08/1990", tob="06:30", lagna="Karka")
        chart_id = temp_db.add_chart(chart)
        retrieved = temp_db.get_chart(chart_id)
        assert retrieved is not None
        assert retrieved.name == "Rajesh"
        assert retrieved.lagna == "Karka"

    def test_add_event(self, temp_db):
        chart_id = temp_db.add_chart(ChartRecord(name="Test", dob="01/01/1990", tob="12:00"))
        event = LifeEvent(
            chart_id=chart_id, event_date="2015-11-20",
            event_type="marriage", description="Got married",
            dasha_lord="Venus", antardasha_lord="Jupiter",
        )
        event_id = temp_db.add_event(event)
        assert event_id > 0

    def test_get_events(self, temp_db):
        chart_id = temp_db.add_chart(ChartRecord(name="Test", dob="01/01/1990", tob="12:00"))
        temp_db.add_event(LifeEvent(chart_id=chart_id, event_date="2015-01-01", event_type="career"))
        temp_db.add_event(LifeEvent(chart_id=chart_id, event_date="2016-06-01", event_type="marriage"))
        events = temp_db.get_events(chart_id)
        assert len(events) == 2

    def test_find_similar_events(self, temp_db):
        cid1 = temp_db.add_chart(ChartRecord(name="A", dob="01/01/1990", tob="12:00"))
        cid2 = temp_db.add_chart(ChartRecord(name="B", dob="01/01/1985", tob="06:00"))
        temp_db.add_event(LifeEvent(chart_id=cid1, event_date="2015-01-01", event_type="marriage", dasha_lord="Venus"))
        temp_db.add_event(LifeEvent(chart_id=cid2, event_date="2018-06-01", event_type="marriage", dasha_lord="Venus"))
        similar = temp_db.find_similar_events("marriage", dasha_lord="Venus")
        assert len(similar) == 2

    def test_pattern_stats(self, temp_db):
        cid = temp_db.add_chart(ChartRecord(name="Test", dob="01/01/1990", tob="12:00"))
        temp_db.add_event(LifeEvent(chart_id=cid, event_date="2015-01-01", event_type="career", dasha_lord="Saturn", outcome="positive"))
        temp_db.add_event(LifeEvent(chart_id=cid, event_date="2016-01-01", event_type="career", dasha_lord="Mercury", outcome="positive"))
        stats = temp_db.get_pattern_stats("career")
        assert stats["total_events"] == 2
        assert "Saturn" in stats["dasha_distribution"]

    def test_nonexistent_chart(self, temp_db):
        assert temp_db.get_chart(999) is None
