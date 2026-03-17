"""Test scripture database loading and querying."""

from pathlib import Path

import pytest
import yaml

from jyotish.domain.models.scripture import ScriptureReference
from jyotish.scriptures.scripture_db import (
    get_all_references,
    get_citation,
    query_by_chapter,
    query_by_planet,
    query_by_topic,
    reload,
    validate_against_scripture,
)

_BPHS_DIR = Path(__file__).resolve().parents[2] / "jyotish" / "scriptures" / "bphs"

# Expected YAML files in bphs/
_EXPECTED_FILES = [
    "chapter_03_planet_nature.yaml",
    "chapter_05_houses.yaml",
    "chapter_07_friendships.yaml",
    "chapter_10_yogas.yaml",
    "chapter_19_marriage.yaml",
    "chapter_25_dasha_effects.yaml",
    "chapter_80_gemstones.yaml",
    "chapter_85_remedies.yaml",
]


@pytest.fixture(autouse=True)
def fresh_load():
    """Ensure fresh load for each test."""
    reload()


# ------------------------------------------------------------------
# Test: all YAML files load without error
# ------------------------------------------------------------------

class TestYAMLFilesLoad:
    """Verify every expected BPHS YAML file exists and is valid."""

    @pytest.mark.parametrize("filename", _EXPECTED_FILES)
    def test_yaml_file_exists(self, filename: str) -> None:
        path = _BPHS_DIR / filename
        assert path.exists(), f"Missing YAML file: {filename}"

    @pytest.mark.parametrize("filename", _EXPECTED_FILES)
    def test_yaml_file_parses(self, filename: str) -> None:
        path = _BPHS_DIR / filename
        with open(path) as f:
            data = yaml.safe_load(f)
        assert data is not None
        assert "book" in data
        assert "chapter" in data
        assert "rules" in data
        assert len(data["rules"]) > 0

    def test_all_yaml_files_load_into_db(self) -> None:
        """All BPHS YAML files should load without error."""
        refs = get_all_references()
        assert len(refs) > 0
        # We have 8 files with many rules each — expect a significant count
        assert len(refs) >= 100, f"Expected >= 100 total rules, got {len(refs)}"

    def test_multiple_chapters_loaded(self) -> None:
        refs = get_all_references()
        chapters = {r.chapter for r in refs}
        assert len(chapters) >= 8, f"Expected >= 8 chapters, got {chapters}"


# ------------------------------------------------------------------
# Test: query_by_planet
# ------------------------------------------------------------------

class TestQueryByPlanet:
    def test_query_by_planet_saturn(self) -> None:
        results = query_by_planet("Saturn")
        assert len(results) > 0
        for r in results:
            assert "Saturn" in r.planets

    def test_query_by_planet_jupiter(self) -> None:
        results = query_by_planet("Jupiter")
        assert len(results) > 0

    def test_query_by_planet_with_house(self) -> None:
        results = query_by_planet("Venus", house=7)
        assert len(results) > 0
        # Each result should either mention house 7 or have no house filter
        for r in results:
            assert "Venus" in r.planets
            assert 7 in r.houses or len(r.houses) == 0

    def test_query_nonexistent_planet_returns_empty(self) -> None:
        results = query_by_planet("Pluto")
        assert results == []

    def test_all_nine_planets_have_references(self) -> None:
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                       "Venus", "Saturn", "Rahu", "Ketu"]:
            results = query_by_planet(planet)
            assert len(results) > 0, f"No references found for {planet}"


# ------------------------------------------------------------------
# Test: query_by_topic
# ------------------------------------------------------------------

class TestQueryByTopic:
    def test_query_by_topic_marriage(self) -> None:
        results = query_by_topic("marriage")
        assert len(results) > 0

    def test_query_by_topic_gemstone(self) -> None:
        results = query_by_topic("gemstone")
        assert len(results) > 0

    def test_query_by_topic_yoga(self) -> None:
        results = query_by_topic("yoga")
        assert len(results) > 0

    def test_query_by_topic_remedy(self) -> None:
        results = query_by_topic("remedy")
        assert len(results) > 0

    def test_query_by_topic_dasha(self) -> None:
        results = query_by_topic("dasha")
        assert len(results) > 0

    def test_query_by_topic_friendship(self) -> None:
        results = query_by_topic("friendship")
        assert len(results) > 0


# ------------------------------------------------------------------
# Test: query_by_chapter
# ------------------------------------------------------------------

class TestQueryByChapter:
    def test_query_by_chapter_bphs_3(self) -> None:
        results = query_by_chapter("BPHS", 3)
        assert len(results) >= 20, "Chapter 3 should have at least 20 rules"
        for r in results:
            assert r.book == "BPHS"
            assert r.chapter == 3

    def test_query_by_chapter_bphs_5(self) -> None:
        results = query_by_chapter("BPHS", 5)
        assert len(results) >= 24, "Chapter 5 should have at least 24 rules"

    def test_query_by_chapter_bphs_10(self) -> None:
        results = query_by_chapter("BPHS", 10)
        assert len(results) >= 15, "Chapter 10 should have at least 15 rules"

    def test_query_by_chapter_bphs_25(self) -> None:
        results = query_by_chapter("BPHS", 25)
        assert len(results) >= 18, "Chapter 25 should have at least 18 rules"


# ------------------------------------------------------------------
# Test: validate_against_scripture
# ------------------------------------------------------------------

class TestValidateAgainstScripture:
    def test_validate_returns_references(self) -> None:
        results = validate_against_scripture(
            "Saturn delays marriage", "Saturn", house=7
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_validate_ranks_by_relevance(self) -> None:
        results = validate_against_scripture(
            "Saturn causes delay depression isolation", "Saturn"
        )
        assert len(results) > 0
        # All results should mention Saturn
        for r in results:
            assert "Saturn" in r.planets


# ------------------------------------------------------------------
# Test: citation and data quality
# ------------------------------------------------------------------

class TestDataQuality:
    def test_get_citation_format(self) -> None:
        refs = get_all_references()
        assert len(refs) > 0
        citation = get_citation(refs[0])
        assert refs[0].book in citation

    def test_scripture_has_hindi_text(self) -> None:
        refs = get_all_references()
        has_hindi = any(r.text_hindi for r in refs)
        assert has_hindi, "At least some references should have Hindi text"

    def test_scripture_has_sanskrit_text(self) -> None:
        refs = get_all_references()
        has_sanskrit = any(r.text_sanskrit for r in refs)
        assert has_sanskrit, "At least some references should have Sanskrit text"

    def test_all_refs_are_dataclass_instances(self) -> None:
        refs = get_all_references()
        for r in refs:
            assert isinstance(r, ScriptureReference)

    def test_rule_types_are_valid(self) -> None:
        valid_types = {
            "general", "yoga", "dasha", "remedy",
            "transit", "friendship", "gemstone",
            "planet_house", "raja_yoga", "muhurta",
            "lord_placement", "bhava_effect", "karaka_effect",
            "ashtakavarga", "dasha_effect",
        }
        refs = get_all_references()
        for r in refs:
            assert r.rule_type in valid_types, (
                f"Invalid rule_type '{r.rule_type}' in {r.book} ch.{r.chapter} v.{r.verse}"
            )
