# DaivAI Five-Layer Architecture

## Layer Diagram

```
Layer 5: UI / Delivery
  Web App (FastAPI+Jinja2), Telegram Bot, PDF Reports, CLI
  End User View + Pandit Ji View. Responsive 390-1440px.
    ↑ reads from
Layer 4: AI Interpretation
  LLM backends (Groq free, Ollama, Claude, OpenAI)
  Prompt templates per domain. Validation: AI never contradicts computation.
    ↑ reads from
Layer 3: Decision Engine
  Chart Selector (which charts for this query)
  House Highlighter. Cross-Chart Validator (D1 vs D9).
  Confidence Scorer (0-100). Progressive input handler.
    ↑ reads from
Layer 2: Data Models
  FullChartAnalysis unified Pydantic model (v5.1, 67 fields)
  Contains ALL computed data. Single source of truth. JSON serializable.
    ↑ reads from
Layer 1: Computation Engine
  Swiss Ephemeris. 100+ compute modules. 20+ YAML knowledge files.
  18 BPHS chapters. 100% deterministic. Same input = same output.
```

## Core Rules

1. **UI never computes.** Layer 5 reads from layers below.
2. **AI never guesses positions.** Layer 4 interprets computed data only.
3. **Decisions based on computed data.** Layer 3 reads Layer 2, not Layer 1.
4. **Each layer reads ONLY from the layer below.**
5. **No layer skips another.** UI cannot call engine directly.

## Layer → Code Package Mapping

| Layer | Package | Phase |
|-------|---------|-------|
| Layer 1 | `engine/` | Phase 1 (DONE) |
| Layer 2 | `engine/models/analysis.py` + `products/` consumers | Phase 2 (DONE) |
| Layer 3 | `products/decision/` (to be created) | Phase 3 (NOT STARTED) |
| Layer 4 | `products/interpret/` | Phase 4 (PARTIAL) |
| Layer 5 | `apps/` (CLI, web, telegram) | Phase 6+ |

## Products (7 + 1 Future)

| # | Product | Route | Description |
|---|---------|-------|-------------|
| 1 | Kundali | /client/{id} | Full birth chart report, diamond charts, 3 PDF formats |
| 2 | Dasha Timeline | /client/{id}/dasha | Visual Vimshottari timeline, golden period |
| 3 | Gemstone Guide | /client/{id}/ratna | 10-factor weight, prohibited stones, alternatives |
| 4 | Daily Guidance | /client/{id}/daily | Day rating, color, mantra, transit analysis |
| 5 | Matching | /client/{id}/matching | Ashtakoot 36-guna, Mangal dosha cross-check |
| 6 | Muhurta | /client/{id}/muhurta | Auspicious date finder, calendar view |
| 7 | Pandit Dashboard | /pandit | Corrections, validation, trust scoring |
| 8 | Financial Timing | (future) | Dasha financial rating, investment windows |

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| Ephemeris | Swiss Ephemeris (NASA JPL DE431) |
| Ayanamsha | Lahiri (default), configurable |
| Web | FastAPI + Jinja2 (server-rendered) |
| Database | SQLite (MVP), PostgreSQL-ready |
| AI/LLM | Groq free (default), Ollama, Claude, OpenAI |
| PDF | WeasyPrint (primary), ReportLab (fallback) |
| Tests | pytest, 3643+ passing |
| Deployment | Oracle Cloud Free Tier |
