# Jyotish — Architecture: Install, Patterns, Workflow & Docs

> For the 3-package architecture, layer rules, and package details,
> see `overview.md`.

---

## Install Options

```bash
# User: everything
pip install daivai

# Developer: just the engine (for their own app)
pip install daivai-engine

# Researcher: engine + products (no CLI/web)
pip install daivai-products

# Development (all packages linked)
git clone https://github.com/master12coder/daivai
cd daivai
uv sync

# With LLM backend
pip install "jyotish[groq]"      # Free cloud
pip install "jyotish[ollama]"    # Free local
pip install "jyotish[claude]"    # Best quality
```

---

## pyproject.toml (Root)

```toml
[project]
name = "daivai"
version = "1.0.0"
requires-python = ">=3.12"

[tool.uv.workspace]
members = ["engine", "products", "apps"]

[tool.uv.sources]
daivai-engine = { workspace = true }
daivai-products = { workspace = true }

[tool.ruff]
target-version = "py312"
line-length = 100
src = ["engine/src", "products/src", "apps/src"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.12"
disallow_untyped_defs = true
warn_return_any = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "safety: gemstone/interpretation safety tests",
    "slow: slow tests",
]
```

---

## Modern Python Patterns Used

```python
# Pydantic v2 models (not raw dataclasses)
from pydantic import BaseModel, Field

class PlanetPosition(BaseModel):
    name: str
    longitude: float = Field(ge=0, lt=360)
    sign: int = Field(ge=0, lt=12)
    degree: float = Field(ge=0, lt=30)
    nakshatra: int = Field(ge=0, lt=27)
    pada: int = Field(ge=1, le=4)
    house: int = Field(ge=1, le=12)
    retrograde: bool = False
    combust: bool = False
    dignity: str  # exalted, debilitated, own, mooltrikona, neutral

# Python 3.12 match statements
match planet.dignity:
    case "exalted":
        strength *= 1.5
    case "debilitated":
        strength *= 0.5
    case "own" | "mooltrikona":
        strength *= 1.25
    case _:
        pass

# Protocol for LLM abstraction
from typing import Protocol

class LLMBackend(Protocol):
    async def generate(self, system: str, user: str) -> str: ...
    def name(self) -> str: ...

# Factory with match
def get_llm(provider: str) -> LLMBackend:
    match provider:
        case "groq": return GroqBackend()
        case "ollama": return OllamaBackend()
        case "claude": return ClaudeBackend()
        case "none": return OfflineBackend()
        case _: raise ValueError(f"Unknown: {provider}")
```

---

## What Claude Code/Cowork Does Daily

### Morning (automated or on-demand)
```bash
# Claude Cowork runs these checks
make audit          # Architecture + safety
make test           # All tests pass?
make lint           # Code clean?

# If any fail, Claude Code fixes automatically
```

### When you give a task
```
You: "Add Lal Kitab remedies for Saturn in 7th house"

Claude Code:
1. Reads CLAUDE.md (auto)
2. Checks docs/architecture/ for where this goes
3. Adds to engine/src/daivai_engine/knowledge/lal_kitab.yaml
4. Updates products/src/daivai_products/remedies/lal_kitab.py
5. Adds test in tests/products/remedies/test_lal_kitab.py
6. Runs make all
7. Commits: "feat(remedies): add Lal Kitab Saturn in 7th house rules"
```

### Daily companion operation
```
# Cron job or manual
daivai daily --chart charts/manish.json --level medium

# Telegram bot runs 24/7
jyotish bot start

# User gets WhatsApp/Telegram message at 5:30 AM:
# "7/10 | Green | ओम् बुधाय नमः x 11 | Avoid 3-4:30 PM"
```

---

## File Count Target

| Package | Files | Why |
|---|---|---|
| engine/ | ~35 | Computation + models + YAML + scriptures |
| products/ | ~40 | 7 products + interpret + store |
| apps/ | ~15 | CLI + web + telegram |
| tests/ | ~50 | Mirror source structure |
| docs/ | ~15 | Architecture + products + dev guides |
| scripts/ | ~4 | Audit tools |
| **Total** | **~160 files** | Manageable. Not bloated. |

Each file: under 300 lines. Total codebase: ~15,000-20,000 lines.

---

## CLAUDE.md (Keep This Short)

```
# Rules for Claude Code

Read docs/architecture/ for full context.

## Commands
make test | make lint | make audit | make all

## Hard Rules
- 300-line file limit
- Pydantic v2 for all models
- Type hints everywhere
- Constants in engine/constants.py
- Gemstones from lordship_rules.yaml ONLY
- Every LLM prompt gets lordship rules + prohibited stones
- Post-validate every LLM output
- Layer: engine <- products <- apps (never reverse)

## Test Fixture
Manish: 13/03/1989, 12:17 PM, Varanasi
Lagna: Mithuna | Moon: Rohini Pada 2
Panna=SAFE | Pukhraj=PROHIBITED | Jupiter=MARAKA
```

30 lines. Done.

---

## Docs Structure

```
docs/
+-- architecture/
|   +-- overview.md         # Architecture, layers, packages
|   +-- overview-patterns.md # This document
|   +-- layers.md           # Layer rules + examples
|   +-- decisions/          # ADRs (numbered)
+-- products/
|   +-- kundali.md          # 18-section visual kundali spec
|   +-- daily.md            # 3-level daily companion spec
|   +-- matching.md         # Compatibility spec
|   +-- remedies.md         # Gemstone + routine spec
|   +-- predictions.md      # Accuracy tracker spec
|   +-- pandit.md           # Professional tools spec
|   +-- muhurta.md          # Timing finder spec
+-- development/
|   +-- setup.md            # Install + first run
|   +-- testing.md          # Strategy + fixtures
+-- vedic/
|   +-- gemstone-safety.md  # Safety protocol
|   +-- lordship-guide.md   # Per-lagna rules
+-- roadmap.md              # Build order + timeline
```

No random .md at root. Ever.
