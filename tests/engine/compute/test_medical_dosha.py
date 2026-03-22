"""Tests for Ayurvedic Tridosha computation from birth chart."""

from __future__ import annotations

from daivai_engine.compute.medical_dosha import (
    _dignity_modifier,
    _load_rules,
    compute_tridosha,
)
from daivai_engine.models.medical import TridoshaBalance


class TestLoadRules:
    """Tests for the YAML rules loading."""

    def test_rules_loaded_as_dict(self) -> None:
        rules = _load_rules()
        assert isinstance(rules, dict)

    def test_tridosha_weights_key_present(self) -> None:
        rules = _load_rules()
        assert "tridosha_weights" in rules

    def test_three_doshas_in_weights(self) -> None:
        rules = _load_rules()
        weights = rules["tridosha_weights"]
        assert "vata" in weights
        assert "pitta" in weights
        assert "kapha" in weights

    def test_dignity_modifiers_present(self) -> None:
        rules = _load_rules()
        assert "tridosha_dignity_modifiers" in rules


class TestDignityModifier:
    """Tests for the _dignity_modifier() function."""

    def test_exalted_gives_high_modifier(self, manish_chart) -> None:
        # Create a fake planet-like object with exalted dignity
        class FakePlanet:
            dignity = "exalted"
            is_combust = False
            is_retrograde = False

        mod = _dignity_modifier(FakePlanet())
        assert mod >= 1.0

    def test_debilitated_gives_low_modifier(self) -> None:
        class FakePlanet:
            dignity = "debilitated"
            is_combust = False
            is_retrograde = False

        mod = _dignity_modifier(FakePlanet())
        assert mod <= 1.0

    def test_combust_reduces_modifier(self) -> None:
        class FakeExalted:
            dignity = "exalted"
            is_combust = True
            is_retrograde = False

        class FakeExaltedNotCombust:
            dignity = "exalted"
            is_combust = False
            is_retrograde = False

        combust_mod = _dignity_modifier(FakeExalted())
        normal_mod = _dignity_modifier(FakeExaltedNotCombust())
        assert combust_mod <= normal_mod


class TestComputeTridosha:
    """Tests for compute_tridosha()."""

    def test_returns_tridosha_balance(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert isinstance(result, TridoshaBalance)

    def test_percentages_sum_to_100(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        total = result.vata_percentage + result.pitta_percentage + result.kapha_percentage
        assert abs(total - 100.0) < 0.5, f"Sum: {total}"

    def test_all_scores_positive(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert result.vata_score > 0
        assert result.pitta_score > 0
        assert result.kapha_score > 0

    def test_dominant_dosha_is_valid(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert result.dominant_dosha in ("Vata", "Pitta", "Kapha")

    def test_secondary_dosha_is_valid(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert result.secondary_dosha in ("Vata", "Pitta", "Kapha")

    def test_dominant_not_same_as_secondary(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert result.dominant_dosha != result.secondary_dosha

    def test_constitution_type_is_non_empty(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert result.constitution_type

    def test_imbalance_risk_is_valid(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert result.imbalance_risk in ("low", "moderate", "high")

    def test_dominant_has_highest_score(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        scores = {
            "Vata": result.vata_score,
            "Pitta": result.pitta_score,
            "Kapha": result.kapha_score,
        }
        highest = max(scores, key=lambda k: scores[k])
        assert result.dominant_dosha == highest

    def test_planet_lists_non_empty(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        # At least some planets should contribute to each dosha
        assert len(result.vata_planets) > 0
        assert len(result.pitta_planets) > 0
        assert len(result.kapha_planets) > 0

    def test_description_contains_constitution(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        assert "Constitution" in result.description

    def test_percentages_in_range(self, manish_chart) -> None:
        result = compute_tridosha(manish_chart)
        for pct in [result.vata_percentage, result.pitta_percentage, result.kapha_percentage]:
            assert 0.0 <= pct <= 100.0
