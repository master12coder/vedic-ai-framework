"""Scripture database — load and query classical Vedic astrology text references."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from jyotish.domain.models.scripture import ScriptureReference
from jyotish.utils.logging_config import get_logger

logger = get_logger(__name__)

_BPHS_DIR = Path(__file__).parent / "bphs"
_ALL_REFS: list[ScriptureReference] | None = None


def _load_yaml_rules(yaml_path: Path) -> list[ScriptureReference]:
    """Load scripture rules from a single YAML file."""
    if not yaml_path.exists():
        return []
    with open(yaml_path) as f:
        data = yaml.safe_load(f) or {}

    book = data.get("book", "BPHS")
    chapter = data.get("chapter", 0)
    rules = data.get("rules", [])

    refs = []
    for rule in rules:
        refs.append(ScriptureReference(
            book=book,
            chapter=chapter,
            verse=rule.get("verse"),
            topic=rule.get("topic", ""),
            planets=rule.get("planets", []),
            houses=rule.get("houses", []),
            text_sanskrit=rule.get("text_sanskrit", ""),
            text_english=rule.get("text_english", ""),
            text_hindi=rule.get("text_hindi", ""),
            rule_type=rule.get("rule_type", "general"),
        ))
    return refs


def _load_all() -> list[ScriptureReference]:
    """Load all scripture references from YAML files."""
    global _ALL_REFS
    if _ALL_REFS is not None:
        return _ALL_REFS

    _ALL_REFS = []
    if _BPHS_DIR.exists():
        for yaml_file in sorted(_BPHS_DIR.glob("*.yaml")):
            try:
                refs = _load_yaml_rules(yaml_file)
                _ALL_REFS.extend(refs)
                logger.debug("Loaded %d rules from %s", len(refs), yaml_file.name)
            except Exception as e:
                logger.warning("Error loading %s: %s", yaml_file.name, e)

    logger.info("Total scripture references loaded: %d", len(_ALL_REFS))
    return _ALL_REFS


def reload() -> None:
    """Force reload of all scripture data."""
    global _ALL_REFS
    _ALL_REFS = None
    _load_all()


def query_by_planet(planet: str, house: int | None = None) -> list[ScriptureReference]:
    """Query scripture references by planet and optionally house.

    Args:
        planet: Planet name (e.g., "Saturn", "Jupiter")
        house: Optional house number (1-12)

    Returns:
        List of matching ScriptureReference objects.
    """
    refs = _load_all()
    results = [r for r in refs if planet in r.planets]
    if house is not None:
        results = [r for r in results if house in r.houses or not r.houses]
    return results


def query_by_topic(topic: str) -> list[ScriptureReference]:
    """Query scripture references by topic keyword.

    Args:
        topic: Topic to search for (e.g., "marriage", "career", "yoga")

    Returns:
        List of matching references (topic field contains the keyword).
    """
    refs = _load_all()
    topic_lower = topic.lower()
    return [
        r for r in refs
        if topic_lower in r.topic.lower() or topic_lower in r.text_english.lower()
    ]


def query_by_chapter(book: str, chapter: int) -> list[ScriptureReference]:
    """Query by specific book and chapter.

    Args:
        book: Book name (e.g., "BPHS")
        chapter: Chapter number
    """
    refs = _load_all()
    return [r for r in refs if r.book == book and r.chapter == chapter]


def validate_against_scripture(
    statement: str,
    planet: str,
    house: int | None = None,
) -> list[ScriptureReference]:
    """Find scripture references that relate to a given statement.

    Useful for the validation pipeline — check if a pandit's correction
    aligns with or contradicts classical texts.

    Args:
        statement: The claim to validate
        planet: Planet being discussed
        house: House being discussed

    Returns:
        List of potentially relevant references.
    """
    return query_by_planet(planet, house)


def get_citation(ref: ScriptureReference) -> str:
    """Format a scripture reference as a citation string.

    Example: "BPHS 19:8 — Saturn in 7th delays marriage"
    """
    verse = f":{ref.verse}" if ref.verse else ""
    return f"{ref.book} {ref.chapter}{verse} — {ref.text_english[:80]}"


def get_all_references() -> list[ScriptureReference]:
    """Get all loaded scripture references."""
    return _load_all()
