# CLAUDE.md — DaivAI Framework

> Read this FIRST every session. Follow EVERY rule. No exceptions.

## Architecture (FROZEN)

```
engine/       Pure math. Swiss Ephemeris + YAML rules. Zero AI.
products/     AI interpretation + 7 product plugins + storage.
apps/         CLI + Web + Telegram. Thin adapters.

engine/ imports NOTHING from products/ or apps/.
products/ imports ONLY from engine/.
apps/ imports from products/ and engine/.
Plugins NEVER import each other.
```

## Decision Tree (EVERY task — follow top to bottom)

```
STEP 1: What type of change?

  Bug fix / typo / config change
    → Find the file. Fix it. Test. Commit.

  New constant, model, or computation
    → engine/

  New YAML rule (lordship, gemstone, mantra, remedy, yoga)
    → engine/knowledge/*.yaml

  New scripture rule (BPHS verse)
    → engine/scriptures/bphs/*.yaml

  New interpretation prompt or LLM logic
    → products/interpret/

  New safety validation
    → products/interpret/validator.py

  Pandit correction or learning logic
    → products/plugins/pandit/

STEP 2: Is it a user-facing feature?

  YES → Does a plugin already handle this domain?
    → YES: Add to that plugin. Do NOT create a new plugin.
    → NO:  Create products/plugins/{name}/
           MUST have __init__.py with: PLUGIN_NAME, COMMANDS, DESCRIPTION
           MUST have at least one test
           MUST NOT import other plugins

  NO → It belongs in engine/ or products/interpret/

STEP 3: Does user need a new command or screen?

  New CLI command → apps/cli/{name}.py
    Auto-register from plugin COMMANDS

  New Telegram handler → apps/telegram/handlers.py

  New web route → apps/web/routes.py
```

## File Rules

```
Max 300 lines per file. Split if approaching.
One file = one responsibility.
Every public function has type hints + docstring.
Pydantic v2 for all models (not dataclasses).
Python 3.12+ features: match statements, type params.
Constants in engine/constants.py. ONE file. Not scattered.
Exceptions in engine/exceptions.py. ONE file. Not scattered.
Config in engine/knowledge/*.yaml. Not hardcoded.
```

## Import Rules (CI enforced — scripts/check_imports.py)

```
ALLOWED:
  engine/compute/    → engine/models/, engine/constants, engine/exceptions
  engine/knowledge/  → engine/models/, engine/constants
  engine/scriptures/ → engine/models/, engine/constants
  products/interpret/→ engine/*
  products/plugins/* → engine/*, products/interpret/, products/store/
  products/store/    → engine/models/
  apps/*             → products/*, engine/*

FORBIDDEN:
  engine/ → products/ or apps/           (NEVER)
  products/ → apps/                      (NEVER)
  plugins/daily/ → plugins/kundali/      (NEVER — plugins isolated)
  plugins/ANY/ → plugins/OTHER/          (NEVER)
  ANY file → LLM backend directly        (use products/interpret/factory.py)
  ANY file → hardcoded planet positions  (use engine/compute/)
  ANY file → hardcoded gemstone rules    (use engine/knowledge/)
```

## Safety Rules (NON-NEGOTIABLE)

```
1. Gemstone recommendations come ONLY from engine/knowledge/lordship_rules.yaml
2. Every LLM prompt template MUST include:
   - Lagna-specific lordship classification
   - Prohibited stones list for that lagna
   - MARAKA planets named explicitly
3. Every LLM response MUST be scanned by products/interpret/validator.py:
   - Prohibited stone mentioned as recommended → BLOCK + regenerate
   - MARAKA planet called "benefic" without caveat → BLOCK + regenerate
   - Generic prediction without chart factor → FLAG
4. If validator finds violation → fix it before returning to user
5. NEVER recommend Pukhraj/Moonga/Moti/Manikya for Mithuna lagna

Test fixture for safety:
  Manish Chaurasia: 13/03/1989, 12:17 PM, Varanasi
  Lagna: Mithuna | Moon: Rohini Pada 2 | Current: Jupiter > Mercury
  Panna (Emerald) = RECOMMENDED (Lagnesh stone)
  Pukhraj (Yellow Sapphire) = PROHIBITED (Jupiter = 7th MARAKA)
  Moonga (Red Coral) = PROHIBITED (Mars = 6th lord)
  Moti (Pearl) = PROHIBITED (Moon = 2nd MARAKA)
```

## Plugin Contract

```
Every plugin in products/plugins/{name}/ MUST have:

__init__.py containing:
  PLUGIN_NAME: str = "daily"
  DESCRIPTION: str = "Personalized daily guidance based on chart + transits"
  COMMANDS: dict = {
      "daily": {"help": "Get today's guidance", "handler": "run_daily"},
  }

At least one module with actual logic (not empty).
At least one test in tests/products/plugins/{name}/.
Zero imports from other plugins.
```

## Testing Rules

```
Run: make test (pytest must pass 100% before any commit)

Test naming: test_{what}_{expected}_{condition}
  Example: test_pukhraj_prohibited_for_mithuna_lagna

Markers:
  @pytest.mark.safety    → gemstone/interpretation safety
  @pytest.mark.slow      → heavy computation

Coverage: 80% minimum on engine/ and products/interpret/

Primary fixture (conftest.py):
  manish_chart → pre-computed ChartData for Manish Chaurasia
  Use this for ALL product tests.
```

## Git Rules

```
Conventional commits:
  feat(daily): add medium level formatting
  fix(safety): block Pukhraj recommendation for Mithuna
  refactor(engine): split yoga_detector into focused modules
  test(remedies): add Lal Kitab Saturn in 7th test
  docs: update daily product spec

Run make all before EVERY commit. If it fails, fix first.

make all = make lint + make typecheck + make test + make audit
```

## Commands

```
make test       → pytest
make lint       → ruff check + ruff format --check
make typecheck  → mypy engine/src/ products/src/
make audit      → python scripts/check_imports.py + check_plugins.py + safety_audit.py
make all        → all of the above
make run        → daivai --help
```

## When Uncertain

```
Q: Where does this code go?
A: Follow the decision tree above. If still unclear → engine/.

Q: Should I create a new plugin or enhance existing?
A: If >70% of the logic overlaps with existing plugin → enhance.
   If it's a genuinely different user need → new plugin.

Q: Should I modify engine/ for a product need?
A: engine/ changes ONLY if the computation/model/rule is universal.
   Product-specific logic NEVER goes in engine/.

Q: A YAML rule seems wrong. Should I change it?
A: NEVER change lordship_rules.yaml without explicit instruction.
   Other YAML files: change if you can cite a scripture source.

Q: The LLM output has errors. What do I do?
A: Fix the prompt template, not the validator.
   Validator is the last defense, not the primary fix.

Q: File is approaching 300 lines. What do I do?
A: Split into two files by responsibility.
   Update imports. Run make all.
```

## Documentation

```
All docs in docs/. NEVER create .md files at project root.
Only root .md files: README.md, CLAUDE.md, CHANGELOG.md.

Naming: kebab-case for all doc files (e.g. gemstone-safety.md).

docs/architecture/    → System design, layer rules, ADRs
docs/deployment/      → Server setup, CI/CD, OAuth
docs/design/          → UI design system, page specs
docs/products/        → One spec per product plugin
docs/development/     → Setup, testing, style guide
docs/vedic/           → Gemstone safety, lordship guide
```
