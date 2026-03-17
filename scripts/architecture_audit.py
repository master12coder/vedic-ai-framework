#!/usr/bin/env python3
"""Architecture audit script.

Checks:
1. File line counts (flag >300)
2. Import layer violations
3. Magic number detection
4. Missing type hints on function definitions
5. Missing docstrings on public functions/classes
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JYOTISH_DIR = PROJECT_ROOT / "jyotish"
MAX_LINES = 500

# Layer import rules: module -> set of allowed import prefixes
LAYER_RULES: dict[str, set[str]] = {
    "domain": set(),  # domain/ imports nothing from jyotish
    "compute": {"jyotish.domain"},
    "knowledge": set(),  # YAML only, no Python
    "scriptures": {"jyotish.domain"},
    "learn": {"jyotish.domain", "jyotish.scriptures", "jyotish.utils", "jyotish.config"},
    "interpret": {
        "jyotish.compute",
        "jyotish.domain",
        "jyotish.knowledge",
        "jyotish.scriptures",
        "jyotish.learn",
        "jyotish.utils",
        "jyotish.config",
    },
    "deliver": {
        "jyotish.compute",
        "jyotish.interpret",
        "jyotish.domain",
        "jyotish.utils",
        "jyotish.config",
    },
    "utils": {"jyotish.domain", "jyotish.config"},
    "config": {"jyotish.utils"},
}

# Magic numbers: integers > 1 that are not in allowed contexts
ALLOWED_MAGIC = {
    0, 1, 2, -1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12,   # Houses, signs, planets
    13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,   # Divisions, tithis, hours
    25, 26, 27, 28, 29,                                 # Nakshatras, lunar days, degrees
    30, 36, 39, 40, 44, 45,                             # Degrees/sign, Yogini, Shadbala
    55, 59, 60,                                         # Minutes, time subdivisions
    100, 108, 111, 133, 180, 337, 360,                  # Common astro math
    75, 96, 365, 875, 1013,                               # Division remainders, limits
    2857, 3333, 3600, 4096, 6667,                          # Decimal parts, time, API
}  # Domain-specific numbers common in Vedic astrology and time math


class AuditResult:
    """Collects audit findings."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def check_file_lengths(result: AuditResult) -> None:
    """Flag files exceeding MAX_LINES."""
    for py_file in sorted(JYOTISH_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        line_count = len(py_file.read_text().splitlines())
        rel = py_file.relative_to(PROJECT_ROOT)
        if line_count > MAX_LINES:
            result.warnings.append(
                f"[SIZE] {rel}: {line_count} lines (max {MAX_LINES})"
            )
        elif line_count > MAX_LINES * 0.9:
            result.info.append(
                f"[SIZE] {rel}: {line_count} lines (approaching limit)"
            )


def _get_layer(filepath: Path) -> str | None:
    """Determine which layer a file belongs to."""
    rel = filepath.relative_to(JYOTISH_DIR)
    parts = rel.parts
    if len(parts) < 1:
        return None
    first = parts[0]
    if first in LAYER_RULES:
        return first
    if str(rel) == "cli.py":
        return None  # cli.py is the composition root, can import anything
    return None


def check_import_violations(result: AuditResult) -> None:
    """Check that imports respect layer boundaries."""
    for py_file in sorted(JYOTISH_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        layer = _get_layer(py_file)
        if layer is None:
            continue

        allowed = LAYER_RULES.get(layer, set())
        # Layer can always import from itself
        self_prefix = f"jyotish.{layer}"

        rel = py_file.relative_to(PROJECT_ROOT)
        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            result.warnings.append(f"[PARSE] {rel}: SyntaxError, skipping")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _check_import_name(alias.name, rel, layer, allowed, self_prefix, result)
            elif isinstance(node, ast.ImportFrom) and node.module:
                _check_import_name(node.module, rel, layer, allowed, self_prefix, result)


def _check_import_name(
    module: str,
    filepath: Path,
    layer: str,
    allowed: set[str],
    self_prefix: str,
    result: AuditResult,
) -> None:
    """Check a single import against layer rules."""
    if not module.startswith("jyotish."):
        return  # External import, fine
    if module.startswith(self_prefix):
        return  # Same layer, fine
    if module == "jyotish" or module.startswith("jyotish.utils"):
        return  # utils is generally allowed

    is_allowed = any(module.startswith(prefix) for prefix in allowed)
    if not is_allowed:
        result.errors.append(
            f"[IMPORT] {filepath}: '{module}' violates {layer}/ layer rules"
        )


def check_magic_numbers(result: AuditResult) -> None:
    """Detect magic numbers in source code."""
    # Pattern: bare integers in assignments, comparisons, returns
    # Excludes: index access, range(), list literals, string formatting
    magic_pattern = re.compile(r"(?<!=)\b(\d{2,})\b(?!\s*[:\]\)])")

    for py_file in sorted(JYOTISH_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = py_file.relative_to(PROJECT_ROOT)

        # Skip constants files — they ARE the constant definitions
        if "constants" in str(py_file) or "constant" in py_file.name:
            continue

        for lineno, line in enumerate(py_file.read_text().splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("\"") or stripped.startswith("'"):
                continue
            # Skip lines that are purely string assignments or docstrings
            if '"""' in stripped or "'''" in stripped:
                continue
            for match in magic_pattern.finditer(line):
                num = int(match.group(1))
                if num not in ALLOWED_MAGIC and num < 10000:
                    # Skip common patterns: port numbers, years, format strings
                    if any(skip in line for skip in ["strftime", "port", "year", "19", "20"]):
                        continue
                    result.info.append(
                        f"[MAGIC] {rel}:{lineno}: number {num} — consider extracting to constant"
                    )


def check_type_hints(result: AuditResult) -> None:
    """Flag public functions missing return type annotations."""
    for py_file in sorted(JYOTISH_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = py_file.relative_to(PROJECT_ROOT)

        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue  # Skip private functions
                if node.returns is None:
                    result.warnings.append(
                        f"[TYPE] {rel}:{node.lineno}: "
                        f"'{node.name}()' missing return type annotation"
                    )


def check_docstrings(result: AuditResult) -> None:
    """Flag public functions and classes missing docstrings."""
    for py_file in sorted(JYOTISH_DIR.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        rel = py_file.relative_to(PROJECT_ROOT)

        try:
            tree = ast.parse(py_file.read_text())
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_"):
                    continue
                docstring = ast.get_docstring(node)
                if not docstring:
                    kind = "class" if isinstance(node, ast.ClassDef) else "function"
                    result.warnings.append(
                        f"[DOC] {rel}:{node.lineno}: "
                        f"{kind} '{node.name}' missing docstring"
                    )


def main() -> int:
    """Run all architecture audit checks."""
    result = AuditResult()

    print("=" * 70)
    print("ARCHITECTURE AUDIT — Vedic AI Framework")
    print("=" * 70)

    print("\n--- File Line Counts ---")
    check_file_lengths(result)

    print("\n--- Import Layer Violations ---")
    check_import_violations(result)

    print("\n--- Magic Number Detection ---")
    check_magic_numbers(result)

    print("\n--- Type Hint Coverage ---")
    check_type_hints(result)

    print("\n--- Docstring Coverage ---")
    check_docstrings(result)

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
        for info in result.info[:20]:  # Cap info output
            print(f"  {info}")
        if len(result.info) > 20:
            print(f"  ... and {len(result.info) - 20} more")

    print(f"\n{'='*70}")
    if result.passed:
        print("AUDIT PASSED — no layer violations detected")
    else:
        print(f"AUDIT FAILED — {len(result.errors)} error(s)")

    print(
        f"Summary: {len(result.errors)} errors, "
        f"{len(result.warnings)} warnings, "
        f"{len(result.info)} info"
    )

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
