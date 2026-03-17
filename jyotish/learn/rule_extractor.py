"""Extract learned rules from validated corrections."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict

from jyotish.config import get as cfg_get
from jyotish.learn.corrections import PanditCorrection, PanditCorrectionStore


@dataclass
class LearnedRule:
    """A rule extracted from validated Pandit Ji corrections."""

    rule_id: str
    category: str
    lagna: str
    planets: list[str]
    houses: list[int]
    rule_text: str
    reasoning: str
    prompt_addition: str
    source_correction_ids: list[str]
    confidence: float
    occurrence_count: int


class RuleExtractor:
    """Extract learned rules from validated corrections."""

    def __init__(self, store: PanditCorrectionStore | None = None):
        self._store = store or PanditCorrectionStore()
        self._min_confidence = float(cfg_get("learning.min_confidence_for_rule", 0.5))

    def extract_rules(self) -> list[LearnedRule]:
        """Extract rules from all validated corrections.

        Groups corrections by (category, lagna, planets) and creates
        a LearnedRule when confidence >= threshold.
        """
        corrections = self._store.list_corrections(status="validated")

        # Group by (category, lagna, frozenset(planets))
        groups: dict[tuple, list[PanditCorrection]] = defaultdict(list)
        for c in corrections:
            key = (c.category, c.lagna, frozenset(c.planets_involved))
            groups[key].append(c)

        rules = []
        for (category, lagna, planets_set), group in groups.items():
            avg_confidence = sum(c.confidence for c in group) / len(group)
            if avg_confidence < self._min_confidence:
                continue

            planets = sorted(planets_set)
            houses = sorted(set(h for c in group for h in c.houses_involved))

            # Combine the pandit's wisdom into a rule
            rule_text = group[0].pandit_said
            if len(group) > 1:
                rule_text = "; ".join(c.pandit_said for c in group[:3])

            reasoning = group[0].pandit_reasoning
            if len(group) > 1:
                reasoning = "; ".join(c.pandit_reasoning for c in group[:3] if c.pandit_reasoning)

            prompt_addition = (
                f"For {lagna} lagna with {', '.join(planets) if planets else 'general'}: "
                f"{rule_text} (Pandit Ji reasoning: {reasoning})"
            )

            rule = LearnedRule(
                rule_id=f"rule_{category}_{lagna}_{len(rules)}",
                category=category,
                lagna=lagna,
                planets=planets,
                houses=houses,
                rule_text=rule_text,
                reasoning=reasoning,
                prompt_addition=prompt_addition,
                source_correction_ids=[c.id for c in group],
                confidence=round(avg_confidence, 2),
                occurrence_count=len(group),
            )
            rules.append(rule)

        return rules

    def save_rules(self, output_path: str | Path | None = None) -> Path:
        """Extract and save rules to a JSON file."""
        rules = self.extract_rules()
        if output_path is None:
            output_path = Path(cfg_get("learning.data_dir", "data/pandit_corrections")) / "learned_rules.json"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump([asdict(r) for r in rules], f, indent=2, ensure_ascii=False)

        return output_path

    def get_prompt_additions(
        self,
        lagna: str | None = None,
        category: str | None = None,
        max_rules: int | None = None,
    ) -> str:
        """Generate prompt additions from learned rules."""
        if max_rules is None:
            max_rules = int(cfg_get("learning.max_rules_in_prompt", 5))

        rules = self.extract_rules()

        if lagna:
            rules = [r for r in rules if r.lagna == lagna or not r.lagna]
        if category:
            rules = [r for r in rules if r.category == category]

        rules.sort(key=lambda r: r.confidence, reverse=True)
        rules = rules[:max_rules]

        if not rules:
            return ""

        lines = ["## Learned Rules from Pandit Ji"]
        for r in rules:
            lines.append(f"- {r.prompt_addition} [Confidence: {r.confidence}]")
        return "\n".join(lines)
