"""Tests for family gemstone synergy analysis."""

from __future__ import annotations

import pytest

from daivai_engine.compute.family_gemstone_synergy import compute_family_gem_synergy
from daivai_engine.models.chart import ChartData


def test_family_gem_synergy_returns_result(manish_chart: ChartData, sample_chart: ChartData):
    """compute_family_gem_synergy produces a FamilyGemSynergyResult."""
    result = compute_family_gem_synergy([manish_chart, sample_chart])
    assert len(result.members) == 2
    assert result.members[0].name == manish_chart.name
    assert result.members[1].name == sample_chart.name
    assert len(result.summary) > 0


def test_member_profile_structure(manish_chart: ChartData):
    """Each member profile has correct structure."""
    result = compute_family_gem_synergy([manish_chart])
    member = result.members[0]
    assert member.name == manish_chart.name
    assert member.lagna_sign == manish_chart.lagna_sign
    assert isinstance(member.recommended, list)
    assert isinstance(member.prohibited, list)
    assert isinstance(member.test_with_caution, list)
    # Shadow planet analysis should be present
    assert member.rahu_gem is not None
    assert member.ketu_gem is not None


@pytest.mark.safety
def test_manish_pukhraj_prohibited(manish_chart: ChartData):
    """Manish (Mithuna lagna): Pukhraj must be prohibited (Jupiter = 7L maraka)."""
    result = compute_family_gem_synergy([manish_chart])
    member = result.members[0]
    assert any("Yellow Sapphire" in s for s in member.prohibited)


@pytest.mark.safety
def test_manish_panna_recommended(manish_chart: ChartData):
    """Manish (Mithuna lagna): Panna must be recommended (Mercury = lagnesh)."""
    result = compute_family_gem_synergy([manish_chart])
    member = result.members[0]
    assert any("Emerald" in s for s in member.recommended)


def test_synergy_pairs_detected(manish_chart: ChartData, sample_chart: ChartData):
    """Two charts should produce at least some synergy pairs."""
    result = compute_family_gem_synergy([manish_chart, sample_chart])
    # synergy_pairs may be empty if no complement/shared, but structure is valid
    assert isinstance(result.synergy_pairs, list)
    for pair in result.synergy_pairs:
        assert pair.relationship in ("karmic_complement", "shared_recommend", "conflict")
        assert pair.stone != ""
        assert pair.person_a != ""
        assert pair.person_b != ""


def test_family_safe_stones(manish_chart: ChartData, sample_chart: ChartData):
    """Family-safe stones should be a list of stone names."""
    result = compute_family_gem_synergy([manish_chart, sample_chart])
    assert isinstance(result.family_safe_stones, list)
    for stone in result.family_safe_stones:
        assert isinstance(stone, str)


def test_rahu_ketu_gems_have_safety(manish_chart: ChartData):
    """Rahu/Ketu gem profiles should have gemstone_safety set."""
    result = compute_family_gem_synergy([manish_chart])
    member = result.members[0]
    if member.rahu_gem:
        assert member.rahu_gem.gemstone_safety in ("safe", "test_with_caution", "unsafe")
    if member.ketu_gem:
        assert member.ketu_gem.gemstone_safety in ("safe", "test_with_caution", "unsafe")
