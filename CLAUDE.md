# CLAUDE.md — DaivAI Framework

> Read this FIRST every session. Follow EVERY rule. No exceptions.

## Research before coding (mandatory)

Before starting ANY task:
1. Run `nlm query "[main topic of task]" --top-k 5`
2. Read the returned chunks
3. Use that context to ground your implementation
4. If nothing relevant found, run `nlm list` to see what's indexed

Examples:
- Task about gemstones → `nlm query "gemstone safety mithuna lagna"`
- Task about dasha → `nlm query "dasha transit timing technique"`
- Task about yoga → `nlm query "yoga activation timing"`
- Task about Lal Kitab → `nlm query "lal kitab remedies rin"`
- Unsure what exists → `nlm query "[feature name]" --top-k 8`

Never start coding without querying nlm first.

## Documentation research

An auto-query hook (tools/nlm/auto-query.sh) silently injects relevant documentation context on every prompt. This is handled automatically — no action needed for most tasks.

For architecture or spec-heavy tasks, manually query for deeper context:
- `nlm query "[topic]" --top-k 5` — search indexed documentation
- `nlm query "[topic]" --doc "spec-name"` — search specific document
- `nlm list` — see all indexed documents
- `nlm stats` — check index health

Do NOT use nlm for code search — Claude Code's native codebase reading is better for that. nlm is for documentation, specs, and architecture decision records only.

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

## Engine Scope (173 compute modules as of March 2026)

```
Core: chart, dasha (5 types), divisional, divisional_extended, special_lagnas (8), upagraha
Yogas: yoga + 13 sub-modules (284 yogas: Nabhasa, Arishta, Bandhana, Daridra,
       Kemadruma, Parivartana, Neech Bhanga, Moksha, Lunar, Solar…)
       yoga_timing — maps all yogas to dasha activation periods
Matching: kootas (North Indian 36-point) + porutham (South Indian 10-point)
Dashas: Vimshottari, Narayana, Kalachakra, Mudda, Sudarshan, conditional
        dasha_transit — #1 timing technique (dasha lords + transit + BAV + double transit)
Strength: bhava_bala, ishta_kashta, vimshopaka, graha_yuddha, avasthas (2 modules)
Divisional: 16 vargas, D60 Shastyamsha, Drekkana, varga analysis (deep + models)
Jaimini: karakas, padas, rasi dashas, bhavat_bhavam, badhaka
KP: sub-lord tables, ruling planets, rectification (3 methods)
Predictive: gochara, transit (3 modules), double_transit, sav_transit, vedha,
            transit_finder (ingress/station/aspect search), eclipse_natal
Muhurta: engine + lagna + panchanga + chandrabalam, tithi_pravesh, varsha_pravesh
Medical: body mapping, disease, dosha constitution
Remedies: gem_therapy (4 modules), mantra, yantra, vastu (2 modules), lal_kitab
Prashna: prashna + helpers, Ashtamangala (2 modules)
Specialized: Pancha Pakshi, Namakarana, numerology (3 modules), sarvatobhadra,
             mundane (3 modules), saham, longevity, dispositor, nisheka, kota_chakra
Reference: chandra_kundali, surya_kundali (lordship-aware Moon/Sun chart analysis)
```

## Engine Conventions (confirmed March 2026 audit)

```
DST handling (datetime_utils.py):
  AmbiguousTimeError (fall-back) → resolve to standard time
  NonExistentTimeError (spring-forward) → shift forward 1 hour
  Supports HH:MM:SS birth time format

Ayanamsha (chart.py):
  Configurable via ayanamsha_type param (Lahiri default)
  Non-Lahiri computation MUST restore Lahiri in finally block
  Available: Lahiri, KP, Raman, and all Swiss Ephemeris types

Stationary planets (chart.py):
  Detected via STATIONARY_THRESHOLDS dict in constants/planets.py
  Per Saravali Ch.4 — threshold varies by planet

D60 Shastyamsha (divisional_extended.py):
  BPHS Ch.8 rule — odd signs count from Aries, even signs from Libra
  NOT from own sign for all signs

Hora Lagna (special_lagnas.py):
  Rate = 12 deg/ghatika (= 1 sign per 2.5 ghatikas, BPHS Ch.5)
  NOT 15 deg/ghatika

Scripture citations:
  Every computation fix MUST cite source (BPHS chapter, Saravali, etc.)
  Commit messages include the citation
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
Constants in engine/constants/ package. Organized by domain (planets.py, signs.py, etc.). Not scattered across compute modules.
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
