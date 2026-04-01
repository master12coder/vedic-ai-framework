"""Tests for confidence scoring — per-section 0-100 confidence scores."""

from __future__ import annotations

from daivai_engine.models.analysis import FullChartAnalysis
from daivai_products.decision.confidence import compute_confidence
from daivai_products.decision.models import ConfidenceReport, SectionConfidence


# All sections scored by the confidence module
_EXPECTED_SECTIONS = {
    "career",
    "marriage",
    "health",
    "wealth",
    "education",
    "spiritual",
    "children",
    "longevity",
    "timing",
}


class TestComputeConfidence:
    """Tests for compute_confidence()."""

    def test_returns_confidence_report(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Must return a ConfidenceReport model."""
        result = compute_confidence(manish_analysis)
        assert isinstance(result, ConfidenceReport)

    def test_all_sections_scored(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Must score all expected life-area sections."""
        result = compute_confidence(manish_analysis)
        scored_sections = {s.section for s in result.sections}
        assert scored_sections == _EXPECTED_SECTIONS, (
            f"Missing sections: {_EXPECTED_SECTIONS - scored_sections}"
        )

    def test_scores_between_0_and_100(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Every section score must be in [0, 100]."""
        result = compute_confidence(manish_analysis)
        for section in result.sections:
            assert isinstance(section, SectionConfidence)
            assert 0 <= section.score <= 100, (
                f"Score {section.score} out of range for {section.section}"
            )

    def test_overall_score_is_weighted_average(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Overall score should be a weighted average of section scores."""
        result = compute_confidence(manish_analysis)
        # Manually compute weighted average using known weights
        weights = {
            "career": 1.5,
            "marriage": 1.3,
            "health": 1.5,
            "wealth": 1.2,
            "education": 1.0,
            "spiritual": 0.8,
            "children": 1.0,
            "longevity": 1.2,
            "timing": 1.0,
        }
        total_weight = sum(weights.get(s.section, 1.0) for s in result.sections)
        weighted_sum = sum(
            s.score * weights.get(s.section, 1.0) for s in result.sections
        )
        expected = round(weighted_sum / total_weight) if total_weight > 0 else 50
        expected = max(0, min(100, expected))
        assert result.overall_score == expected, (
            f"Overall {result.overall_score} != weighted avg {expected}"
        )

    def test_birth_time_quality_detected(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Birth time quality must be one of exact/approximate/unknown."""
        result = compute_confidence(manish_analysis)
        assert result.birth_time_quality in {"exact", "approximate", "unknown"}

    def test_overall_score_in_range(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Overall score must be in [0, 100]."""
        result = compute_confidence(manish_analysis)
        assert 0 <= result.overall_score <= 100

    def test_section_has_key_planets(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Each section should list key planets relevant to that life area."""
        result = compute_confidence(manish_analysis)
        for section in result.sections:
            assert isinstance(section.key_planets, list)
            assert len(section.key_planets) > 0, (
                f"No key planets for {section.section}"
            )

    def test_boosters_and_penalties_are_lists(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Boosters, penalties, and caveats must be lists of strings."""
        result = compute_confidence(manish_analysis)
        for section in result.sections:
            assert isinstance(section.boosters, list)
            assert isinstance(section.penalties, list)
            assert isinstance(section.caveats, list)
            for b in section.boosters:
                assert isinstance(b, str)
            for p in section.penalties:
                assert isinstance(p, str)
            for c in section.caveats:
                assert isinstance(c, str)

    def test_birth_time_caveats_populated(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Birth time caveats should be a list (possibly non-empty)."""
        result = compute_confidence(manish_analysis)
        assert isinstance(result.birth_time_caveats, list)

    def test_career_includes_saturn_as_key_planet(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Career section should include Saturn as a key planet."""
        result = compute_confidence(manish_analysis)
        career = next(s for s in result.sections if s.section == "career")
        assert "Saturn" in career.key_planets

    def test_marriage_includes_venus_as_key_planet(
        self, manish_analysis: FullChartAnalysis
    ) -> None:
        """Marriage section should include Venus as a key planet."""
        result = compute_confidence(manish_analysis)
        marriage = next(s for s in result.sections if s.section == "marriage")
        assert "Venus" in marriage.key_planets
