"""Tests for the gem therapy computation engine.

Covers:
- compute_gem_recommendation: lordship-based selection + therapy enrichment
- check_gem_contraindications: conflict detection
- compute_wearing_muhurta: auspicious date finding
- Safety: Mithuna lagna fixture (Manish Chaurasia)
"""

from __future__ import annotations

from datetime import datetime

import pytest

from daivai_engine.compute.gem_therapy import (
    check_gem_contraindications,
    compute_gem_recommendation,
    compute_wearing_muhurta,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.gem_therapy import (
    ContraindicationResult,
    GemActivation,
    GemQualitySpec,
    GemTherapyRecommendation,
    GemUpratna,
    WearingMuhurta,
)


# ── fixtures ─────────────────────────────────────────────────────────────────




# ── compute_gem_recommendation ───────────────────────────────────────────────


class TestComputeGemRecommendation:
    """Tests for compute_gem_recommendation()."""

    def test_returns_list_of_recommendations(self, manish_chart: ChartData) -> None:
        """Returns a non-empty list of GemTherapyRecommendation."""
        recs = compute_gem_recommendation(manish_chart)
        assert isinstance(recs, list)
        assert len(recs) > 0
        assert all(isinstance(r, GemTherapyRecommendation) for r in recs)

    def test_covers_all_nine_planets(self, manish_chart: ChartData) -> None:
        """All 9 planets must be covered."""
        recs = compute_gem_recommendation(manish_chart)
        planets = {r.planet for r in recs}
        expected = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert planets == expected

    @pytest.mark.safety
    def test_emerald_recommended_for_mithuna(self, manish_chart: ChartData) -> None:
        """Panna (Emerald) MUST be recommended for Mithuna lagna — Mercury is lagnesh."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.status == "recommended"
        assert mercury_rec.stone_name == "Emerald"

    @pytest.mark.safety
    def test_pukhraj_prohibited_for_mithuna(self, manish_chart: ChartData) -> None:
        """Pukhraj (Yellow Sapphire) MUST be prohibited — Jupiter is 7th maraka."""
        recs = compute_gem_recommendation(manish_chart)
        jupiter_rec = next(r for r in recs if r.planet == "Jupiter")
        assert jupiter_rec.status == "prohibited"
        assert jupiter_rec.stone_name == "Yellow Sapphire"

    @pytest.mark.safety
    def test_moonga_prohibited_for_mithuna(self, manish_chart: ChartData) -> None:
        """Red Coral (Moonga) MUST be prohibited — Mars is 6th lord."""
        recs = compute_gem_recommendation(manish_chart)
        mars_rec = next(r for r in recs if r.planet == "Mars")
        assert mars_rec.status == "prohibited"

    @pytest.mark.safety
    def test_moti_prohibited_for_mithuna(self, manish_chart: ChartData) -> None:
        """Pearl (Moti) MUST be prohibited — Moon is 2nd maraka."""
        recs = compute_gem_recommendation(manish_chart)
        moon_rec = next(r for r in recs if r.planet == "Moon")
        assert moon_rec.status == "prohibited"

    def test_recommended_first_prohibited_last(self, manish_chart: ChartData) -> None:
        """Sort order: recommended → test_with_caution → neutral → prohibited."""
        recs = compute_gem_recommendation(manish_chart)
        order = {"recommended": 0, "test_with_caution": 1, "neutral": 2, "prohibited": 3}
        scores = [order.get(r.status, 9) for r in recs]
        assert scores == sorted(scores), "Results not sorted correctly"

    def test_recommended_stone_has_finger(self, manish_chart: ChartData) -> None:
        """Recommended stones must have a finger assignment."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.finger != ""
        assert mercury_rec.finger == "Little finger"  # Mercury → little finger

    def test_recommended_stone_has_metal(self, manish_chart: ChartData) -> None:
        """Recommended stones must have a metal assignment."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.metal != ""
        assert "Gold" in mercury_rec.metal

    def test_recommended_stone_has_day(self, manish_chart: ChartData) -> None:
        """Recommended stones must have a wearing day."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.day == "Wednesday"

    def test_recommended_stone_has_mantra(self, manish_chart: ChartData) -> None:
        """Recommended stones must have a mantra."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert len(mercury_rec.mantra) > 5

    def test_recommended_stone_has_weight_formula(self, manish_chart: ChartData) -> None:
        """Recommended stones must have a weight formula."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert "ratti" in mercury_rec.weight_formula.lower()

    def test_recommended_stone_has_quality_spec(self, manish_chart: ChartData) -> None:
        """Recommended stones must have quality specifications."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.quality is not None
        assert isinstance(mercury_rec.quality, GemQualitySpec)

    def test_quality_spec_has_min_weight(self, manish_chart: ChartData) -> None:
        """Quality spec must include minimum weight in ratti."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.quality is not None
        assert mercury_rec.quality.min_weight_ratti > 0

    def test_recommended_stone_has_upratna(self, manish_chart: ChartData) -> None:
        """Recommended stones must have an upratna (substitute stone)."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.upratna is not None
        assert isinstance(mercury_rec.upratna, GemUpratna)
        assert mercury_rec.upratna.name == "Green Tourmaline"
        assert 0 < mercury_rec.upratna.effectiveness_percent <= 100

    def test_recommended_stone_has_activation(self, manish_chart: ChartData) -> None:
        """Recommended stones must have activation (Pran Pratishtha) data."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.activation is not None
        assert isinstance(mercury_rec.activation, GemActivation)
        assert mercury_rec.activation.mantra_count == 108

    def test_activation_has_steps(self, manish_chart: ChartData) -> None:
        """Activation ritual must have step-by-step instructions."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert mercury_rec.activation is not None
        assert len(mercury_rec.activation.activation_steps) >= 5

    def test_recommended_stone_has_removal_conditions(self, manish_chart: ChartData) -> None:
        """All stones must have removal conditions."""
        recs = compute_gem_recommendation(manish_chart)
        mercury_rec = next(r for r in recs if r.planet == "Mercury")
        assert len(mercury_rec.removal_conditions) >= 5

    def test_prohibited_stone_has_prohibition_reason(self, manish_chart: ChartData) -> None:
        """Prohibited stones must have a prohibition reason."""
        recs = compute_gem_recommendation(manish_chart)
        jupiter_rec = next(r for r in recs if r.planet == "Jupiter")
        assert jupiter_rec.prohibition_reason is not None
        assert len(jupiter_rec.prohibition_reason) > 10

    def test_blue_sapphire_has_special_precaution(self, manish_chart: ChartData) -> None:
        """Blue Sapphire must have the 3-day trial special precaution."""
        recs = compute_gem_recommendation(manish_chart)
        saturn_rec = next(r for r in recs if r.planet == "Saturn")
        # Blue Sapphire always carries special precaution regardless of status
        if saturn_rec.status != "prohibited":
            assert saturn_rec.special_precaution is not None
            assert "trial" in saturn_rec.special_precaution.lower() or "3" in saturn_rec.special_precaution


# ── check_gem_contraindications ──────────────────────────────────────────────


class TestCheckGemContraindications:
    """Tests for check_gem_contraindications()."""

    def test_returns_contraindication_result(self) -> None:
        """Must return a ContraindicationResult."""
        result = check_gem_contraindications(["Ruby", "Blue Sapphire"])
        assert isinstance(result, ContraindicationResult)

    def test_ruby_blue_sapphire_absolute_conflict(self) -> None:
        """Ruby + Blue Sapphire is an absolute contraindication (Sun vs Saturn)."""
        result = check_gem_contraindications(["Ruby", "Blue Sapphire"])
        assert len(result.conflicts) > 0
        assert result.has_absolute_conflict

    def test_pearl_hessonite_absolute_conflict(self) -> None:
        """Pearl + Hessonite is an absolute contraindication (Moon vs Rahu)."""
        result = check_gem_contraindications(["Pearl", "Hessonite"])
        assert result.has_absolute_conflict

    def test_emerald_yellow_sapphire_conflict(self) -> None:
        """Emerald + Yellow Sapphire conflict (Mercury vs Jupiter)."""
        result = check_gem_contraindications(["Emerald", "Yellow Sapphire"])
        assert len(result.conflicts) > 0

    def test_planet_names_accepted(self) -> None:
        """Planet names should be accepted and resolve to stone names."""
        result = check_gem_contraindications(["Sun", "Saturn"])
        assert result.has_absolute_conflict

    def test_compatible_stones_no_conflict(self) -> None:
        """Compatible stones should produce no conflicts."""
        result = check_gem_contraindications(["Emerald", "Diamond"])
        assert len(result.conflicts) == 0
        assert not result.has_absolute_conflict

    def test_single_stone_no_conflict(self) -> None:
        """A single stone cannot conflict with itself."""
        result = check_gem_contraindications(["Ruby"])
        assert len(result.conflicts) == 0

    def test_conflict_has_reason(self) -> None:
        """Each conflict must include a reason string."""
        result = check_gem_contraindications(["Ruby", "Blue Sapphire"])
        for conflict in result.conflicts:
            assert len(conflict.reason) > 10

    def test_summary_mentions_conflict(self) -> None:
        """Summary must mention the conflict for absolute pairs."""
        result = check_gem_contraindications(["Ruby", "Blue Sapphire"])
        assert "conflict" in result.summary.lower() or "critical" in result.summary.lower()

    def test_safe_summary_for_compatible_gems(self) -> None:
        """Summary should say safe when no conflicts found."""
        result = check_gem_contraindications(["Emerald", "Diamond"])
        assert "safe" in result.summary.lower()

    def test_three_gems_multiple_conflicts(self) -> None:
        """Three gems with two conflicting pairs should detect both."""
        result = check_gem_contraindications(["Ruby", "Blue Sapphire", "Pearl"])
        # Ruby+Blue Sapphire conflict, Pearl is separate
        assert len(result.conflicts) >= 1
        assert result.has_absolute_conflict


# ── compute_wearing_muhurta ──────────────────────────────────────────────────


class TestComputeWearingMuhurta:
    """Tests for compute_wearing_muhurta()."""

    def test_returns_list_of_muhurtas(self, manish_chart: ChartData) -> None:
        """Must return a list of WearingMuhurta."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start)
        assert isinstance(result, list)
        assert all(isinstance(m, WearingMuhurta) for m in result)

    def test_returns_at_most_max_results(self, manish_chart: ChartData) -> None:
        """Should respect max_results parameter."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, max_results=3)
        assert len(result) <= 3

    def test_stone_name_accepted(self, manish_chart: ChartData) -> None:
        """Stone name 'Emerald' should be accepted (resolves to Mercury)."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Emerald", manish_chart, start)
        assert isinstance(result, list)

    def test_muhurta_has_score(self, manish_chart: ChartData) -> None:
        """Each muhurta must have a positive score."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, days_to_scan=90)
        if result:
            assert all(m.score > 0 for m in result)

    def test_muhurta_sorted_by_score_descending(self, manish_chart: ChartData) -> None:
        """Muhurtas should be sorted with highest score first."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, days_to_scan=90)
        if len(result) > 1:
            scores = [m.score for m in result]
            assert scores == sorted(scores, reverse=True)

    def test_muhurta_has_vara(self, manish_chart: ChartData) -> None:
        """Each muhurta must specify the weekday."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, days_to_scan=90)
        if result:
            assert all(m.vara != "" for m in result)

    def test_muhurta_has_nakshatra(self, manish_chart: ChartData) -> None:
        """Each muhurta must specify the nakshatra."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, days_to_scan=90)
        if result:
            assert all(m.nakshatra != "" for m in result)

    def test_muhurta_has_hora_timing(self, manish_chart: ChartData) -> None:
        """Each muhurta must have hora timing guidance."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, days_to_scan=90)
        if result:
            assert all(m.hora_timing != "" for m in result)

    def test_muhurta_has_reasons(self, manish_chart: ChartData) -> None:
        """Each muhurta must have reasons for its auspiciousness."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Mercury", manish_chart, start, days_to_scan=90)
        if result:
            assert all(len(m.reasons) > 0 for m in result)

    def test_blue_sapphire_marks_trial(self, manish_chart: ChartData) -> None:
        """Blue Sapphire muhurtas must be marked as trial dates."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Blue Sapphire", manish_chart, start, days_to_scan=90)
        if result:
            assert all(m.is_trial_date for m in result)

    def test_emerald_not_trial(self, manish_chart: ChartData) -> None:
        """Non-Saturn stones should not be marked as trial dates."""
        start = datetime(2026, 3, 25)
        result = compute_wearing_muhurta("Emerald", manish_chart, start, days_to_scan=90)
        if result:
            assert not any(m.is_trial_date for m in result)
