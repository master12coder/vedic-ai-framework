.PHONY: help install test test-safety lint typecheck format audit safety-check clean

PYTHON ?= python3

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install: ## Install package with dev + ollama extras
	$(PYTHON) -m pip install -e ".[dev,ollama]"

install-all: ## Install with all optional backends
	$(PYTHON) -m pip install -e ".[dev,all]"

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run full test suite
	$(PYTHON) -m pytest tests/ -q

test-v: ## Run tests with verbose output
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ --cov=jyotish --cov-report=term-missing

test-safety: ## Run gemstone and interpretation safety tests only
	$(PYTHON) -m pytest tests/ -q -k "safety or gemstone or maraka or prohibited"

test-fast: ## Run unit tests only (skip integration)
	$(PYTHON) -m pytest tests/ -q --ignore=tests/integration/

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Run ruff linter
	$(PYTHON) -m ruff check jyotish/ tests/ scripts/

lint-fix: ## Run ruff linter with auto-fix
	$(PYTHON) -m ruff check --fix jyotish/ tests/ scripts/

typecheck: ## Run mypy type checker
	$(PYTHON) -m mypy jyotish/ --ignore-missing-imports

format: ## Format code with ruff
	$(PYTHON) -m ruff format jyotish/ tests/ scripts/

format-check: ## Check formatting without modifying
	$(PYTHON) -m ruff format --check jyotish/ tests/ scripts/

# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------

audit: ## Run architecture audit
	$(PYTHON) scripts/architecture_audit.py

safety-check: ## Run gemstone safety audit
	$(PYTHON) scripts/gemstone_safety_audit.py

audit-all: audit safety-check ## Run all audit scripts

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

report: ## Generate sample report (Manish chart, no LLM)
	$(PYTHON) -m jyotish.cli report --name "Manish Chaurasia" --dob "13/03/1989" --tob "12:17" --place "Varanasi" --gender Male

report-llm: ## Generate sample report with Groq LLM
	$(PYTHON) -m jyotish.cli report --name "Manish Chaurasia" --dob "13/03/1989" --tob "12:17" --place "Varanasi" --gender Male --llm groq

chart: ## Compute chart only (no interpretation)
	$(PYTHON) -m jyotish.cli chart --name "Manish Chaurasia" --dob "13/03/1989" --tob "12:17" --place "Varanasi" --gender Male

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

check-all: lint typecheck test audit-all ## Run all checks (CI equivalent)
