# Development Setup

## Prerequisites

- Python 3.11+ (`python3 --version`)
- Git
- pip (comes with Python)

## Quick Start

```bash
# 1. Clone
git clone https://github.com/<org>/vedic-ai-framework.git
cd vedic-ai-framework

# 2. Virtual environment
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# 3. Install (dev + Ollama)
pip install -e ".[dev,ollama]"

# 4. Verify
pytest                       # 224+ tests pass
jyotish --help               # CLI works
```

## Install Options

```bash
pip install -e ".[dev]"              # Minimal: tests only, no LLM
pip install -e ".[dev,ollama]"       # Local LLM via Ollama (recommended)
pip install -e ".[dev,groq]"         # Free cloud LLM via Groq
pip install -e ".[dev,all]"          # Everything (Ollama + Groq + Claude + OpenAI + PDF + Telegram)
```

## LLM Backend Setup

### Ollama (Local, Free — Recommended)

```bash
# One-command setup
bash scripts/setup_ollama.sh

# Or manual:
brew install ollama           # macOS
ollama serve &                # start server
ollama pull qwen3:8b          # download model (~5GB)
```

### Groq (Cloud, Free Tier)

1. Get API key at https://console.groq.com
2. `export GROQ_API_KEY=gsk_...`
3. Use: `jyotish report --llm groq ...`

### Claude / OpenAI (Premium)

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Claude
export OPENAI_API_KEY=sk-...          # OpenAI
```

## Configuration

All settings in `config.yaml` at project root. Environment variables override
with `JYOTISH_` prefix:

```bash
export JYOTISH_LLM__DEFAULT_BACKEND=groq
export JYOTISH_OUTPUT__LANGUAGE=hindi
```

## Development Commands

```bash
make help          # show all available commands
make test          # run full test suite
make lint          # run ruff linter
make typecheck     # run mypy
make format        # auto-format with ruff
make audit         # architecture audit
make safety-check  # gemstone safety audit
make check-all     # run everything (CI equivalent)
```

## Project Structure

```
jyotish/
├── compute/     # Layer 1: Swiss Ephemeris computation (deterministic)
├── domain/      # Foundation: models, constants, rules, exceptions
├── knowledge/   # Layer 2: YAML astrological rules (human-editable)
├── interpret/   # Layer 3: LLM prompts, backends, validation
├── learn/       # Layer 4: Pandit Ji correction system
├── deliver/     # Layer 5: Output formatting (MD/JSON/PDF/Telegram)
├── scriptures/  # Sacred text database (BPHS)
├── config/      # Configuration module
├── utils/       # Utilities (datetime, geo, logging)
└── cli.py       # CLI entry point
```

## Quick Verification

```bash
# Compute a chart (no LLM needed)
jyotish chart --name "Test" --dob "15/08/1990" --tob "06:30" --place "Jaipur" --gender Male

# Generate full report with LLM
jyotish report --name "Test" --dob "15/08/1990" --tob "06:30" --place "Jaipur" --gender Male --llm groq
```
