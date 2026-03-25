"""Tests for functional nature classification and Rahu/Ketu rashyadhipati."""

from __future__ import annotations

import pytest

from daivai_engine.compute.chart import compute_chart
from daivai_engine.compute.functional_nature import get_functional_nature, get_shadow_planet_nature
from daivai_engine.models.chart import ChartData


# ── get_functional_nature tests ──────────────────────────────────────────────


def test_mars_mesha_lagna_benefic():
    """Mars is lagna lord for Mesha → always benefic."""
    result = get_functional_nature("Mars", "Aries")
    assert result.classification == "benefic"
    assert 1 in result.houses_owned
    assert result.planet == "Mars"
    assert result.lagna_sign == "Aries"


def test_jupiter_mithuna_lagna_malefic():
    """Jupiter owns 7+10 for Mithuna → functional malefic + maraka."""
    result = get_functional_nature("Jupiter", "Gemini")
    assert result.classification == "malefic"
    assert result.is_maraka is True
    assert 7 in result.houses_owned
    assert 10 in result.houses_owned


def test_venus_mithuna_lagna_yogakaraka():
    """Venus is yogakaraka for Mithuna lagna (5th lord)."""
    result = get_functional_nature("Venus", "Gemini")
    assert result.classification == "yogakaraka"
    assert result.is_yogakaraka is True


def test_jupiter_vrischika_lagna_benefic():
    """Jupiter owns 2+5 for Vrischika → functional benefic (yogakaraka)."""
    result = get_functional_nature("Jupiter", "Scorpio")
    assert result.classification == "yogakaraka"
    assert result.is_yogakaraka is True
    assert 2 in result.houses_owned
    assert 5 in result.houses_owned


def test_venus_vrischika_lagna_malefic():
    """Venus owns 7+12 for Vrischika → functional malefic."""
    result = get_functional_nature("Venus", "Scorpio")
    assert result.classification == "malefic"


def test_saturn_mithuna_lagna_benefic_mixed():
    """Saturn owns 8+9 for Mithuna → classified as benefic (9th trikona dominates)."""
    result = get_functional_nature("Saturn", "Gemini")
    assert result.classification == "benefic"
    assert 8 in result.houses_owned
    assert 9 in result.houses_owned


def test_moon_mithuna_lagna_maraka():
    """Moon owns 2nd for Mithuna → maraka."""
    result = get_functional_nature("Moon", "Gemini")
    assert result.is_maraka is True


def test_unknown_planet_neutral():
    """A planet not listed should return neutral."""
    # Rahu is not listed in lordship_rules.yaml functional lists
    result = get_functional_nature("Rahu", "Gemini")
    assert result.classification == "neutral"


# ── Rashyadhipati: shadow planet gemstone safety ─────────────────────────────


@pytest.fixture
def vrischika_chart() -> ChartData:
    """Chart with Vrischika (Scorpio) lagna for rashyadhipati testing.

    Uses a birth date/place that gives Vrischika lagna.
    """
    return compute_chart(
        name="Vrischika Native",
        dob="20/08/1992",
        tob="12:05",
        lat=25.3176,
        lon=83.0067,
        tz_name="Asia/Kolkata",
        gender="Female",
    )


@pytest.mark.safety
def test_shadow_planet_nature_basic(manish_chart: ChartData):
    """Manish (Mithuna lagna): verify Rahu shadow resolution works."""
    result = get_shadow_planet_nature("Rahu", manish_chart)
    assert result.shadow_planet == "Rahu"
    assert result.sign_lord != ""
    assert result.gemstone_name == "Hessonite (Gomed)"
    assert result.gemstone_safety in ("safe", "test_with_caution", "unsafe")
    assert result.sign_lord_nature.planet == result.sign_lord


@pytest.mark.safety
def test_ketu_shadow_nature(manish_chart: ChartData):
    """Verify Ketu shadow resolution returns Cat's Eye."""
    result = get_shadow_planet_nature("Ketu", manish_chart)
    assert result.shadow_planet == "Ketu"
    assert result.gemstone_name == "Cat's Eye (Lehsunia)"
    assert result.gemstone_safety in ("safe", "test_with_caution", "unsafe")


@pytest.mark.safety
def test_shadow_planet_sign_lord_matches(manish_chart: ChartData):
    """Sign lord in ShadowPlanetNature must match SIGN_LORDS for that sign index."""
    from daivai_engine.constants.signs import SIGN_LORDS

    for shadow in ["Rahu", "Ketu"]:
        result = get_shadow_planet_nature(shadow, manish_chart)
        expected_lord = SIGN_LORDS[result.sign_index]
        assert result.sign_lord == expected_lord


@pytest.mark.safety
def test_gemstone_safety_classification_logic():
    """Verify the safety logic: benefic without dusthana → safe."""
    nature_benefic = get_functional_nature("Jupiter", "Scorpio")  # 2+5L, no dusthana
    assert nature_benefic.classification == "yogakaraka"

    nature_mixed = get_functional_nature("Saturn", "Gemini")  # 8+9L, 8 is dusthana
    assert nature_mixed.classification == "benefic"
    assert 8 in nature_mixed.houses_owned  # dusthana involvement
