"""Test prediction tracker."""

import pytest
import tempfile
from pathlib import Path
from jyotish.learn.prediction_tracker import PredictionTracker, Prediction


@pytest.fixture
def temp_tracker():
    with tempfile.TemporaryDirectory() as tmpdir:
        tracker = PredictionTracker(db_path=Path(tmpdir) / "test.db")
        yield tracker
        tracker.close()


class TestPredictionTracker:
    def test_log_prediction(self, temp_tracker):
        pred = Prediction(
            chart_id=1, prediction_date="2026-03-15",
            category="career", prediction="Promotion expected",
            confidence=0.7, dasha_lord="Jupiter",
        )
        pid = temp_tracker.log_prediction(pred)
        assert pid > 0

    def test_update_outcome(self, temp_tracker):
        pred = Prediction(chart_id=1, prediction_date="2026-01-01", category="health", prediction="Test")
        pid = temp_tracker.log_prediction(pred)
        temp_tracker.update_outcome(pid, "confirmed", "2026-03-01")
        preds = temp_tracker.get_predictions(outcome="confirmed")
        assert len(preds) == 1
        assert preds[0].outcome == "confirmed"

    def test_invalid_outcome_raises(self, temp_tracker):
        pred = Prediction(chart_id=1, prediction_date="2026-01-01", category="test", prediction="Test")
        pid = temp_tracker.log_prediction(pred)
        with pytest.raises(ValueError, match="Invalid outcome"):
            temp_tracker.update_outcome(pid, "invalid_status")

    def test_get_predictions_filter(self, temp_tracker):
        temp_tracker.log_prediction(Prediction(chart_id=1, prediction_date="2026-01-01", category="career", prediction="A"))
        temp_tracker.log_prediction(Prediction(chart_id=1, prediction_date="2026-02-01", category="health", prediction="B"))
        temp_tracker.log_prediction(Prediction(chart_id=2, prediction_date="2026-03-01", category="career", prediction="C"))

        career = temp_tracker.get_predictions(category="career")
        assert len(career) == 2

        chart1 = temp_tracker.get_predictions(chart_id=1)
        assert len(chart1) == 2

    def test_accuracy_dashboard(self, temp_tracker):
        p1 = temp_tracker.log_prediction(Prediction(chart_id=1, prediction_date="2026-01-01", category="career", prediction="A"))
        p2 = temp_tracker.log_prediction(Prediction(chart_id=1, prediction_date="2026-02-01", category="career", prediction="B"))
        p3 = temp_tracker.log_prediction(Prediction(chart_id=1, prediction_date="2026-03-01", category="health", prediction="C"))

        temp_tracker.update_outcome(p1, "confirmed")
        temp_tracker.update_outcome(p2, "not_occurred")
        temp_tracker.update_outcome(p3, "confirmed")

        dashboard = temp_tracker.get_accuracy_dashboard()
        assert dashboard["total_predictions"] == 3
        assert dashboard["pending"] == 0
        assert "career" in dashboard["categories"]
        assert dashboard["categories"]["career"]["accuracy"] == 50.0
        assert dashboard["categories"]["health"]["accuracy"] == 100.0

    def test_empty_dashboard(self, temp_tracker):
        dashboard = temp_tracker.get_accuracy_dashboard()
        assert dashboard["total_predictions"] == 0
        assert dashboard["overall_accuracy"] == 0.0
