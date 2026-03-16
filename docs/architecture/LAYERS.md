# Layer Responsibilities and Import Rules

## Layer 1: `compute/` — Deterministic Computation

**Responsibility:** Swiss Ephemeris calculations, dasha computation, yoga/dosha
detection, strength analysis, divisional charts, transit overlay.

**Rules:**
- NEVER uses LLM for any calculation
- Positions are computed to arc-second precision via pyswisseph
- All functions are pure: same input always produces same output
- Returns domain model dataclasses (ChartData, PlanetData, etc.)

**Can import:** `domain/` only
**Files:** `chart.py`, `dasha.py`, `yoga.py`, `dosha.py`, `strength.py`,
`divisional.py`, `transit.py`, `ashtakavarga.py`, `bhava_chalit.py`, `kp.py`,
`matching.py`, `muhurta.py`, `panchang.py`, `upagraha.py`

---

## Layer 2: `knowledge/` — YAML Rules (no Python code)

**Responsibility:** Store astrological rules as human-editable YAML. These files
are the single source of truth for lordship, gemstones, yogas, doshas,
nakshatras, remedies, and weekly routines.

**Rules:**
- YAML only — no Python modules in this directory
- Loaded at runtime by `interpret/` and `domain/rules/`
- Version-controlled — diffs show exactly what changed
- Editable by Jyotish scholars without programming knowledge

**Files:** `lordship_rules.yaml`, `gemstone_logic.yaml`, `yoga_definitions.yaml`,
`dosha_definitions.yaml`, `nakshatra_data.yaml`, `remedy_rules.yaml`,
`aspects.yaml`, `combustion.yaml`, `dignity.yaml`, `weekly_routine.yaml`

---

## Layer 3: `interpret/` — LLM Interpretation

**Responsibility:** Build prompt context from chart data + knowledge files,
render Jinja2 templates, call LLM backends, validate output.

**Rules:**
- Loads ALL knowledge (lordship, gemstones, scripture, pandit rules) BEFORE
  every LLM call
- Every prompt template includes mandatory rules section for the specific lagna
- Post-generation validation checks every response for safety errors
- LLM backend is selected via factory pattern — never hardcoded

**Can import:** `compute/`, `domain/`, `knowledge/` (YAML loading),
`scriptures/`, `learn/`
**Files:** `interpreter.py`, `llm_backend.py`, `formatter.py`, `prompts/*.md`

---

## Layer 4: `learn/` — Pandit Ji Learning System

**Responsibility:** Accept, validate, store, and apply corrections from human
astrologers. 6-layer validation pipeline ensures corrections are evidence-based.

**Rules:**
- Corrections NEVER override computed positions (Layer 1 absolute)
- Validated corrections become "learned rules" injected into prompts
- Trust scoring tracks per-pandit accuracy over time
- Life event correlation provides strongest validation evidence

**Can import:** `domain/`, `scriptures/`
**Files:** `corrections.py`, `validator.py`, `rule_extractor.py`,
`trust_scorer.py`, `life_events_db.py`, `prediction_tracker.py`,
`audio_processor.py`

---

## Layer 5: `deliver/` — Output Formatting

**Responsibility:** Format interpretation results for different output channels:
Markdown, JSON, PDF, Telegram.

**Rules:**
- Pure formatting — no business logic, no computation, no LLM calls
- Receives already-validated data from interpret layer
- Each output format is a separate module

**Can import:** `compute/`, `interpret/`, `domain/`
**Files:** `markdown_report.py`, `json_export.py`, `pdf_report.py`,
`telegram_bot.py`

---

## Foundation: `domain/` — Shared Kernel

**Responsibility:** Data models (dataclasses), constants, business rules,
custom exceptions. Shared by all layers.

**Rules:**
- NEVER imports from any other jyotish module
- All data structures are immutable dataclasses
- Constants centralized here — not scattered in code
- Custom exceptions for domain-specific errors

**Can import:** Python stdlib only
**Submodules:**
- `models/` — ChartData, PlanetData, DashaPeriod, Yoga, Dosha, etc.
- `constants/` — signs, planets, houses, nakshatras, dashas, dignity
- `rules/` — lordship calculation, gemstone advisor logic
- `exceptions.py` — custom exception types

---

## `scriptures/` — Sacred Text Database

**Responsibility:** Load and query classical Vedic astrology text references
(BPHS chapters as structured YAML).

**Can import:** `domain/`
**Files:** `scripture_db.py`, `bphs/*.yaml`

---

## `cli.py` — Command-Line Orchestrator

**Responsibility:** Wire all layers together via Click commands. The only module
that imports from all layers.

**Can import:** All layers (this is the composition root)

---

## Import Violation Examples

```python
# VIOLATION: compute/ importing from interpret/
# jyotish/compute/chart.py
from jyotish.interpret.llm_backend import get_backend  # NEVER

# VIOLATION: domain/ importing from compute/
# jyotish/domain/models/chart.py
from jyotish.compute.dasha import compute_mahadashas  # NEVER

# CORRECT: interpret/ importing from compute/
# jyotish/interpret/interpreter.py
from jyotish.compute.chart import ChartData  # OK — inward dependency
```
