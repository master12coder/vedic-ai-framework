# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive engineering governance: CLAUDE.md, ADRs, audit scripts, PR templates
- Architecture audit script (`scripts/architecture_audit.py`)
- Gemstone safety audit script (`scripts/gemstone_safety_audit.py`)
- Makefile with lint, typecheck, test, format, audit targets
- GitHub PR and issue templates
- Documentation: architecture overview, layer guide, ADRs, setup, testing, style guide
- Vedic safety documentation: gemstone safety guide, lordship reference

### Changed
- CLAUDE.md rewritten as comprehensive engineering bible
- pyproject.toml: added ruff, mypy, pytest tool configurations

## [0.1.0] — 2025-05-15

### Added
- Core chart computation via Swiss Ephemeris (pyswisseph)
- Vimshottari Dasha (MD/AD/PD) calculation
- 30+ Yoga detection (Panch Mahapurush, Raj, Dhan, Vipreet)
- Dosha detection (Mangal, Kaal Sarpa, Sadesati, Pitra, Kemdrum)
- Ashtakavarga strength analysis
- Bhava Chalit house activation
- Shadbala planetary strength
- KP sub-lord system
- Divisional charts (D9, D10, D7, D12)
- Upagraha computation
- Panchang (Tithi, Nakshatra, Yoga, Karana, Vara)
- Ashtakoot 36-guna compatibility matching
- Muhurta (auspicious timing) finder
- Transit overlay on natal chart
- LLM interpretation via Ollama, Groq, Claude, OpenAI backends
- Jinja2 prompt templates for 7 interpretation sections
- Scripture database (BPHS 8 chapters, 127 rules)
- 6-layer Pandit Ji validation pipeline
- Life event tracking and prediction accuracy
- Lordship rules for all 12 lagnas (1800+ lines YAML)
- Gemstone logic with contraindications
- Interpretation safety: lordship injection, prohibited stone checks, post-validation
- CLI (`jyotish`) with report, chart, transit, daily, match, muhurta commands
- 224 tests across compute, integration, scripture, and learning modules
