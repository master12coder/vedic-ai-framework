"""Test scripture database loading and querying."""

import pytest
from jyotish.scriptures.scripture_db import (
    query_by_planet, query_by_topic, query_by_chapter,
    validate_against_scripture, get_citation, get_all_references, reload,
)


@pytest.fixture(autouse=True)
def fresh_load():
    """Ensure fresh load for each test."""
    reload()


class TestScriptureDB:
    def test_all_yaml_files_load(self):
        """All BPHS YAML files should load without error."""
        refs = get_all_references()
        assert len(refs) > 0

    def test_query_by_planet_saturn(self):
        results = query_by_planet("Saturn")
        assert len(results) > 0
        for r in results:
            assert "Saturn" in r.planets

    def test_query_by_planet_jupiter(self):
        results = query_by_planet("Jupiter")
        assert len(results) > 0

    def test_query_by_topic_marriage(self):
        results = query_by_topic("marriage")
        assert len(results) > 0

    def test_query_by_topic_gemstone(self):
        results = query_by_topic("gemstone")
        assert len(results) > 0

    def test_query_by_chapter_bphs_3(self):
        results = query_by_chapter("BPHS", 3)
        assert len(results) > 0
        for r in results:
            assert r.book == "BPHS"
            assert r.chapter == 3

    def test_validate_returns_references(self):
        results = validate_against_scripture("Saturn delays marriage", "Saturn", house=7)
        assert isinstance(results, list)

    def test_get_citation_format(self):
        refs = get_all_references()
        if refs:
            citation = get_citation(refs[0])
            assert refs[0].book in citation

    def test_scripture_has_hindi_text(self):
        refs = get_all_references()
        has_hindi = any(r.text_hindi for r in refs)
        assert has_hindi

    def test_multiple_chapters_loaded(self):
        refs = get_all_references()
        chapters = {r.chapter for r in refs}
        assert len(chapters) >= 3  # At least 3 different chapters
