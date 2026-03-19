.PHONY: help install test lint typecheck format audit all clean run backup backup-gdrive backup-setup

PYTHON ?= python3
UV ?= uv

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install: ## Install all packages in dev mode with uv
	$(UV) sync

install-pip: ## Install with pip (fallback)
	$(PYTHON) -m pip install -e engine/ -e products/ -e "apps/[all]"
	$(PYTHON) -m pip install pytest ruff mypy

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run full test suite
	$(PYTHON) -m pytest tests/ -v --tb=short

test-q: ## Run tests quietly
	$(PYTHON) -m pytest tests/ -q

test-safety: ## Run safety tests only
	$(PYTHON) -m pytest tests/ -q -k "safety or gemstone or maraka or prohibited"

# ---------------------------------------------------------------------------
# Code Quality
# ---------------------------------------------------------------------------

lint: ## Run ruff linter + format check
	$(PYTHON) -m ruff check engine/src/ products/src/ apps/src/ tests/ scripts/
	$(PYTHON) -m ruff format --check engine/src/ products/src/ apps/src/

lint-fix: ## Auto-fix lint issues
	$(PYTHON) -m ruff check --fix engine/src/ products/src/ apps/src/ tests/ scripts/
	$(PYTHON) -m ruff format engine/src/ products/src/ apps/src/

typecheck: ## Run mypy type checker
	$(PYTHON) -m mypy engine/src/ products/src/ apps/src/ --ignore-missing-imports

# ---------------------------------------------------------------------------
# Audits
# ---------------------------------------------------------------------------

audit: ## Run all audit scripts
	$(PYTHON) scripts/check_imports.py
	$(PYTHON) scripts/check_plugins.py
	$(PYTHON) scripts/safety_audit.py

# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------

all: lint typecheck test audit ## Run everything (CI equivalent)

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

run: ## Show CLI help
	$(PYTHON) -m daivai_app.cli.main --help

chart: ## Compute Manish's chart
	$(PYTHON) -m daivai_app.cli.main chart --name "Manish Chaurasia" --dob "13/03/1989" --tob "12:17" --place "Varanasi" --gender Male

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

backup: ## Backup local data (database, charts, .env)
	bash scripts/backup/local_backup.sh

backup-gdrive: ## Backup + upload to Google Drive
	bash scripts/backup/auto_backup.sh

backup-setup: ## One-time: configure Google Drive sync
	bash scripts/backup/setup_gdrive_sync.sh

# ---------------------------------------------------------------------------
# Maintenance
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
