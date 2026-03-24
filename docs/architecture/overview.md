# Jyotish — Architecture: Layers & Packages

## One Sentence
Three packages: engine computes, products interpret, apps deliver.

## Team
- **Manish**: Tech lead. Reviews, directs, decides.
- **Claude Code**: Developer. Writes code, runs tests, commits.
- **Claude Cowork**: Maintains architecture, reviews PRs, runs audits.

## Stack (Modern Python, AI-Era)
- **Python 3.12+** — match statements, type params, f-string debugging
- **uv** — package manager + workspace linking
- **Pydantic v2** — models with validation, JSON serialization, settings
- **pyswisseph** — NASA JPL DE431 ephemeris, 0.001 deg precision
- **Jinja2** — prompt templates
- **Click** — CLI
- **FastAPI** — web API + HTML
- **python-telegram-bot** — daily companion delivery
- **matplotlib + reportlab** — charts + PDF
- **ruff** — lint + format
- **mypy** — type check
- **pytest** — test

---

## Three Packages

```
jyotish/
+-- engine/                 # pip install daivai-engine
|   +-- src/daivai_engine/
+-- products/               # pip install daivai-products
|   +-- src/daivai_products/
+-- apps/                   # pip install daivai
|   +-- src/daivai_app/
+-- docs/
+-- scripts/
+-- tests/
+-- pyproject.toml          # uv workspace root
+-- CLAUDE.md               # 40 lines. Rules only.
+-- README.md
+-- Makefile
+-- LICENSE
```

### Why 3, not 1, not 15

| Count | Problem |
|---|---|
| 1 package | 100+ files, messy imports, can't install just computation |
| 15 packages | 15 pyproject.toml files, dependency hell, solo dev overhead |
| **3 packages** | **Clean separation. Installable parts. Claude manages 3 configs easily.** |

---

## Package 1: engine/ (Pure Computation — Zero AI)

```
engine/
+-- pyproject.toml
+-- src/daivai_engine/
    +-- __init__.py              # from daivai_engine import compute_chart
    |
    +-- models/                  # Pydantic v2 models — THE contract
    |   +-- chart.py             # ChartData, PlanetPosition, HouseData
    |   +-- dasha.py             # DashaPeriod, DashaTimeline
    |   +-- yoga.py              # YogaResult, YogaStatus
    |   +-- transit.py           # TransitPosition, TransitImpact
    |   +-- panchang.py          # PanchangData, TithiInfo, HoraSlot
    |   +-- matching.py          # AshtakootResult, CompatibilityReport
    |   +-- gemstone.py          # GemstoneRec, ProhibitedStone
    |   +-- daily.py             # DailyGuidance, RemedyLevel
    |
    +-- compute/                 # Swiss Ephemeris wrappers
    |   +-- chart.py             # compute_chart() -> ChartData
    |   +-- dasha.py             # Vimshottari, Yogini, Chara
    |   +-- divisional.py        # D1-D60
    |   +-- ashtakavarga.py      # Bhinna + Sarva (total=337)
    |   +-- shadbala.py          # Six-fold strength
    |   +-- kp.py                # KP sub-lord table
    |   +-- jaimini.py           # Chara karakas
    |   +-- transit.py           # Current positions
    |   +-- panchang.py          # Tithi, nakshatra, yoga, karana
    |   +-- hora.py              # Planetary hora sequence
    |   +-- matching.py          # Ashtakoot 36-guna
    |   +-- yoga_detector.py     # 150+ yoga detection
    |
    +-- knowledge/               # YAML source of truth
    |   +-- lordship_rules.yaml  # 12 lagnas: benefic/malefic/maraka
    |   +-- gemstone_logic.yaml  # Contraindications
    |   +-- yoga_definitions.yaml # 150+ yogas
    |   +-- remedy_rules.yaml    # Mantra, daan, color, food per planet
    |   +-- lal_kitab.yaml       # Planet x house remedies
    |   +-- mantras.yaml         # Audio links per planet
    |   +-- loader.py            # YAML loading with caching
    |
    +-- scriptures/              # Classical text DB
    |   +-- bphs/                # 20+ chapter YAML files
    |   +-- query.py             # Scripture query interface
    |
    +-- constants.py             # ALL magic numbers. One file.
    +-- exceptions.py            # JyotishError hierarchy. One file.
```

**Dependencies:** pyswisseph, pyyaml, pydantic. Nothing else.
**Can be used standalone:** `pip install daivai-engine` gives anyone NASA-grade computation.
**No AI, no LLM, no network required.** Pure math + rules.

---

## Package 2: products/ (AI + Business Logic)

```
products/
+-- pyproject.toml
+-- src/daivai_products/
    +-- __init__.py
    |
    +-- interpret/               # LLM layer
    |   +-- factory.py           # get_llm("groq") -> LLMBackend
    |   +-- context.py           # Build prompt context from chart + rules
    |   +-- renderer.py          # Jinja2 prompt rendering
    |   +-- validator.py         # Post-generation safety check
    |   +-- backends/
    |   |   +-- groq.py
    |   |   +-- ollama.py
    |   |   +-- claude.py
    |   |   +-- openai.py
    |   |   +-- offline.py       # No LLM — computation only
    |   +-- prompts/             # Jinja2 templates
    |       +-- overview.md.j2
    |       +-- career.md.j2
    |       +-- gemstone.md.j2
    |       +-- ...
    |
    +-- kundali/                 # Product: Full Chart Report
    |   +-- report.py            # Text report orchestrator (18 sections)
    |   +-- pdf.py               # PDF assembler (3 formats)
    |   +-- diamond.py           # D1 North Indian chart renderer
    |   +-- divisional.py        # Reusable D9/D10/any varga renderer
    |   +-- dasha_gantt.py       # Dasha timeline Gantt chart
    |   +-- ashtakavarga_heatmap.py  # Color-coded bindu grid
    |   +-- shadbala_chart.py    # Planet strength bars
    |   +-- yoga_cards.py        # Active yoga cards
    |   +-- gemstone_card.py     # Multi-factor gemstone card
    |   +-- graha_table.py       # Planet position table
    |   +-- golden_period.py     # Best upcoming dasha highlight
    |   +-- prohibited_stones.py # Prohibited stones danger list
    |   +-- accuracy_cert.py     # Computation certificate
    |   +-- theme.py             # Sanatan Dharma colors/fonts/styles
    |
    +-- daily/                   # Product: Daily Companion
    |   +-- engine.py            # compute_daily() -> DailyGuidance
    |   +-- rating.py            # Day rating 1-10
    |   +-- levels.py            # Simple / Medium / Detailed
    |   +-- mantra.py            # Selector + audio links
    |   +-- format.py            # WhatsApp / Telegram / Terminal
    |
    +-- matching/                # Product: Compatibility
    |   +-- report.py            # Full compatibility analysis
    |   +-- muhurta_dates.py     # Best marriage dates
    |
    +-- remedies/                # Product: Remedy Planner
    |   +-- gemstone.py          # Full recommendation engine
    |   +-- weekly.py            # Day-wise routine
    |   +-- pooja.py             # Monthly calendar
    |   +-- lal_kitab.py         # Lal Kitab remedies
    |
    +-- predictions/             # Product: Accuracy Tracker
    |   +-- tracker.py           # Log, track, verify
    |   +-- accuracy.py          # Stats
    |   +-- patterns.py          # Cross-chart patterns
    |
    +-- pandit/                  # Product: Professional Tools
    |   +-- technical.py         # Pandit-formatted report
    |   +-- comparison.py        # AI vs Pandit [=][+][!=]
    |   +-- corrections.py       # 6-layer validation
    |   +-- trust.py             # Per-pandit scoring
    |
    +-- muhurta/                 # Product: Timing Finder
    |   +-- finder.py
    |   +-- rahu_kaal.py
    |
    +-- store/                   # SQLite persistence
        +-- charts.py            # Saved charts
        +-- events.py            # Life events
        +-- predictions.py       # Prediction log
```

**Dependencies:** daivai-engine, jinja2, groq/ollama/anthropic (optional), matplotlib, reportlab
**Imports engine, never the reverse.**

---

## Package 3: apps/ (Delivery — How Users Access Products)

```
apps/
+-- pyproject.toml
+-- src/daivai_app/
    +-- __init__.py
    |
    +-- cli/                     # jyotish command
    |   +-- main.py              # Click group
    |   +-- chart.py             # daivai chart ...
    |   +-- kundali.py           # daivai kundali ...
    |   +-- daily.py             # daivai daily ...
    |   +-- match.py             # jyotish match ...
    |   +-- remedies.py          # jyotish remedies ...
    |   +-- predict.py           # jyotish predict ...
    |   +-- pandit.py            # jyotish pandit ...
    |   +-- muhurta.py           # daivai muhurta ...
    |
    +-- web/                     # Browser UI
    |   +-- app.py               # FastAPI
    |   +-- routes.py            # API routes
    |   +-- templates/           # HTML (Jinja2)
    |
    +-- telegram/                # Daily companion bot
        +-- bot.py
        +-- handlers.py          # /start, /daily, /level, /mantra
```

**Dependencies:** daivai-products, click, fastapi, python-telegram-bot
**This is what users install:** `pip install daivai`

---

## Layer Rule (One Picture)

```
+--------------------------------------+
|  apps/        CLI, Web, Telegram     |  <- Users interact here
|  (Layer 3)    Format + Deliver       |
+--------------+-----------------------+
               | imports
+--------------v-----------------------+
|  products/    Kundali, Daily, Match  |  <- AI interprets here
|  (Layer 2)    Interpret + Validate   |
+--------------+-----------------------+
               | imports
+--------------v-----------------------+
|  engine/      Compute, Knowledge     |  <- Math happens here
|  (Layer 1)    Swiss Ephemeris + YAML |
+--------------------------------------+

     engine/ has ZERO dependencies on products/ or apps/
     products/ has ZERO dependencies on apps/
     apps/ depends on everything above
```
