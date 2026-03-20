# Architecture Decision Records (ADRs)

## ADR-001: Swiss Ephemeris for Planetary Computation

**Status:** Accepted
**Date:** 2025-01-15

### Context
Vedic astrology requires precise planetary positions (longitude to arc-second
accuracy). Approximations or LLM-generated positions would produce incorrect
charts with cascading interpretation errors.

### Decision
Use `pyswisseph` (Python binding for Swiss Ephemeris) for all planetary position
calculations. Computation layer (`compute/`) is deterministic and LOCKED — no
LLM, no approximation, no override.

### Consequences
- Positions are astronomically accurate to arc-second precision
- `compute/` has zero LLM dependency — runs offline, instant
- Pandit Ji corrections (Layer 4) can NEVER override computed positions
- 6-layer validation auto-rejects corrections that contradict computation

---

## ADR-002: LLM-Agnostic Backend Architecture

**Status:** Accepted
**Date:** 2025-01-15

### Context
The LLM landscape changes rapidly. Users need flexibility: free local (Ollama),
free cloud (Groq), premium (Claude/OpenAI). Lock-in to any single provider is
unacceptable.

### Decision
Use **Factory + Protocol** pattern. `LLMBackend` is a Python `Protocol` with a
`generate(system_prompt, user_prompt) -> str` method. `get_backend(name)` factory
returns the appropriate implementation. New backends added by implementing the
protocol — zero changes to interpretation code.

### Consequences
- Swapping LLM providers is a one-line config change
- Tests use `NoLLMBackend` (returns prompt as-is) — no API calls needed
- Each backend handles its own API key management, model selection, token limits
- Interpretation logic is completely decoupled from LLM transport

---

## ADR-003: YAML Knowledge Files as Source of Truth

**Status:** Accepted
**Date:** 2025-02-01

### Context
Astrological rules (lordship, yogas, doshas, gemstones) must be:
- Human-readable and editable by Jyotish scholars
- Version-controlled with clear diffs
- Loadable at runtime without code changes
- Reviewable by non-programmers

### Decision
All astrological rules are stored as YAML files in `jyotish/knowledge/`. These
files are the single source of truth. Python code loads and applies them but
never hardcodes astrological constants.

### Consequences
- `lordship_rules.yaml` (1800+ lines) covers all 12 lagnas with complete data
- Jyotish scholars can review and correct rules via YAML PRs
- `gemstone_logic.yaml` centralizes contraindications and wearing protocols
- Runtime behavior changes by editing YAML — no code deployment needed
- YAML is injected into LLM prompts via Jinja2 templates

---

## ADR-004: Scripture Citations in Interpretation

**Status:** Accepted
**Date:** 2025-03-01

### Context
LLMs tend to produce generic astrology if not grounded in specific texts. Vedic
astrology has authoritative classical texts (BPHS, Brihat Jataka, Phaladeepika)
that provide verse-level rules for planetary effects.

### Decision
Build a scripture database (`scriptures/bphs/`) with structured YAML rules
linked to specific books, chapters, and verses. Query relevant citations for
each planet-house combination and inject them into LLM prompts.

### Consequences
- Interpretations cite specific sources: "BPHS 19:8 — Saturn in 7th delays marriage"
- Scripture validation layer can check pandit corrections against classical texts
- Users can trace any interpretation back to its textual authority
- Expandable: new books/chapters added as YAML files without code changes

---

## ADR-005: 6-Layer Pandit Validation Pipeline

**Status:** Accepted
**Date:** 2025-03-10

### Context
A single pandit's opinion is not ground truth. Corrections must be validated
against multiple evidence sources before being incorporated into the system's
knowledge.

### Decision
Implement a 6-layer validation pipeline:

1. **Astronomical Fact Check** — auto-reject if contradicts Swiss Ephemeris
2. **Scripture Cross-Reference** — flag if contradicts BPHS/classical texts
3. **Life Event Validation** — strongest evidence: does real life confirm?
4. **Multi-Source Consensus** — require agreement from multiple pandits
5. **Source Trust Scoring** — per-pandit accuracy tracking
6. **Fact vs Interpretation** — corrections override interpretations only, never computation

### Consequences
- System learns over time but never accepts unvalidated corrections
- Computation is permanently locked (Layer 1 is absolute)
- High-confidence corrections become "learned rules" injected into prompts
- Trust scores create accountability for correction sources

---

## ADR-006: Post-Generation Safety Validation

**Status:** Accepted
**Date:** 2025-03-15

### Context
LLMs can hallucinate dangerous recommendations even when given correct rules in
the prompt. For gemstone recommendations specifically, recommending a maraka
planet's stone can cause real-world harm to users who follow the advice.

### Decision
Every LLM-generated interpretation passes through `validate_interpretation()`
before being shown to the user. This function checks:
- Prohibited stones recommended in positive context
- Maraka planets called "benefic" or "auspicious"
- Worship/strengthening recommended for maraka planets

Flagged content gets safety warning blocks appended.

### Consequences
- Defense-in-depth: prompt injection + post-validation = two safety layers
- Users see explicit warnings if LLM output contradicts lordship rules
- Validation errors are logged for monitoring LLM accuracy over time
- False positives (correct text flagged) are acceptable — safety over convenience
