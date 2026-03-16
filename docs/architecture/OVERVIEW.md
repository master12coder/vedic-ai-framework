# Architecture Overview

## Philosophy

The Vedic AI Framework follows **Clean Architecture + Domain-Driven Design +
Hexagonal (Ports & Adapters)** principles. The core insight: astronomical
computation is deterministic truth, while interpretation is probabilistic
opinion. The architecture enforces this distinction at the import level.

## Layer Diagram

```
┌─────────────────────────────────────────────────────┐
│                    deliver/                          │  Layer 5: Output
│       (PDF, Markdown, JSON, Telegram)               │  Adapters
├─────────────────────────────────────────────────────┤
│                   interpret/                         │  Layer 3: LLM
│     (Prompt templates, LLM backends, validation)    │  Interpretation
├────────────────────┬────────────────────────────────┤
│    knowledge/      │         learn/                  │  Layer 2: Rules
│  (YAML rules,      │  (Pandit Ji corrections,       │  Layer 4: Learning
│   scripture DB)    │   6-layer validation)           │
├────────────────────┴────────────────────────────────┤
│                    compute/                          │  Layer 1: Computation
│     (Swiss Ephemeris, Dasha, Yoga, Dosha)           │  DETERMINISTIC
├─────────────────────────────────────────────────────┤
│                    domain/                           │  Foundation
│   (Models, Constants, Rules, Exceptions)            │  Shared kernel
└─────────────────────────────────────────────────────┘
```

## One-Way Dependency Rule

Dependencies flow **inward and downward only**:

```
deliver/ → interpret/ → compute/ → domain/
                ↓            ↓
           knowledge/    domain/
                ↓
             learn/
```

**Import Rules:**

| Module        | Can Import From                              | NEVER Imports         |
|---------------|----------------------------------------------|-----------------------|
| `domain/`     | Python stdlib only                           | Any jyotish module    |
| `compute/`    | `domain/`                                    | `interpret/`, `learn/`, `deliver/` |
| `knowledge/`  | `domain/` (YAML files, no Python imports)    | `compute/`, `interpret/` |
| `interpret/`  | `compute/`, `domain/`, `knowledge/`, `learn/`, `scriptures/` | `deliver/` |
| `learn/`      | `domain/`, `scriptures/`                     | `compute/`, `interpret/`, `deliver/` |
| `deliver/`    | `compute/`, `interpret/`, `domain/`          | `learn/`, `knowledge/` direct |
| `cli.py`      | All layers (orchestrator)                    | —                     |

## Data Flow

```
User Input (name, DOB, TOB, place)
  │
  ▼
compute_chart() ──────────────────► ChartData (immutable dataclass)
  │                                    │
  │                                    ├── planets: dict[str, PlanetData]
  │                                    ├── lagna_sign, yogas, doshas
  │                                    └── dasha periods, strengths
  │
  ▼
_build_chart_context() ───────────► Context dict (enriched)
  │  Loads:                            │
  │  ├── lordship_rules.yaml           ├── lordship classification
  │  ├── gemstone_logic.yaml           ├── prohibited/recommended stones
  │  ├── scripture_db                  ├── BPHS citations
  │  └── pandit_corrections            └── learned rules
  │
  ▼
Jinja2 renders prompt templates ──► System prompt + section prompts
  │
  ▼
LLM backend.generate() ──────────► Raw interpretation text
  │
  ▼
validate_interpretation() ────────► Safety-checked text + warnings
  │
  ▼
format_report_markdown() ────────► Final output (Markdown/PDF/JSON)
```

## Key Design Decisions

See [DECISIONS.md](DECISIONS.md) for full Architecture Decision Records.

1. **Swiss Ephemeris for computation** — astronomical accuracy is non-negotiable
2. **LLM-agnostic backends** — factory + protocol pattern, swap providers freely
3. **YAML knowledge files** — human-editable, version-controlled astrological rules
4. **Scripture citations** — every interpretation backed by classical text references
5. **6-layer Pandit validation** — corrections validated against computation, scripture, and life events
6. **Post-generation safety** — LLM output checked for dangerous gemstone errors
