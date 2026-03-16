"""Data model for scripture references from classical Jyotish texts."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScriptureReference:
    """A single reference from a classical Jyotish scripture.

    Attributes:
        book: Name of the text, e.g. "BPHS", "Brihat Jataka",
              "Phaladeepika", "Lal Kitab".
        chapter: Chapter number within the text.
        verse: Verse/shloka number (None when the rule spans
               multiple verses or is a summarised principle).
        topic: Canonical topic tag, e.g. "planet_nature", "yoga",
               "marriage", "remedy", "dasha_effects".
        planets: Planets referenced by this rule (English names).
        houses: House numbers (1-12) referenced by this rule.
        text_sanskrit: Original Sanskrit or transliterated text.
        text_english: English translation / summary.
        text_hindi: Hindi translation.
        rule_type: One of "general", "yoga", "dasha", "remedy",
                   "transit", "friendship", "gemstone".
    """

    book: str
    chapter: int
    verse: int | None
    topic: str
    planets: list[str] = field(default_factory=list)
    houses: list[int] = field(default_factory=list)
    text_sanskrit: str = ""
    text_english: str = ""
    text_hindi: str = ""
    rule_type: str = "general"
