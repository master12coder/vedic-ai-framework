# Vedic AI Framework — Engineering Bible

## Quick Start

```bash
pip install -e ".[dev,ollama]"   # install for development
pytest                           # run all tests (224+)
make check-all                   # lint + typecheck + test + audit
jyotish --help                   # CLI help
```

---

## 1. Architecture

**Clean Architecture + Domain-Driven Design + Hexagonal (Ports & Adapters)**

Core principle: astronomical computation is deterministic truth; interpretation
is probabilistic opinion. The architecture enforces this at the import level.

### Layer Diagram

```
┌──────────────────────────────────────────────────────┐
│                     deliver/                         │  Layer 5: Output adapters
│        (Markdown, JSON, PDF, Telegram)               │
├──────────────────────────────────────────────────────┤
│                    interpret/                         │  Layer 3: LLM interpretation
│    (Jinja2 prompts, LLM backends, validation)        │
├───────────────────┬──────────────────────────────────┤
│    knowledge/     │          learn/                   │  L2: YAML rules
│   (YAML rules,    │   (Pandit corrections,           │  L4: Learning
│    scriptures)    │    6-layer validation)            │
├───────────────────┴──────────────────────────────────┤
│                    compute/                           │  Layer 1: DETERMINISTIC
│      (Swiss Ephemeris, Dasha, Yoga, Dosha)           │  (LOCKED — no LLM)
├──────────────────────────────────────────────────────┤
│                     domain/                          │  Foundation: shared kernel
│     (Models, Constants, Rules, Exceptions)            │
└──────────────────────────────────────────────────────┘
```

### Import Rules (one-way dependencies)

| Module       | Can Import From                                             | NEVER Imports              |
|--------------|-------------------------------------------------------------|----------------------------|
| `domain/`    | Python stdlib only                                          | Any `jyotish.*`            |
| `compute/`   | `domain/`                                                   | `interpret/`, `learn/`, `deliver/` |
| `knowledge/` | YAML only — no Python modules                               | Everything                 |
| `scriptures/`| `domain/`                                                   | `compute/`, `interpret/`   |
| `learn/`     | `domain/`, `scriptures/`                                    | `compute/`, `interpret/`, `deliver/` |
| `interpret/` | `compute/`, `domain/`, `knowledge/`, `scriptures/`, `learn/`| `deliver/`                 |
| `deliver/`   | `compute/`, `interpret/`, `domain/`                         | `learn/`, `knowledge/`     |
| `cli.py`     | All (composition root)                                      | —                          |

### Design Patterns

| Pattern           | Where Used                                    | Purpose                                |
|-------------------|-----------------------------------------------|----------------------------------------|
| **Factory**       | `get_backend("ollama")` in `llm_backend.py`   | LLM provider selection at runtime      |
| **Strategy**      | `LLMBackend` implementations                  | Interchangeable LLM providers          |
| **Protocol**      | `LLMBackend` protocol in `llm_backend.py`     | Structural typing for backends         |
| **Repository**    | `PanditCorrectionStore` in `corrections.py`   | File-based persistence abstraction     |
| **Builder**       | `_build_chart_context()` in `interpreter.py`  | Incremental context assembly           |
| **Pipeline**      | 6-layer validation in `validator.py`          | Sequential validation with early exit  |
| **Template Method**| Jinja2 `.md` prompts rendered with context   | Prompt structure with variable injection|

---

## 2. Commands

```bash
# Development
make test              # full test suite
make test-safety       # gemstone safety tests only
make lint              # ruff linter
make typecheck         # mypy type checker
make format            # auto-format with ruff
make audit             # architecture audit (file sizes, imports, magic numbers)
make safety-check      # gemstone safety audit
make check-all         # everything (CI equivalent)

# CLI
jyotish chart    --name "..." --dob "DD/MM/YYYY" --tob "HH:MM" --place "..." --gender Male
jyotish report   --name "..." --dob "..." --tob "..." --place "..." --gender Male --llm groq
jyotish transit  --name "..." --dob "..." --tob "..." --place "..." --gender Male
jyotish daily    --name "..." --dob "..." --tob "..." --place "..." --gender Male --llm ollama
jyotish match    --name1 "..." --dob1 "..." --name2 "..." --dob2 "..."
jyotish correct  --chart "..." --category "gemstone" --what "..." --reasoning "..."
```

---

## 3. Python Standards

| Standard | What                       | Enforced By      |
|----------|----------------------------|------------------|
| PEP 8    | Code style                 | `ruff check`     |
| PEP 257  | Docstring conventions      | `ruff check`     |
| PEP 484  | Type hints                 | `mypy`           |
| PEP 621  | pyproject.toml metadata    | Manual review    |

- **Formatter:** ruff format (Black-compatible), 100-char line length
- **Import sorting:** ruff (isort-compatible)
- **Docstrings:** Google-style, required on all public functions/classes
- **Type hints:** mandatory on all function signatures, use `X | None` not `Optional[X]`

---

## 4. Coding Rules

### Hard Rules (enforced by CI / audit)

1. **300-line max** per file — extract if growing beyond
2. **Type hints** on every function signature — no untyped public functions
3. **Dataclasses only** — no raw `dict` for domain data
4. **No magic numbers** — constants in `domain/constants/` or `knowledge/*.yaml`
5. **Custom exceptions** — from `domain/exceptions.py`, not bare `Exception`
6. **Structured logging** — via `utils/logging_config.get_logger(__name__)`
7. **Dependency injection** — backends and stores passed as arguments, not hard-imported
8. **Config via YAML** — `config.yaml` for all tunables, env vars for secrets

### Conventions

- Python 3.11+ features: `X | None`, `dict[str, Any]`, `list[str]`
- Hindi text in Devanagari script, English in plain ASCII
- Key terms in both: `"Mithuna (Gemini / मिथुन)"`
- All YAML knowledge files are the single source of truth for astrological rules
- Every prompt template is a standalone `.md` file in `interpret/prompts/`
- Swiss Ephemeris positions are NEVER approximated — always `pyswisseph`
- Pandit Ji corrections are JSON files in `data/pandit_corrections/`

---

## 5. Vedic Safety Rules

These are **non-negotiable safety constraints** for the interpretation system.

### Gemstone Contraindications

- **NEVER** recommend a maraka planet's gemstone (lords of 2nd/7th houses)
- **NEVER** recommend a functional malefic's gemstone (6th/8th/12th lords without trikona)
- **ALWAYS** recommend lagnesh stone (ascendant lord is always beneficial)
- **ALWAYS** recommend yogakaraka stone (kendra + trikona lord)
- Prohibited stones per lagna are in `knowledge/lordship_rules.yaml`
- Contraindications (enemy stones): `knowledge/gemstone_logic.yaml`
- See [docs/vedic/GEMSTONE_SAFETY.md](docs/vedic/GEMSTONE_SAFETY.md)

### Maraka Dual-Nature Rule

Maraka planets often own positive houses too. The interpretation MUST
acknowledge BOTH sides:

> "Jupiter owns 10th (career) BUT ALSO 7th (maraka). Career growth and
> health/financial risks happen SIMULTANEOUSLY."

Never call a maraka planet purely benefic or purely malefic.

### Computation Locked

Swiss Ephemeris computation (`compute/`) is deterministic and LOCKED:
- No LLM output can override computed positions
- No Pandit Ji correction can change planetary longitudes
- 6-layer validation auto-rejects computation contradictions

### 6-Layer Pandit Validation

1. **Astronomical fact check** — auto-reject if contradicts computation
2. **Scripture cross-reference** — flag if contradicts BPHS
3. **Life event validation** — real-world evidence is strongest
4. **Multi-source consensus** — single pandit is not truth
5. **Source trust scoring** — per-pandit accuracy tracking
6. **Fact vs interpretation** — corrections override interpretations only

### Post-Generation Validation

Every LLM response passes through `validate_interpretation()` which catches:
- Prohibited stone names in recommendation context
- Maraka planets called "benefic" / "auspicious"
- Worship/strengthening recommended for maraka planets

---

## 6. Interpretation Rules

### Before Every LLM Call

`interpreter.py` MUST load and inject into context:
1. `lordship_rules.yaml` — benefics, malefics, maraka, gemstones for THIS lagna
2. `gemstone_logic.yaml` — contraindications, friend/enemy groups
3. `scripture_db` — BPHS citations for each planet-house combination
4. `PanditCorrectionStore` — learned rules for this lagna

### Every Prompt Template MUST Include

Via the system prompt (`system_prompt.md`):
- `MANDATORY RULES` section with lagna-specific classification
- Recommended stones list (functional benefics)
- PROHIBITED stones list (maraka + malefic planets)
- Interpretation rules (chart-specific references, maraka dual-nature)
- Scripture citations for relevant planets

### After Every LLM Response

Run `validate_interpretation()` — append safety warnings if violations found.

---

## 7. Testing

### Test Pyramid

| Level       | Count  | Speed     | What                              |
|-------------|--------|-----------|-----------------------------------|
| Unit        | ~200   | < 1s each | Computation, models, individual modules |
| Integration | ~20    | < 2s each | Pipeline, corrections, scripture  |
| E2E         | ~5     | 5-30s     | Full report with LLM backend      |

### Naming Convention

```python
def test_<what>_<condition>_<expected>():
    """<What> should <expected> when <condition>."""
```

### Safety Test Markers

```python
@pytest.mark.safety      # Gemstone/interpretation safety
@pytest.mark.slow        # Tests >5 seconds
@pytest.mark.integration # Cross-layer tests
```

### Primary Fixture

```python
@pytest.fixture
def manish_chart() -> ChartData:
    """Reference chart: Manish Chaurasia — verified data."""
    return compute_chart(
        name="Manish Chaurasia", dob="13/03/1989", tob="12:17",
        lat=25.3176, lon=83.0067, tz_name="Asia/Kolkata", gender="Male",
    )
```

**Known values:** Lagna = Mithuna, Moon = Rohini, Jupiter = maraka,
Mercury = lagnesh, current MD = Jupiter (maraka), current AD = Mercury (lagnesh).

---

## 8. Git Conventions

### Conventional Commits

```
<type>(<scope>): <short description>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `safety`, `perf`
**Scopes:** `compute`, `interpret`, `knowledge`, `learn`, `deliver`, `cli`, `scripts`, `docs`

### Pre-Commit Checklist (13 Points)

Before every commit, verify:

1. [ ] `make lint` — no linter errors
2. [ ] `make typecheck` — no type errors
3. [ ] `make test` — all tests pass
4. [ ] No file exceeds 300 lines
5. [ ] All new functions have type hints + docstrings
6. [ ] No magic numbers — use constants
7. [ ] No raw dicts — use dataclasses
8. [ ] Import rules respected (no reverse dependencies)
9. [ ] Config in YAML / env vars, not hardcoded
10. [ ] No API keys or secrets in code
11. [ ] Hindi text in Devanagari, English in ASCII
12. [ ] Safety: gemstone recs checked against lordship rules
13. [ ] Tested with reference chart if touching interpretation

### Principal-Engineer Self-Review Checklist

For any non-trivial PR, review against these dimensions:

**Architecture:**
- [ ] Dependencies flow inward only
- [ ] No LLM calls in compute layer
- [ ] New modules placed in correct layer
- [ ] No circular imports introduced

**Code Quality:**
- [ ] Functions < 50 lines, files < 300 lines
- [ ] Single Responsibility: each function does one thing
- [ ] DRY: no duplicated logic across files
- [ ] Error paths handled with custom exceptions

**Safety:**
- [ ] Gemstone recommendations checked against lordship YAML
- [ ] Maraka acknowledged with dual-nature description
- [ ] Post-validation catches prohibited stones
- [ ] LLM prompts inject mandatory rules section

**Performance:**
- [ ] YAML / scripture data cached (not reloaded per call)
- [ ] LLM calls minimised (one per section, not per paragraph)
- [ ] No N+1 queries in scripture lookups

---

## 9. AI-Era Patterns

### Structured Knowledge → LLM

```
YAML rules (lordship, gemstones, scripture)
    ↓
Jinja2 templates (system_prompt.md, section prompts)
    ↓
LLM backend.generate(system_prompt, user_prompt)
    ↓
Post-validation (safety checks)
    ↓
Formatted output (Markdown/PDF/JSON)
```

### Factory + Protocol for LLM

```python
class LLMBackend(Protocol):
    def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str: ...
    def name(self) -> str: ...
    def is_available(self) -> bool: ...

# Swap providers with one line:
backend = get_backend("groq")   # or "ollama", "claude", "openai", "none"
```

### Observability

- Structured logging via `get_logger(__name__)` in every module
- Validation errors logged with lagna + section context
- LLM call timing can be added to backend.generate()
- `config/logging.yaml` for production log configuration

### Plugin Architecture for Extensibility

- **New LLM backend:** Implement `LLMBackend` protocol, register in factory
- **New scripture book:** Add YAML files to `scriptures/bphs/` (or new book dir)
- **New interpretation section:** Add `.md` template to `prompts/`, register in `interpret_chart()`
- **New output format:** Add module to `deliver/`
- **New dosha/yoga:** Add definition to `knowledge/*.yaml`, detection in `compute/`

---

## 10. Quick Reference — What Goes Where

| You Want To...                        | Put It In                              |
|---------------------------------------|----------------------------------------|
| Add a planetary calculation           | `compute/` (+ test in `tests/compute/`) |
| Add a yoga or dosha definition        | `knowledge/yoga_definitions.yaml` or `dosha_definitions.yaml` |
| Add a scripture rule                  | `scriptures/bphs/chapter_*.yaml`       |
| Add an LLM interpretation section     | `interpret/prompts/new_section.md`     |
| Add a new LLM provider               | `interpret/llm_backend.py` (implement protocol) |
| Add gemstone contraindication         | `knowledge/gemstone_logic.yaml`        |
| Fix lordship rule for a lagna         | `knowledge/lordship_rules.yaml`        |
| Add a Pandit Ji correction            | `jyotish correct` CLI command          |
| Add an output format                  | `deliver/` (new module)                |
| Add a constant                        | `domain/constants/` (appropriate file) |
| Add a data model                      | `domain/models/` (dataclass)           |
| Add a custom exception                | `domain/exceptions.py`                 |
| Add a CLI command                     | `cli.py` (Click command)               |

---

## 11. Key Files

| File                                | Purpose                               |
|-------------------------------------|---------------------------------------|
| `jyotish/interpret/interpreter.py`  | Orchestration: context → LLM → validation |
| `jyotish/interpret/llm_backend.py`  | Factory + Protocol for LLM providers  |
| `jyotish/interpret/prompts/system_prompt.md` | System prompt with mandatory rules |
| `jyotish/knowledge/lordship_rules.yaml` | All 12 lagnas: benefics, malefics, maraka, gemstones |
| `jyotish/knowledge/gemstone_logic.yaml` | Gemstone data, contraindications, friendships |
| `jyotish/compute/chart.py`         | Swiss Ephemeris chart computation      |
| `jyotish/domain/models/chart.py`   | ChartData / PlanetData dataclasses     |
| `jyotish/learn/validator.py`       | 6-layer Pandit validation pipeline     |
| `jyotish/scriptures/scripture_db.py`| Scripture query and citation engine    |
| `config.yaml`                       | All runtime configuration              |
| `tests/conftest.py`                 | Shared fixtures (manish_chart, sample_chart) |
