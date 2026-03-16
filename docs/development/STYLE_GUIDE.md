# Style Guide

## Python Standards

| Standard | What                          | Enforced By |
|----------|-------------------------------|-------------|
| PEP 8    | Code style                    | ruff        |
| PEP 257  | Docstring conventions         | ruff        |
| PEP 484  | Type hints                    | mypy        |
| PEP 621  | pyproject.toml metadata       | Manual      |

## Formatting

- **Formatter:** ruff format (Black-compatible)
- **Line length:** 100 characters
- **Imports:** sorted by ruff (isort-compatible), grouped: stdlib → third-party → local
- **Quotes:** double quotes for strings
- **Trailing commas:** yes, in multi-line structures

## Type Hints

**Mandatory** on all function signatures:

```python
# Good
def compute_chart(name: str, dob: str, tob: str, place: str, gender: str) -> ChartData:

# Bad — missing return type
def compute_chart(name, dob, tob, place, gender):
```

Use modern syntax (Python 3.11+):
```python
# Good
def get_planets(chart: ChartData) -> dict[str, PlanetData]:
    items: list[str] = []
    value: int | None = None

# Avoid legacy
from typing import Dict, List, Optional  # Not needed in 3.11+
```

## Docstrings

Google-style, required on all public functions and classes:

```python
def recommend_gemstone(
    planet: str,
    is_functional_benefic: bool,
    is_maraka: bool = False,
) -> GemstoneRecommendation:
    """Generate a gemstone recommendation based on chart context.

    Args:
        planet: Planet name (e.g., "Jupiter", "Mercury").
        is_functional_benefic: Whether planet is benefic for the lagna.
        is_maraka: Whether planet is a maraka planet.

    Returns:
        GemstoneRecommendation with stone, reasoning, and contraindications.

    Raises:
        ValueError: If planet name is not recognized.
    """
```

## Data Structures

**Always dataclasses**, never raw dicts for domain data:

```python
# Good
@dataclass
class PlanetData:
    name: str
    sign: str
    house: int
    dignity: str

# Bad
planet = {"name": "Jupiter", "sign": "Vrishabha", "house": 12, "dignity": "neutral"}
```

## File Size

**Maximum 300 lines per file.** If a file exceeds this:
1. Extract related functions into a new module
2. Use the same directory — create `_helpers.py` or domain-specific sub-module
3. Keep the public API in the original file, move implementation

## Constants

Centralized in `domain/constants/`, never scattered:

```python
# Good — from constants module
from jyotish.domain.constants.signs import SIGNS, SIGNS_EN

# Bad — magic values in code
lagna_name = ["Mesha", "Vrishabha", "Mithuna", ...][index]
if house == 7:  # What is 7?
```

## Error Handling

Use custom exceptions from `domain/exceptions.py`:

```python
# Good
from jyotish.domain.exceptions import ChartComputationError
raise ChartComputationError(f"Invalid date: {dob}")

# Bad
raise Exception("something went wrong")
raise ValueError("bad input")  # OK for stdlib validation, not domain errors
```

## Logging

Structured logging via `utils/logging_config.py`:

```python
from jyotish.utils.logging_config import get_logger
logger = get_logger(__name__)

logger.info("Computing chart for %s", name)
logger.warning("No lordship rules for lagna: %s", lagna_sign)
logger.error("LLM backend failed: %s", error)
```

## Hindi / Bilingual Text

- Hindi text in Devanagari script, never transliterated Latin
- English text in plain ASCII
- Key terms provided in both: `"Mithuna (Gemini / मिथुन)"`
- YAML knowledge files use both Hindi and English names

## Naming Conventions

| Entity          | Convention           | Example                    |
|-----------------|----------------------|----------------------------|
| Modules         | `snake_case.py`      | `gemstone_advisor.py`      |
| Classes         | `PascalCase`         | `ChartData`                |
| Functions       | `snake_case`         | `compute_chart`            |
| Constants       | `UPPER_SNAKE_CASE`   | `SIGNS_EN`                 |
| Private         | `_leading_underscore` | `_load_yaml`              |
| Test functions  | `test_what_condition_expected` | `test_lagna_mithuna_jupiter_maraka` |
| YAML keys       | `snake_case`         | `functional_benefics`      |
| Prompt templates| `snake_case.md`      | `remedy_generation.md`     |
