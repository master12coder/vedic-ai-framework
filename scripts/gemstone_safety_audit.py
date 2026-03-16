#!/usr/bin/env python3
"""Gemstone safety audit script.

Checks:
1. Scan all prompt templates for prohibited stone names per lagna
2. Scan lordship_rules.yaml for completeness (all 12 lagnas, all fields)
3. Report any gaps in contraindication data
4. Verify gemstone_logic.yaml coverage for all 9 planets
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "jyotish" / "knowledge"
PROMPTS_DIR = PROJECT_ROOT / "jyotish" / "interpret" / "prompts"

ALL_LAGNAS = [
    "mesha", "vrishabha", "mithuna", "karka", "simha", "kanya",
    "tula", "vrischika", "dhanu", "makara", "kumbha", "meena",
]
LAGNA_ENGLISH = {
    "mesha": "Aries", "vrishabha": "Taurus", "mithuna": "Gemini",
    "karka": "Cancer", "simha": "Leo", "kanya": "Virgo",
    "tula": "Libra", "vrischika": "Scorpio", "dhanu": "Sagittarius",
    "makara": "Capricorn", "kumbha": "Aquarius", "meena": "Pisces",
}

ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
REQUIRED_LAGNA_FIELDS = [
    "lagna_number", "sign", "sign_lord", "house_lords",
    "yogakaraka", "functional_benefics", "functional_malefics",
    "maraka", "gemstone_recommendations",
]

# Known stone names for matching
STONE_NAMES = {
    "Sun": ["Ruby", "Manikya"],
    "Moon": ["Pearl", "Moti"],
    "Mars": ["Red Coral", "Moonga"],
    "Mercury": ["Emerald", "Panna"],
    "Jupiter": ["Yellow Sapphire", "Pukhraj"],
    "Venus": ["Diamond", "Heera"],
    "Saturn": ["Blue Sapphire", "Neelam"],
    "Rahu": ["Hessonite", "Gomed"],
    "Ketu": ["Cat's Eye", "Lehsuniya"],
}


class SafetyResult:
    """Collects safety audit findings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def load_lordship_rules() -> dict:
    """Load lordship_rules.yaml."""
    path = KNOWLEDGE_DIR / "lordship_rules.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_gemstone_logic() -> dict:
    """Load gemstone_logic.yaml."""
    path = KNOWLEDGE_DIR / "gemstone_logic.yaml"
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def check_lordship_completeness(result: SafetyResult) -> dict:
    """Check that lordship_rules.yaml has data for all 12 lagnas."""
    data = load_lordship_rules()
    lagnas = data.get("lagnas", {})

    for lagna in ALL_LAGNAS:
        if lagna not in lagnas:
            result.errors.append(
                f"[LORDSHIP] Missing lagna: {lagna} ({LAGNA_ENGLISH[lagna]})"
            )
            continue

        rules = lagnas[lagna]
        for field in REQUIRED_LAGNA_FIELDS:
            if field not in rules:
                result.errors.append(
                    f"[LORDSHIP] {lagna}: missing field '{field}'"
                )

        # Check gemstone recommendations cover all 7 planets
        gem_recs = rules.get("gemstone_recommendations", {})
        for planet in ALL_PLANETS:
            if planet not in gem_recs:
                result.warnings.append(
                    f"[LORDSHIP] {lagna}: no gemstone recommendation for {planet}"
                )
            else:
                rec = gem_recs[planet]
                if "recommendation" not in rec:
                    result.errors.append(
                        f"[LORDSHIP] {lagna}/{planet}: missing 'recommendation' field"
                    )
                if "gemstone" not in rec:
                    result.errors.append(
                        f"[LORDSHIP] {lagna}/{planet}: missing 'gemstone' field"
                    )

        # Check maraka has at least one entry
        maraka = rules.get("maraka", [])
        if not maraka:
            result.errors.append(
                f"[LORDSHIP] {lagna}: no maraka planets defined"
            )

    return data


def check_gemstone_logic_coverage(result: SafetyResult) -> None:
    """Check gemstone_logic.yaml covers all planets and contraindications."""
    data = load_gemstone_logic()
    gemstones = data.get("gemstones", {})

    all_stone_planets = list(ALL_PLANETS) + ["Rahu", "Ketu"]
    for planet in all_stone_planets:
        if planet not in gemstones:
            result.errors.append(
                f"[GEMSTONE] Missing gemstone data for {planet}"
            )
            continue

        info = gemstones[planet]
        required = ["primary", "finger", "metal", "day", "mantra"]
        for field in required:
            if field not in info:
                result.warnings.append(
                    f"[GEMSTONE] {planet}: missing field '{field}'"
                )

        primary = info.get("primary", {})
        if "name_en" not in primary:
            result.errors.append(
                f"[GEMSTONE] {planet}: missing primary.name_en"
            )
        if "name_hi" not in primary:
            result.warnings.append(
                f"[GEMSTONE] {planet}: missing primary.name_hi"
            )

    # Check contraindications exist
    contras = data.get("contraindications", [])
    if len(contras) < 3:
        result.errors.append(
            f"[GEMSTONE] Only {len(contras)} contraindications defined (need at least 3)"
        )

    # Check planetary friendships
    friendships = data.get("planetary_friendships", {})
    if "friends" not in friendships:
        result.errors.append("[GEMSTONE] Missing planetary_friendships.friends")
    if "enemies" not in friendships:
        result.errors.append("[GEMSTONE] Missing planetary_friendships.enemies")


def check_prompt_templates(result: SafetyResult, lordship_data: dict) -> None:
    """Scan prompt templates for hardcoded stone recommendations.

    Templates should not contain hardcoded stone names in recommendation
    context — they should use Jinja2 variables from lordship context.
    """
    if not PROMPTS_DIR.exists():
        result.errors.append("[PROMPT] Prompts directory not found")
        return

    lagnas = lordship_data.get("lagnas", {})

    for template_path in sorted(PROMPTS_DIR.glob("*.md")):
        content = template_path.read_text()
        content_lower = content.lower()
        rel = template_path.relative_to(PROJECT_ROOT)

        # Check for hardcoded stone names outside Jinja2 variable references
        for planet, stone_names in STONE_NAMES.items():
            for stone in stone_names:
                stone_lower = stone.lower()
                if stone_lower in content_lower:
                    # Allow if it's inside a Jinja2 expression {{ }}
                    # or in a context description, not a raw recommendation
                    # Simple heuristic: flag if near "recommend" without "prohibit"
                    lines_with_stone = [
                        (i, line) for i, line in enumerate(content.splitlines(), 1)
                        if stone_lower in line.lower()
                    ]
                    for lineno, line in lines_with_stone:
                        line_lower = line.lower()
                        # Skip Jinja2 variables and conditional blocks
                        if "{{" in line or "{%" in line:
                            continue
                        # Flag hardcoded recommendations
                        if "recommend" in line_lower and "prohibit" not in line_lower:
                            result.warnings.append(
                                f"[PROMPT] {rel}:{lineno}: "
                                f"hardcoded '{stone}' near 'recommend' — "
                                f"use Jinja2 variable instead"
                            )

    # Check that system_prompt.md references mandatory rules
    sys_prompt = PROMPTS_DIR / "system_prompt.md"
    if sys_prompt.exists():
        sys_content = sys_prompt.read_text()
        if "MANDATORY RULES" not in sys_content:
            result.errors.append(
                "[PROMPT] system_prompt.md: missing MANDATORY RULES section"
            )
        if "prohibited" not in sys_content.lower():
            result.errors.append(
                "[PROMPT] system_prompt.md: no mention of prohibited stones"
            )
        if "maraka" not in sys_content.lower():
            result.errors.append(
                "[PROMPT] system_prompt.md: no mention of maraka planets"
            )
    else:
        result.errors.append("[PROMPT] system_prompt.md not found")

    # Check remedy_generation.md has decision framework
    remedy = PROMPTS_DIR / "remedy_generation.md"
    if remedy.exists():
        remedy_content = remedy.read_text()
        if "DECISION FRAMEWORK" not in remedy_content.upper():
            result.errors.append(
                "[PROMPT] remedy_generation.md: missing GEMSTONE DECISION FRAMEWORK"
            )
        if "NEVER RECOMMEND" not in remedy_content.upper():
            result.errors.append(
                "[PROMPT] remedy_generation.md: missing NEVER RECOMMEND section"
            )
    else:
        result.errors.append("[PROMPT] remedy_generation.md not found")


def check_prohibited_consistency(result: SafetyResult, lordship_data: dict) -> None:
    """Verify prohibited stones are consistent across maraka and gemstone data.

    A planet can be both maraka AND lagnesh/yogakaraka/trikona-lord. In these
    dual-lordship cases, classical texts allow wearing the stone because the
    benefic lordship dominates. The audit flags pure maraka planets (those NOT
    also a functional benefic) that have 'wear' recommendations.
    """
    lagnas = lordship_data.get("lagnas", {})

    for lagna_key, rules in lagnas.items():
        maraka_planets = {m.get("planet") for m in rules.get("maraka", [])}
        benefic_planets = {b.get("planet") for b in rules.get("functional_benefics", [])}
        malefic_planets = {m.get("planet") for m in rules.get("functional_malefics", [])}
        lagna_lord = rules.get("sign_lord", "")
        yogakaraka = rules.get("yogakaraka", {})
        yogakaraka_planet = yogakaraka.get("planet", "") if isinstance(yogakaraka, dict) else ""
        gem_recs = rules.get("gemstone_recommendations", {})

        for planet in maraka_planets:
            if not planet or planet not in gem_recs:
                continue
            rec = gem_recs[planet].get("recommendation", "")
            if rec != "wear":
                continue

            # Dual-lordship exception: maraka + benefic/lagnesh/yogakaraka is OK
            is_also_benefic = (
                planet in benefic_planets
                or planet == lagna_lord
                or planet == yogakaraka_planet
            )
            if is_also_benefic:
                result.info.append(
                    f"[DUAL] {lagna_key}: {planet} is maraka + benefic/lagnesh — "
                    f"'wear' is acceptable (dual lordship)"
                )
            else:
                result.errors.append(
                    f"[CONSISTENCY] {lagna_key}: {planet} is MARAKA "
                    f"but gemstone recommendation is 'wear' — MUST be 'avoid'"
                )

        for planet in malefic_planets:
            if not planet or planet not in gem_recs:
                continue
            rec = gem_recs[planet].get("recommendation", "")
            if rec == "wear":
                result.errors.append(
                    f"[CONSISTENCY] {lagna_key}: {planet} is functional MALEFIC "
                    f"but gemstone recommendation is 'wear' — should be 'avoid' or 'neutral'"
                )


def main() -> int:
    """Run all gemstone safety audit checks."""
    result = SafetyResult()

    print("=" * 70)
    print("GEMSTONE SAFETY AUDIT — Vedic AI Framework")
    print("=" * 70)

    print("\n--- Lordship Rules Completeness ---")
    lordship_data = check_lordship_completeness(result)

    print("\n--- Gemstone Logic Coverage ---")
    check_gemstone_logic_coverage(result)

    print("\n--- Prompt Template Scan ---")
    check_prompt_templates(result, lordship_data)

    print("\n--- Prohibited Stone Consistency ---")
    check_prohibited_consistency(result, lordship_data)

    # Print results
    if result.errors:
        print(f"\n{'='*70}")
        print(f"ERRORS ({len(result.errors)}):")
        for err in result.errors:
            print(f"  {err}")

    if result.warnings:
        print(f"\n{'='*70}")
        print(f"WARNINGS ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"  {warn}")

    if result.info:
        print(f"\n{'='*70}")
        print(f"INFO ({len(result.info)}):")
        for info in result.info:
            print(f"  {info}")

    print(f"\n{'='*70}")
    if result.passed:
        print("SAFETY AUDIT PASSED — no critical issues found")
    else:
        print(f"SAFETY AUDIT FAILED — {len(result.errors)} error(s)")

    print(
        f"Summary: {len(result.errors)} errors, "
        f"{len(result.warnings)} warnings, "
        f"{len(result.info)} info"
    )

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
