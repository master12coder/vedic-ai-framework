"""Tests for gemstone_weight — 10-factor gemstone ratti recommendation engine.

Safety tests are critical: Mithuna lagna must prohibit Pukhraj, Moonga, Moti
and recommend Panna. See CLAUDE.md non-negotiable safety rules.
"""

from __future__ import annotations

import pytest

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.gemstone_weight import compute_gemstone_weights
from daivai_products.decision.models import GemstoneReport, GemstoneWeight


# All 10 factor keys that must appear in factor_breakdown
_EXPECTED_FACTORS = {
    "body_weight_base",
    "avastha",
    "bav_bindus",
    "dignity",
    "combustion",
    "retrograde",
    "dasha",
    "lordship",
    "stone_density",
    "purpose",
}


class TestComputeGemstoneWeights:
    """Tests for compute_gemstone_weights()."""

    def test_returns_gemstone_report(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Must return a GemstoneReport model."""
        result = compute_gemstone_weights(manish_analysis)
        assert isinstance(result, GemstoneReport)

    @pytest.mark.safety
    def test_mithuna_lagna_pukhraj_prohibited(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Pukhraj (Yellow Sapphire) MUST be PROHIBITED for Mithuna lagna.

        Jupiter is 7th lord maraka for Mithuna — wearing Pukhraj strengthens
        the maraka and is dangerous. Non-negotiable safety rule.
        """
        result = compute_gemstone_weights(manish_analysis)
        assert result.lagna == "Mithuna"
        pukhraj_weights = [
            w for w in result.weights if "Pukhraj" in w.stone_hindi
        ]
        assert len(pukhraj_weights) > 0, "Pukhraj not found in gemstone weights"
        for w in pukhraj_weights:
            assert w.status == "PROHIBITED", (
                f"Pukhraj must be PROHIBITED for Mithuna, got {w.status}"
            )

    @pytest.mark.safety
    def test_mithuna_lagna_moonga_prohibited(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Moonga (Red Coral) MUST be PROHIBITED for Mithuna lagna.

        Mars is 6th and 11th lord (functional malefic) for Mithuna.
        """
        result = compute_gemstone_weights(manish_analysis)
        moonga_weights = [
            w for w in result.weights if "Moonga" in w.stone_hindi
        ]
        assert len(moonga_weights) > 0, "Moonga not found in gemstone weights"
        for w in moonga_weights:
            assert w.status == "PROHIBITED", (
                f"Moonga must be PROHIBITED for Mithuna, got {w.status}"
            )

    @pytest.mark.safety
    def test_mithuna_lagna_moti_prohibited(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Moti (Pearl) MUST be PROHIBITED for Mithuna lagna.

        Moon is 2nd lord maraka for Mithuna.
        """
        result = compute_gemstone_weights(manish_analysis)
        moti_weights = [
            w for w in result.weights if "Moti" in w.stone_hindi
        ]
        assert len(moti_weights) > 0, "Moti not found in gemstone weights"
        for w in moti_weights:
            assert w.status == "PROHIBITED", (
                f"Moti must be PROHIBITED for Mithuna, got {w.status}"
            )

    @pytest.mark.safety
    def test_mithuna_lagna_panna_recommended(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Panna (Emerald) should be RECOMMENDED for Mithuna lagna.

        Mercury is lagnesh (1st lord) for Mithuna — its stone is always safe.
        """
        result = compute_gemstone_weights(manish_analysis)
        panna_weights = [
            w for w in result.weights if "Panna" in w.stone_hindi
        ]
        assert len(panna_weights) > 0, "Panna not found in gemstone weights"
        for w in panna_weights:
            assert w.status == "RECOMMENDED", (
                f"Panna should be RECOMMENDED for Mithuna, got {w.status}"
            )

    @pytest.mark.safety
    def test_prohibited_stones_have_zero_ratti(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """PROHIBITED stones must have 0.0 recommended_ratti (never wear)."""
        result = compute_gemstone_weights(manish_analysis)
        for w in result.weights:
            if w.status == "PROHIBITED":
                assert w.recommended_ratti == 0.0, (
                    f"PROHIBITED {w.stone} has non-zero ratti {w.recommended_ratti}"
                )

    @pytest.mark.safety
    def test_recommended_stones_have_positive_ratti(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """RECOMMENDED stones must have positive recommended_ratti."""
        result = compute_gemstone_weights(manish_analysis)
        recommended = [w for w in result.weights if w.status == "RECOMMENDED"]
        assert len(recommended) > 0, "No RECOMMENDED stones found"
        for w in recommended:
            assert w.recommended_ratti > 0.0, (
                f"RECOMMENDED {w.stone} has zero ratti"
            )

    def test_free_alternatives_provided_for_prohibited(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """PROHIBITED stones must have free alternatives (mantra, color, daan)."""
        result = compute_gemstone_weights(manish_analysis)
        for w in result.weights:
            if w.status == "PROHIBITED":
                assert len(w.free_alternatives) > 0, (
                    f"No free alternatives for PROHIBITED {w.stone}"
                )
                # Should include mantra, color, or daan
                alt_text = " ".join(w.free_alternatives).lower()
                assert any(
                    kw in alt_text for kw in ["mantra", "color", "daan"]
                ), f"Alternatives for {w.stone} missing mantra/color/daan"

    def test_factor_breakdown_has_all_10_factors(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Each gemstone weight must have all 10 factors in the breakdown."""
        result = compute_gemstone_weights(manish_analysis)
        assert len(result.weights) > 0, "No gemstone weights computed"
        for w in result.weights:
            present_factors = set(w.factor_breakdown.keys())
            missing = _EXPECTED_FACTORS - present_factors
            assert not missing, (
                f"Missing factors for {w.stone}: {missing}"
            )

    def test_body_weight_affects_base_ratti(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Different body weights should produce different base ratti values."""
        result_70 = compute_gemstone_weights(manish_analysis, body_weight_kg=70.0)
        result_90 = compute_gemstone_weights(manish_analysis, body_weight_kg=90.0)
        # Both should have weights
        assert len(result_70.weights) > 0
        assert len(result_90.weights) > 0
        # Find a recommended stone in both and compare base_ratti
        for w70 in result_70.weights:
            if w70.status == "RECOMMENDED":
                w90 = next(
                    (w for w in result_90.weights if w.planet == w70.planet),
                    None,
                )
                if w90:
                    assert w90.base_ratti >= w70.base_ratti, (
                        f"Higher body weight should yield >= base ratti: "
                        f"70kg={w70.base_ratti}, 90kg={w90.base_ratti}"
                    )
                    break

    def test_lagna_is_mithuna(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Report must correctly identify the lagna as Mithuna."""
        result = compute_gemstone_weights(manish_analysis)
        assert result.lagna == "Mithuna"

    def test_lagna_lord_is_mercury(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Report must identify Mercury as lagna lord for Mithuna."""
        result = compute_gemstone_weights(manish_analysis)
        assert result.lagna_lord == "Mercury"

    @pytest.mark.safety
    def test_prohibited_stones_list_populated(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """GemstoneReport.prohibited_stones must list prohibited stone names."""
        result = compute_gemstone_weights(manish_analysis)
        assert len(result.prohibited_stones) > 0, "No prohibited stones listed"

    @pytest.mark.safety
    def test_safety_warnings_for_mithuna(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Mithuna lagna should produce safety warnings for dangerous stones."""
        result = compute_gemstone_weights(manish_analysis)
        assert len(result.safety_warnings) > 0, (
            "No safety warnings for Mithuna lagna"
        )

    def test_weights_sorted_by_status(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Weights should be sorted: RECOMMENDED first, then TEST, then PROHIBITED."""
        result = compute_gemstone_weights(manish_analysis)
        status_order = {"RECOMMENDED": 0, "TEST_WITH_CAUTION": 1, "PROHIBITED": 2}
        prev_rank = -1
        for w in result.weights:
            rank = status_order.get(w.status, 9)
            assert rank >= prev_rank or (
                rank == prev_rank
            ), f"Unsorted: {w.stone} ({w.status}) after rank {prev_rank}"
            prev_rank = rank

    def test_purpose_protection_reduces_ratti(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Protection purpose (0.8x) should produce lower ratti than growth (1.0x)."""
        result_growth = compute_gemstone_weights(
            manish_analysis, purpose="growth"
        )
        result_protect = compute_gemstone_weights(
            manish_analysis, purpose="protection"
        )
        for wg in result_growth.weights:
            if wg.status == "RECOMMENDED":
                wp = next(
                    (w for w in result_protect.weights if w.planet == wg.planet),
                    None,
                )
                if wp and wp.status == "RECOMMENDED":
                    assert wp.recommended_ratti <= wg.recommended_ratti, (
                        f"Protection ratti ({wp.recommended_ratti}) should be "
                        f"<= growth ratti ({wg.recommended_ratti}) for {wg.stone}"
                    )
                    break

    def test_each_weight_has_reasoning(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Every GemstoneWeight must have a non-empty reasoning string."""
        result = compute_gemstone_weights(manish_analysis)
        for w in result.weights:
            assert isinstance(w, GemstoneWeight)
            assert w.reasoning, f"Empty reasoning for {w.stone}"
