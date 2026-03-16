"""Test 6-layer validation pipeline."""

import pytest
import tempfile
from jyotish.learn.corrections import PanditCorrectionStore, PanditCorrection
from jyotish.learn.validator import SixLayerValidator, MultiSourceValidator


@pytest.fixture
def validator():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PanditCorrectionStore(data_dir=tmpdir)
        c = PanditCorrection(chart_name="Test", category="gemstone")
        store.add_correction(c)
        yield SixLayerValidator(store=store), store, c.id


class TestSixLayerValidator:
    def test_layer1_astronomical_pass(self, validator):
        v, store, cid = validator
        result = v.check_astronomical_facts(cid, contradicts_computation=False)
        assert result.is_valid
        assert result.layer == 1

    def test_layer1_astronomical_reject(self, validator):
        v, store, cid = validator
        result = v.check_astronomical_facts(cid, contradicts_computation=True)
        assert not result.is_valid
        assert result.new_status == "rejected"

    def test_layer2_scripture_align(self, validator):
        v, store, cid = validator
        result = v.check_scripture_reference(cid, aligns_with_scripture=True, scripture_ref="BPHS 19:8")
        assert result.is_valid
        assert result.layer == 2

    def test_layer2_scripture_skip(self, validator):
        v, store, cid = validator
        result = v.check_scripture_reference(cid, aligns_with_scripture=None)
        assert result.is_valid  # Skipped = pass
        assert result.confidence_delta == 0.0

    def test_layer3_life_event_confirm(self, validator):
        v, store, cid = validator
        result = v.validate_by_life_event(cid, event_matches=True, event_description="Marriage in 2015")
        assert result.is_valid
        assert result.layer == 3

    def test_layer4_second_opinion(self, validator):
        v, store, cid = validator
        result = v.validate_by_second_opinion(cid, second_pandit_agrees=True, pandit_name="Shastri Ji")
        assert result.is_valid
        assert result.layer == 4

    def test_layer5_trust_master(self, validator):
        v, store, cid = validator
        result = v.apply_trust_weight(cid, trust_score=0.85)
        assert result.confidence_delta == 0.2
        assert result.layer == 5

    def test_layer5_trust_unverified(self, validator):
        v, store, cid = validator
        result = v.apply_trust_weight(cid, trust_score=0.2)
        assert result.confidence_delta == -0.1

    def test_layer6_interpretation_pass(self, validator):
        v, store, cid = validator
        result = v.check_fact_vs_interpretation(cid, is_computation_override=False)
        assert result.is_valid
        assert result.layer == 6

    def test_layer6_computation_override_reject(self, validator):
        v, store, cid = validator
        result = v.check_fact_vs_interpretation(cid, is_computation_override=True)
        assert not result.is_valid
        assert result.new_status == "rejected"

    def test_backward_compat_alias(self):
        assert MultiSourceValidator is SixLayerValidator
