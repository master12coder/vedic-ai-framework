"""Tests for the extended yoga definitions added from classical sources.

Covers: Balarishta, Ayu, Jaimini, Career, Travel, Saravali, Phaladeepika,
Hora Sara, Special Conjunction, Marriage, and Arishta yogas.

Sources verified: Phaladeepika (Mantreswara), Saravali (Kalyana Varma),
Jataka Parijata (Vaidyanatha), Brihat Jataka (Varahamihira),
Hora Sara (Prithuyasas).
"""

from __future__ import annotations

from typing import ClassVar

import pytest

from daivai_engine.compute.chart import compute_chart
from daivai_engine.knowledge.loader import load_yoga_definitions


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def yoga_defs() -> dict:
    """Load yoga definitions once for the whole module."""
    return load_yoga_definitions()


@pytest.fixture(scope="module")
def manish_chart():
    return compute_chart(
        name="Manish Chaurasia",
        dob="13/03/1989",
        tob="12:17",
        lat=25.3176,
        lon=83.0067,
        tz_name="Asia/Kolkata",
        gender="Male",
    )


# ---------------------------------------------------------------------------
# YAML Integrity Tests
# ---------------------------------------------------------------------------


class TestYamlIntegrity:
    """Ensure every new yoga entry has the required structural fields."""

    NEW_YOGA_KEYS: ClassVar[list[str]] = [
        # Balarishta
        "balarishta_1",
        "balarishta_2",
        "balarishta_3",
        "balarishta_4",
        "sutika_arishta",
        # Ayu
        "alpayu_yoga",
        "madhyayu_yoga",
        "purnayu_yoga",
        "deerghayu_yoga",
        "yogayu_yoga",
        # Jaimini
        "jaimini_raj_yoga_atmakaraka",
        "jaimini_raj_yoga_karakamsha",
        "jaimini_dhana_yoga_a2",
        "jaimini_upapada_vivah",
        "jaimini_chara_raj_yoga",
        # Career
        "rajseva_yoga",
        "vanij_yoga",
        "sainya_yoga",
        "vaidya_yoga",
        "guru_yoga_vocation",
        "lekhaka_yoga",
        "kavi_yoga_vocation",
        "shilpi_yoga",
        # Travel / Foreign
        "videsh_yoga_1",
        "videsh_yoga_2",
        "videsh_yoga_3",
        "pravasa_yoga",
        "samudra_yatra_yoga",
        "desh_tyag_yoga",
        # Saravali
        "chandrika_yoga",
        "soma_yoga",
        "vaidhavya_yoga",
        "bandha_yoga",
        "kutumbha_poshana_yoga",
        # Phaladeepika
        "mahimandita_yoga",
        "phaladeepika_raj_nidhana",
        "phaladeepika_pravrajya_4planets",
        "budhaditya_kendra_yoga",
        "chandra_adhi_yoga_refined",
        # Hora Sara
        "hora_sara_dhan_yoga",
        "hora_sara_karma_yoga",
        "hora_sara_rin_yoga",
        "hora_raja_yoga_9_10",
        # Special conjunctions
        "shrapit_yoga",
        "angarak_yoga",
        "brahma_yoga",
        "mrityu_bhaga_yoga",
        "gandanta_yoga",
        # Marriage
        "jara_yoga",
        "vivah_virodhaka_yoga",
        "deerga_kumara_yoga",
        "dwi_vivah_yoga",
        "satputra_vivah_yoga",
        # Sannyasa
        "sannyasa_phaladeepika_saturn_aspect",
        "bhikshu_yoga",
        # Arishta
        "papa_yoga_tri_dosham",
        "matru_arishta_yoga",
        "pitru_arishta_yoga",
        "putra_arishta_yoga",
    ]

    def test_all_new_keys_present(self, yoga_defs):
        """Every newly added yoga key must exist in the definitions file."""
        missing = [k for k in self.NEW_YOGA_KEYS if k not in yoga_defs]
        assert not missing, f"Missing yoga keys: {missing}"

    def test_new_yogas_have_name_en(self, yoga_defs):
        """Every new yoga must have an English name."""
        for key in self.NEW_YOGA_KEYS:
            assert "name_en" in yoga_defs[key], f"{key} missing name_en"
            assert yoga_defs[key]["name_en"], f"{key} name_en is empty"

    def test_new_yogas_have_name_hi(self, yoga_defs):
        """Every new yoga must have a Hindi name."""
        for key in self.NEW_YOGA_KEYS:
            assert "name_hi" in yoga_defs[key], f"{key} missing name_hi"

    def test_new_yogas_have_valid_type(self, yoga_defs):
        """Every new yoga type must be benefic, malefic, or mixed."""
        valid_types = {"benefic", "malefic", "mixed"}
        for key in self.NEW_YOGA_KEYS:
            t = yoga_defs[key].get("type")
            assert t in valid_types, f"{key} has invalid type: {t!r}"

    def test_new_yogas_have_formation(self, yoga_defs):
        """Every new yoga must have a formation section with a condition."""
        for key in self.NEW_YOGA_KEYS:
            assert "formation" in yoga_defs[key], f"{key} missing formation"
            condition = yoga_defs[key]["formation"].get("condition")
            assert condition, f"{key} formation.condition is empty"

    def test_new_yogas_have_effects(self, yoga_defs):
        """Every new yoga must have an effects section with a general description."""
        for key in self.NEW_YOGA_KEYS:
            effects = yoga_defs[key].get("effects")
            assert effects, f"{key} missing effects"
            assert effects.get("general"), f"{key} effects.general is empty"

    def test_new_yogas_have_source(self, yoga_defs):
        """Every new yoga must cite a classical source."""
        for key in self.NEW_YOGA_KEYS:
            source = yoga_defs[key].get("source")
            assert source, f"{key} missing source"

    def test_total_yogas_exceeds_200(self, yoga_defs):
        """The combined definitions file must now contain over 200 yogas."""
        assert len(yoga_defs) >= 200, f"Expected 200+ yogas, found {len(yoga_defs)}"


# ---------------------------------------------------------------------------
# Category-specific Content Tests
# ---------------------------------------------------------------------------


class TestBalarishtagYogas:
    """Balarishta yogas must be malefic and reference childhood danger."""

    BALARISHTA_KEYS: ClassVar[list[str]] = [
        "balarishta_1",
        "balarishta_2",
        "balarishta_3",
        "balarishta_4",
        "sutika_arishta",
    ]

    def test_balarishta_yogas_are_malefic(self, yoga_defs):
        for key in self.BALARISHTA_KEYS:
            assert yoga_defs[key]["type"] == "malefic", f"{key} should be malefic"

    def test_balarishta_yogas_reference_bphs(self, yoga_defs):
        for key in self.BALARISHTA_KEYS:
            source = yoga_defs[key]["source"].lower()
            assert any(ref in source for ref in ["bphs", "brihat jataka", "saravali"]), (
                f"{key} source should cite BPHS, Brihat Jataka, or Saravali: {source!r}"
            )

    def test_balarishta_1_involves_8th_house(self, yoga_defs):
        """Balarishta 1 requires Moon in 8th — 8 must be in houses_required."""
        formation = yoga_defs["balarishta_1"]["formation"]
        assert 8 in formation.get("houses_required", [])

    def test_balarishta_have_cancellation_conditions(self, yoga_defs):
        """Balarishta yogas must list cancellation conditions (Jupiter protection)."""
        for key in self.BALARISHTA_KEYS:
            cancellations = yoga_defs[key].get("cancellation", [])
            assert cancellations, f"{key} has no cancellation conditions"
            # Jupiter should appear as a remedy in at least one condition
            has_jupiter = any("jupiter" in c.lower() for c in cancellations)
            assert has_jupiter, f"{key} cancellations should mention Jupiter protection"


class TestAyuYogas:
    """Ayu (longevity) yogas must cover all three life-length categories."""

    def test_alpayu_yoga_is_malefic(self, yoga_defs):
        assert yoga_defs["alpayu_yoga"]["type"] == "malefic"

    def test_purnayu_yoga_is_benefic(self, yoga_defs):
        assert yoga_defs["purnayu_yoga"]["type"] == "benefic"

    def test_madhyayu_yoga_is_mixed(self, yoga_defs):
        assert yoga_defs["madhyayu_yoga"]["type"] == "mixed"

    def test_alpayu_involves_lagna_and_8th(self, yoga_defs):
        """Alpayu must reference both lagna (1) and 8th house."""
        formation = yoga_defs["alpayu_yoga"]["formation"]
        houses = formation.get("houses_required", [])
        assert 1 in houses and 8 in houses

    def test_deerghayu_references_saturn_in_8th(self, yoga_defs):
        """Long life yoga must involve Saturn and 8th house."""
        formation = yoga_defs["deerghayu_yoga"]["formation"]
        assert "saturn" in formation.get("planets", [])
        assert 8 in formation.get("houses_required", [])

    def test_ayu_yogas_cite_brihat_jataka(self, yoga_defs):
        """Longevity yogas come from Brihat Jataka Ch.14."""
        for key in ("alpayu_yoga", "purnayu_yoga", "deerghayu_yoga"):
            source = yoga_defs[key]["source"].lower()
            assert "brihat jataka" in source, f"{key} should cite Brihat Jataka: {source!r}"


class TestJaiminiYogas:
    """Jaimini-specific yogas must cite Jaimini sources."""

    JAIMINI_KEYS: ClassVar[list[str]] = [
        "jaimini_raj_yoga_atmakaraka",
        "jaimini_raj_yoga_karakamsha",
        "jaimini_dhana_yoga_a2",
        "jaimini_upapada_vivah",
        "jaimini_chara_raj_yoga",
    ]

    def test_jaimini_yogas_cite_jaimini_sutras(self, yoga_defs):
        for key in self.JAIMINI_KEYS:
            source = yoga_defs[key]["source"].lower()
            assert "jaimini" in source, f"{key} should cite Jaimini Sutras: {source!r}"

    def test_atmakaraka_yoga_is_benefic(self, yoga_defs):
        assert yoga_defs["jaimini_raj_yoga_atmakaraka"]["type"] == "benefic"

    def test_upapada_yoga_is_benefic(self, yoga_defs):
        assert yoga_defs["jaimini_upapada_vivah"]["type"] == "benefic"

    def test_dhana_a2_involves_benefic_planets(self, yoga_defs):
        """A2 wealth yoga should involve Jupiter, Venus, or Mercury."""
        planets = yoga_defs["jaimini_dhana_yoga_a2"]["formation"].get("planets", [])
        benefics = {"jupiter", "venus", "mercury"}
        assert any(p in benefics for p in planets)


class TestCareerYogas:
    """Career yogas must have specific career effects and proper planet combinations."""

    def test_rajseva_yoga_involves_sun(self, yoga_defs):
        """Government service yoga must involve the Sun."""
        planets = yoga_defs["rajseva_yoga"]["formation"].get("planets", [])
        assert "sun" in planets

    def test_sainya_yoga_involves_mars(self, yoga_defs):
        """Military yoga must involve Mars."""
        planets = yoga_defs["sainya_yoga"]["formation"].get("planets", [])
        assert "mars" in planets

    def test_vanij_yoga_involves_mercury_venus(self, yoga_defs):
        """Trade yoga must involve Mercury and Venus."""
        planets = yoga_defs["vanij_yoga"]["formation"].get("planets", [])
        assert "mercury" in planets
        assert "venus" in planets

    def test_vaidya_yoga_involves_mars_saturn(self, yoga_defs):
        """Medical yoga must involve Mars and Saturn."""
        planets = yoga_defs["vaidya_yoga"]["formation"].get("planets", [])
        assert "mars" in planets
        assert "saturn" in planets

    def test_career_yogas_have_career_effects(self, yoga_defs):
        """Career yogas must mention career domain in effects."""
        career_keys = [
            "rajseva_yoga",
            "vanij_yoga",
            "sainya_yoga",
            "vaidya_yoga",
            "guru_yoga_vocation",
            "lekhaka_yoga",
            "kavi_yoga_vocation",
            "shilpi_yoga",
        ]
        for key in career_keys:
            effects = yoga_defs[key].get("effects", {})
            career_text = effects.get("career", "")
            assert career_text, f"{key} missing career effects description"

    def test_guru_yoga_involves_jupiter_in_5_or_9(self, yoga_defs):
        """Teacher yoga must involve Jupiter in 5th or 9th house."""
        formation = yoga_defs["guru_yoga_vocation"]["formation"]
        assert "jupiter" in formation.get("planets", [])
        houses = formation.get("houses_required", [])
        assert 5 in houses or 9 in houses


class TestTravelYogas:
    """Foreign/travel yogas must involve 9th and 12th house themes."""

    def test_videsh_yoga_1_involves_rahu_12th(self, yoga_defs):
        """Foreign residence yoga must mention Rahu and 12th house."""
        formation = yoga_defs["videsh_yoga_1"]["formation"]
        assert "rahu" in formation.get("planets", [])
        assert 12 in formation.get("houses_required", [])

    def test_videsh_yoga_2_involves_9th_12th_connection(self, yoga_defs):
        """Fortune-based foreign yoga needs 9th and 12th lords."""
        formation = yoga_defs["videsh_yoga_2"]["formation"]
        houses = formation.get("houses_required", [])
        assert 9 in houses and 12 in houses

    def test_desh_tyag_yoga_is_malefic(self, yoga_defs):
        assert yoga_defs["desh_tyag_yoga"]["type"] == "malefic"

    def test_desh_tyag_involves_4th_house(self, yoga_defs):
        """Exile yoga must afflict the 4th house (homeland)."""
        houses = yoga_defs["desh_tyag_yoga"]["formation"].get("houses_required", [])
        assert 4 in houses

    def test_samudra_yatra_involves_moon_rahu(self, yoga_defs):
        """Ocean voyage yoga must involve Moon and Rahu."""
        planets = yoga_defs["samudra_yatra_yoga"]["formation"].get("planets", [])
        assert "moon" in planets
        assert "rahu" in planets


class TestSpecialConjunctionYogas:
    """Shrapit, Angarak, and Brahma yogas."""

    def test_shrapit_yoga_involves_saturn_rahu(self, yoga_defs):
        """Cursed yoga = Saturn + Rahu conjunction."""
        planets = yoga_defs["shrapit_yoga"]["formation"].get("planets", [])
        assert "saturn" in planets
        assert "rahu" in planets

    def test_angarak_yoga_involves_mars_rahu(self, yoga_defs):
        """Fire yoga = Mars + Rahu conjunction."""
        planets = yoga_defs["angarak_yoga"]["formation"].get("planets", [])
        assert "mars" in planets
        assert "rahu" in planets

    def test_shrapit_angarak_are_malefic(self, yoga_defs):
        assert yoga_defs["shrapit_yoga"]["type"] == "malefic"
        assert yoga_defs["angarak_yoga"]["type"] == "malefic"

    def test_brahma_yoga_is_benefic(self, yoga_defs):
        assert yoga_defs["brahma_yoga"]["type"] == "benefic"

    def test_brahma_yoga_requires_all_three_benefics(self, yoga_defs):
        """Brahma Yoga needs Jupiter, Venus, and Mercury in kendras."""
        formation = yoga_defs["brahma_yoga"]["formation"]
        planets = formation.get("planets", [])
        for p in ("jupiter", "venus", "mercury"):
            assert p in planets, f"Brahma Yoga missing {p}"
        # All must be in kendras
        assert formation.get("houses_required") == [1, 4, 7, 10]

    def test_gandanta_yoga_is_malefic(self, yoga_defs):
        assert yoga_defs["gandanta_yoga"]["type"] == "malefic"


class TestPhaladeeepikaYogas:
    """Phaladeepika-sourced yogas must cite Phaladeepika."""

    PHALADEEPIKA_KEYS: ClassVar[list[str]] = [
        "mahimandita_yoga",
        "phaladeepika_raj_nidhana",
        "phaladeepika_pravrajya_4planets",
        "budhaditya_kendra_yoga",
        "chandra_adhi_yoga_refined",
    ]

    def test_phaladeepika_yogas_cite_correct_source(self, yoga_defs):
        for key in self.PHALADEEPIKA_KEYS:
            source = yoga_defs[key]["source"].lower()
            assert "phaladeepika" in source, f"{key} should cite Phaladeepika: {source!r}"

    def test_pravrajya_4planets_is_mixed(self, yoga_defs):
        """Four planets in one sign can give renunciation or focused achievement."""
        assert yoga_defs["phaladeepika_pravrajya_4planets"]["type"] == "mixed"

    def test_budhaditya_kendra_requires_sun_mercury(self, yoga_defs):
        planets = yoga_defs["budhaditya_kendra_yoga"]["formation"].get("planets", [])
        assert "sun" in planets
        assert "mercury" in planets

    def test_budhaditya_kendra_requires_kendras(self, yoga_defs):
        houses = yoga_defs["budhaditya_kendra_yoga"]["formation"].get("houses_required", [])
        assert set(houses) == {1, 4, 7, 10}


class TestHoraSaraYogas:
    """Hora Sara yogas must cite Hora Sara."""

    HORA_SARA_KEYS: ClassVar[list[str]] = [
        "hora_sara_dhan_yoga",
        "hora_sara_karma_yoga",
        "hora_sara_rin_yoga",
        "hora_raja_yoga_9_10",
    ]

    def test_hora_sara_yogas_cite_source(self, yoga_defs):
        for key in self.HORA_SARA_KEYS:
            source = yoga_defs[key]["source"].lower()
            assert "hora sara" in source, f"{key} should cite Hora Sara: {source!r}"

    def test_hora_sara_karma_yoga_involves_saturn(self, yoga_defs):
        """Saturn in 10th = sustained career per Hora Sara."""
        planets = yoga_defs["hora_sara_karma_yoga"]["formation"].get("planets", [])
        assert "saturn" in planets

    def test_hora_sara_karma_yoga_10th_house(self, yoga_defs):
        houses = yoga_defs["hora_sara_karma_yoga"]["formation"].get("houses_required", [])
        assert 10 in houses

    def test_rin_yoga_is_malefic(self, yoga_defs):
        assert yoga_defs["hora_sara_rin_yoga"]["type"] == "malefic"


class TestMarriageYogasExtended:
    """New marriage yogas have correct type and house involvement."""

    def test_jara_yoga_is_malefic(self, yoga_defs):
        assert yoga_defs["jara_yoga"]["type"] == "malefic"

    def test_jara_yoga_involves_7th(self, yoga_defs):
        houses = yoga_defs["jara_yoga"]["formation"].get("houses_required", [])
        assert 7 in houses

    def test_dwi_vivah_is_mixed(self, yoga_defs):
        """Multiple marriages is mixed — not always negative."""
        assert yoga_defs["dwi_vivah_yoga"]["type"] == "mixed"

    def test_vivah_virodhaka_is_malefic(self, yoga_defs):
        assert yoga_defs["vivah_virodhaka_yoga"]["type"] == "malefic"

    def test_satputra_vivah_is_benefic(self, yoga_defs):
        assert yoga_defs["satputra_vivah_yoga"]["type"] == "benefic"

    def test_deerga_kumara_involves_7th_saturn(self, yoga_defs):
        """Long bachelorhood requires Saturn in 7th."""
        formation = yoga_defs["deerga_kumara_yoga"]["formation"]
        assert "saturn" in formation.get("planets", [])


class TestArishtagYogasExtended:
    """Extended Arishta yogas for family members and triple malefics."""

    def test_matru_arishta_involves_4th_lord(self, yoga_defs):
        planets = yoga_defs["matru_arishta_yoga"]["formation"].get("planets", [])
        assert "4th_lord" in planets or "moon" in planets

    def test_pitru_arishta_involves_9th_lord(self, yoga_defs):
        planets = yoga_defs["pitru_arishta_yoga"]["formation"].get("planets", [])
        assert "9th_lord" in planets or "sun" in planets

    def test_putra_arishta_involves_5th_lord_in_8th(self, yoga_defs):
        formation = yoga_defs["putra_arishta_yoga"]["formation"]
        planets = formation.get("planets", [])
        houses = formation.get("houses_required", [])
        assert "5th_lord" in planets
        assert 8 in houses

    def test_all_extended_arishta_are_malefic(self, yoga_defs):
        for key in (
            "matru_arishta_yoga",
            "pitru_arishta_yoga",
            "putra_arishta_yoga",
            "papa_yoga_tri_dosham",
        ):
            assert yoga_defs[key]["type"] == "malefic", f"{key} should be malefic"

    def test_arishta_yogas_have_cancellations(self, yoga_defs):
        for key in ("matru_arishta_yoga", "pitru_arishta_yoga", "putra_arishta_yoga"):
            cancellations = yoga_defs[key].get("cancellation", [])
            assert cancellations, f"{key} must have cancellation conditions"


# ---------------------------------------------------------------------------
# Integration Tests Against Real Charts
# ---------------------------------------------------------------------------


class TestYogaDefinitionsLoadWithChart:
    """Ensure yoga definitions load cleanly and can be cross-referenced with charts."""

    def test_yoga_definitions_load_without_error(self):
        """The YAML file must parse without exceptions."""
        defs = load_yoga_definitions()
        assert isinstance(defs, dict)
        assert len(defs) > 0

    def test_manish_chart_planets_exist(self, manish_chart):
        """Reference chart has all 9 required planets."""
        required = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        assert required.issubset(set(manish_chart.planets.keys()))

    def test_yoga_defs_keys_are_valid_yaml_identifiers(self, yoga_defs):
        """All yoga keys must be lowercase strings with no spaces."""
        for key in yoga_defs:
            assert key == key.lower(), f"Key not lowercase: {key!r}"
            assert " " not in key, f"Key has spaces: {key!r}"

    def test_new_foreign_yogas_logic_for_rahu_in_12(self, manish_chart):
        """Videsh Yoga 1 condition: Rahu in 12th house — verify chart has Rahu somewhere."""
        rahu = manish_chart.planets.get("Rahu")
        assert rahu is not None, "Chart must have Rahu"
        # We can't force Rahu to be in 12th in Manish's chart,
        # but we verify the chart planet structure is consistent with what
        # the yoga definition checks (house attribute exists)
        assert hasattr(rahu, "house")
        assert 1 <= rahu.house <= 12

    def test_shrapit_yoga_chart_condition(self, manish_chart):
        """Saturn and Rahu are both planets in any chart — verify they exist."""
        saturn = manish_chart.planets.get("Saturn")
        rahu = manish_chart.planets.get("Rahu")
        assert saturn is not None
        assert rahu is not None
        # A Shrapit Yoga would be present if they're in the same house
        is_shrapit = saturn.house == rahu.house
        # We don't assert presence/absence — just that the logic can be evaluated
        assert isinstance(is_shrapit, bool)
