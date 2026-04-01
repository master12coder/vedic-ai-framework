"""Tests for cross_validator — D1 vs D9 consistency checks."""

from __future__ import annotations

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.cross_validator import validate_cross_chart
from daivai_products.decision.models import CrossChartCheck, CrossChartValidation


# The seven classical planets validated by the cross-chart module
_SEVEN_PLANETS = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}

# Valid pattern codes from _classify_pattern
_VALID_PATTERNS = {
    "strong_confirmed",
    "neech_bhanga_potential",
    "d1_weakened",
    "vargottam_strong",
    "neutral",
    "mixed",
}


class TestValidateCrossChart:
    """Tests for validate_cross_chart()."""

    def test_returns_crosschart_validation(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Must return a CrossChartValidation model."""
        result = validate_cross_chart(manish_analysis)
        assert isinstance(result, CrossChartValidation)

    def test_checks_all_seven_planets(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Must produce checks for Sun through Saturn (7 classical planets)."""
        result = validate_cross_chart(manish_analysis)
        checked_planets = {c.planet for c in result.checks}
        assert checked_planets == _SEVEN_PLANETS, (
            f"Expected {_SEVEN_PLANETS}, got {checked_planets}"
        )

    def test_consistency_score_between_0_and_1(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Consistency score must be in [0.0, 1.0] range."""
        result = validate_cross_chart(manish_analysis)
        assert 0.0 <= result.consistency_score <= 1.0

    def test_empty_navamsha_returns_empty_report(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """When navamsha_positions is empty, report should have no checks."""
        # Create a copy with empty navamsha_positions
        empty_analysis = manish_analysis.model_copy(
            update={"navamsha_positions": []}
        )
        result = validate_cross_chart(empty_analysis)
        assert len(result.checks) == 0
        assert result.consistency_score == 0.0
        assert result.vargottam_count == 0
        assert "No Navamsha data" in result.summary

    def test_vargottam_planets_marked_consistent(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Any vargottam planet must be marked as consistent with
        pattern 'vargottam_strong'."""
        result = validate_cross_chart(manish_analysis)
        for check in result.checks:
            if check.is_vargottam:
                assert check.is_consistent, (
                    f"Vargottam {check.planet} should be consistent"
                )
                assert check.pattern == "vargottam_strong", (
                    f"Vargottam {check.planet} should have pattern 'vargottam_strong'"
                )

    def test_each_check_has_valid_fields(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Every CrossChartCheck must have populated sign, dignity, pattern."""
        result = validate_cross_chart(manish_analysis)
        for check in result.checks:
            assert isinstance(check, CrossChartCheck)
            assert check.planet in _SEVEN_PLANETS
            assert check.d1_sign, f"Empty D1 sign for {check.planet}"
            assert check.d9_sign, f"Empty D9 sign for {check.planet}"
            assert check.d1_dignity, f"Empty D1 dignity for {check.planet}"
            assert check.d9_dignity, f"Empty D9 dignity for {check.planet}"
            assert check.pattern in _VALID_PATTERNS, (
                f"Invalid pattern '{check.pattern}' for {check.planet}"
            )
            assert check.explanation, f"Empty explanation for {check.planet}"

    def test_summary_mentions_score(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Summary string should include the consistency score percentage."""
        result = validate_cross_chart(manish_analysis)
        assert "consistency score" in result.summary.lower()

    def test_vargottam_count_matches_checks(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """vargottam_count should match the number of vargottam checks."""
        result = validate_cross_chart(manish_analysis)
        expected = sum(1 for c in result.checks if c.is_vargottam)
        assert result.vargottam_count == expected

    def test_strong_confirmations_count_matches(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """strong_confirmations count should match checks with that pattern."""
        result = validate_cross_chart(manish_analysis)
        expected = sum(1 for c in result.checks if c.pattern == "strong_confirmed")
        assert result.strong_confirmations == expected

    def test_weakened_count_matches(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """weakened_count should match checks with pattern 'd1_weakened'."""
        result = validate_cross_chart(manish_analysis)
        expected = sum(1 for c in result.checks if c.pattern == "d1_weakened")
        assert result.weakened_count == expected

    def test_neech_bhanga_count_matches(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """neech_bhanga_count should match checks with that pattern."""
        result = validate_cross_chart(manish_analysis)
        expected = sum(
            1 for c in result.checks if c.pattern == "neech_bhanga_potential"
        )
        assert result.neech_bhanga_count == expected
