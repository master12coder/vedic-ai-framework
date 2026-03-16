"""Test trust scoring system."""

import pytest
import tempfile
from jyotish.learn.trust_scorer import TrustScorer, PanditTrustScore


@pytest.fixture
def temp_scorer():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield TrustScorer(data_dir=tmpdir)


class TestTrustScorer:
    def test_new_pandit_is_unverified(self, temp_scorer):
        score = temp_scorer.get_score("New Pandit")
        assert score.trust_level == "UNVERIFIED"
        assert score.trust_score == 0.3

    def test_record_correction(self, temp_scorer):
        temp_scorer.record_correction("Pandit A", "gemstone")
        score = temp_scorer.get_score("Pandit A")
        assert score.total_corrections == 1
        assert score.categories["gemstone"] == 1

    def test_record_validation_increases_accuracy(self, temp_scorer):
        temp_scorer.record_correction("Pandit A")
        temp_scorer.record_validation("Pandit A")
        score = temp_scorer.get_score("Pandit A")
        assert score.validated_count == 1
        assert score.accuracy > 0

    def test_record_dispute_decreases_accuracy(self, temp_scorer):
        temp_scorer.record_correction("Pandit A")
        temp_scorer.record_validation("Pandit A")
        temp_scorer.record_dispute("Pandit A")
        score = temp_scorer.get_score("Pandit A")
        assert score.disputed_count == 1
        assert score.accuracy == 0.5  # 1 validated, 1 disputed

    def test_master_level(self, temp_scorer):
        name = "Master Pandit"
        for _ in range(15):
            temp_scorer.record_correction(name)
            temp_scorer.record_validation(name)
        score = temp_scorer.get_score(name)
        assert score.trust_level == "MASTER"
        assert score.trust_score >= 0.8

    def test_get_all_scores(self, temp_scorer):
        temp_scorer.record_correction("A")
        temp_scorer.record_correction("B")
        scores = temp_scorer.get_all_scores()
        assert len(scores) == 2

    def test_get_weight(self, temp_scorer):
        temp_scorer.record_correction("A")
        weight = temp_scorer.get_weight("A")
        assert 0 <= weight <= 1.0
