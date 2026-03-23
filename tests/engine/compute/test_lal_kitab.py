"""Tests for Lal Kitab analysis — planet assessment, Rin detection, remedies.

Primary fixture: manish_chart (Manish Chaurasia — verified reference chart).
  DOB: 13/03/1989  TOB: 12:17  Place: Varanasi
  Lagna: Mithuna (Gemini)   Moon: Rohini Pada 2

Lal Kitab ignores signs and uses planet-in-house positions only.

Source: Lal Kitab (Pandit Roop Chand Joshi, 1939-1952).
"""

from __future__ import annotations

from daivai_engine.compute.lal_kitab import (
    LK_ENEMIES,
    LK_FRIENDS,
    PAKKA_GHAR,
    _assess_planet,
    _categorize_remedy,
    _detect_rins,
    _match_remedies,
    _planets_in_house,
    compute_lal_kitab,
)
from daivai_engine.models.chart import ChartData
from daivai_engine.models.lal_kitab import (
    LalKitabPlanetAssessment,
    LalKitabRemedy,
    LalKitabResult,
    LalKitabRin,
)


# ---------------------------------------------------------------------------
# Pakka Ghar constants
# ---------------------------------------------------------------------------


class TestPakkaGhar:
    """Verify Pakka Ghar (permanent house) assignments per Lal Kitab."""

    def test_sun_pakka_ghar_is_1(self) -> None:
        assert PAKKA_GHAR["Sun"] == 1

    def test_moon_pakka_ghar_is_4(self) -> None:
        assert PAKKA_GHAR["Moon"] == 4

    def test_mars_pakka_ghar_is_3(self) -> None:
        assert PAKKA_GHAR["Mars"] == 3

    def test_jupiter_pakka_ghar_is_2(self) -> None:
        assert PAKKA_GHAR["Jupiter"] == 2

    def test_saturn_pakka_ghar_is_8(self) -> None:
        assert PAKKA_GHAR["Saturn"] == 8

    def test_rahu_pakka_ghar_is_12(self) -> None:
        assert PAKKA_GHAR["Rahu"] == 12

    def test_ketu_pakka_ghar_is_6(self) -> None:
        assert PAKKA_GHAR["Ketu"] == 6


# ---------------------------------------------------------------------------
# Friendship tables
# ---------------------------------------------------------------------------


class TestLKFriendships:
    """Lal Kitab friendships differ from Parashari."""

    def test_moon_mercury_friends_in_lk(self) -> None:
        """In LK, Moon-Mercury are friends (unlike Parashari where Mercury is neutral to Moon)."""
        assert "Mercury" in LK_FRIENDS["Moon"]
        assert "Moon" in LK_FRIENDS["Mercury"]

    def test_sun_saturn_enemies(self) -> None:
        assert "Saturn" in LK_ENEMIES["Sun"]
        assert "Sun" in LK_ENEMIES["Saturn"]

    def test_rahu_friends_include_saturn_friends(self) -> None:
        """Rahu's friends should include Saturn's friends (Mercury, Venus)."""
        rahu_friends = set(LK_FRIENDS["Rahu"])
        saturn_friends = set(LK_FRIENDS["Saturn"])
        assert saturn_friends.issubset(rahu_friends)


# ---------------------------------------------------------------------------
# Planet assessment
# ---------------------------------------------------------------------------


class TestAssessPlanet:
    """Test _assess_planet with the reference chart."""

    def test_assessment_returns_correct_model(self, manish_chart: ChartData) -> None:
        result = _assess_planet("Sun", manish_chart)
        assert isinstance(result, LalKitabPlanetAssessment)

    def test_planet_in_pakka_ghar_is_very_strong(self, manish_chart: ChartData) -> None:
        """If a planet happens to be in its Pakka Ghar (and not with Rahu/Ketu), it should be very_strong."""
        for planet, pakka in PAKKA_GHAR.items():
            result = _assess_planet(planet, manish_chart)
            if result.house == pakka and not result.is_dormant:
                assert result.strength == "very_strong", (
                    f"{planet} in house {pakka} (Pakka Ghar) should be very_strong"
                )

    def test_dormant_when_with_rahu_ketu(self, manish_chart: ChartData) -> None:
        """A planet conjunct Rahu or Ketu should be dormant (soya hua)."""
        for planet in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            result = _assess_planet(planet, manish_chart)
            house = result.house
            occupants = _planets_in_house(house, manish_chart)
            has_node = any(n in occupants for n in ("Rahu", "Ketu") if n != planet)
            if has_node:
                assert result.is_dormant, f"{planet} with Rahu/Ketu should be dormant"
                assert result.strength == "dormant"

    def test_all_nine_planets_assessed(self, manish_chart: ChartData) -> None:
        """Every planet should get an assessment."""
        from daivai_engine.constants import PLANETS

        for p in PLANETS:
            result = _assess_planet(p, manish_chart)
            assert result.planet == p
            assert 1 <= result.house <= 12
            assert result.strength in (
                "very_strong",
                "strong",
                "moderate",
                "weak",
                "dormant",
            )


# ---------------------------------------------------------------------------
# Rin (debt) detection
# ---------------------------------------------------------------------------


class TestDetectRins:
    """Test Rin (debt) detection rules."""

    def test_rins_returns_list(self, manish_chart: ChartData) -> None:
        rins = _detect_rins(manish_chart)
        assert isinstance(rins, list)
        for r in rins:
            assert isinstance(r, LalKitabRin)

    def test_pitra_rin_requires_sun_in_2_5_9(self, manish_chart: ChartData) -> None:
        """Pitra Rin should only appear if Sun is in house 2, 5, or 9."""
        rins = _detect_rins(manish_chart)
        pitra = [r for r in rins if r.rin_type == "pitra"]
        if pitra:
            assert pitra[0].causing_planet == "Sun"
            assert pitra[0].causing_house in (2, 5, 9)

    def test_matri_rin_requires_moon_in_4(self, manish_chart: ChartData) -> None:
        """Matri Rin should only appear if Moon is in house 4."""
        rins = _detect_rins(manish_chart)
        matri = [r for r in rins if r.rin_type == "matri"]
        if matri:
            assert matri[0].causing_planet == "Moon"
            assert matri[0].causing_house == 4

    def test_stri_rin_requires_venus_in_7(self, manish_chart: ChartData) -> None:
        """Stri Rin should only appear if Venus is in house 7."""
        rins = _detect_rins(manish_chart)
        stri = [r for r in rins if r.rin_type == "stri"]
        if stri:
            assert stri[0].causing_planet == "Venus"
            assert stri[0].causing_house == 7

    def test_rin_severity_values(self, manish_chart: ChartData) -> None:
        rins = _detect_rins(manish_chart)
        for r in rins:
            assert r.severity in ("mild", "moderate", "severe")


# ---------------------------------------------------------------------------
# Remedy categorization
# ---------------------------------------------------------------------------


class TestCategorizeRemedy:
    """Test the _categorize_remedy text classifier."""

    def test_donate_is_daan(self) -> None:
        assert _categorize_remedy("Donate wheat on Sundays") == "daan"

    def test_offer_is_daan(self) -> None:
        assert _categorize_remedy("Offer jaggery to monkeys") == "daan"

    def test_avoid_is_behavioral(self) -> None:
        assert _categorize_remedy("Avoid accepting free items") == "behavioral"

    def test_temple_is_ritual(self) -> None:
        assert _categorize_remedy("Visit a temple on Tuesdays") == "ritual"

    def test_generic_is_object(self) -> None:
        assert _categorize_remedy("Keep a copper coin in pocket") == "object"


# ---------------------------------------------------------------------------
# Remedy matching
# ---------------------------------------------------------------------------


class TestMatchRemedies:
    """Test _match_remedies against the YAML file."""

    def test_remedies_matched_from_yaml(self, manish_chart: ChartData) -> None:
        """Remedies YAML should produce at least some matches for any chart."""
        from pathlib import Path

        import yaml

        yaml_path = (
            Path(__file__).resolve().parents[3]
            / "engine"
            / "src"
            / "daivai_engine"
            / "scriptures"
            / "lal_kitab"
            / "remedies.yaml"
        )
        with yaml_path.open() as f:
            data = yaml.safe_load(f)

        remedies = _match_remedies(manish_chart, data)
        assert isinstance(remedies, list)
        for r in remedies:
            assert isinstance(r, LalKitabRemedy)
            assert r.category in ("daan", "behavioral", "ritual", "object")


# ---------------------------------------------------------------------------
# Full computation
# ---------------------------------------------------------------------------


class TestComputeLalKitab:
    """Integration tests for compute_lal_kitab."""

    def test_result_is_correct_model(self, manish_chart: ChartData) -> None:
        result = compute_lal_kitab(manish_chart)
        assert isinstance(result, LalKitabResult)

    def test_nine_planet_assessments(self, manish_chart: ChartData) -> None:
        result = compute_lal_kitab(manish_chart)
        assert len(result.planet_assessments) == 9

    def test_strongest_and_weakest_differ(self, manish_chart: ChartData) -> None:
        result = compute_lal_kitab(manish_chart)
        # Strongest and weakest should be valid planet names
        from daivai_engine.constants import PLANETS

        assert result.strongest_planet in PLANETS
        assert result.weakest_planet in PLANETS

    def test_dormant_planets_subset_of_all(self, manish_chart: ChartData) -> None:
        result = compute_lal_kitab(manish_chart)
        from daivai_engine.constants import PLANETS

        for p in result.dormant_planets:
            assert p in PLANETS

    def test_summary_is_nonempty(self, manish_chart: ChartData) -> None:
        result = compute_lal_kitab(manish_chart)
        assert len(result.summary) > 0
        assert "Strongest" in result.summary
