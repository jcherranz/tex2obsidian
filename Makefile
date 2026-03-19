PYTHON := .venv/bin/python
PIP := .venv/bin/pip
PYTEST := .venv/bin/pytest

.PHONY: help setup test test-full check convert clean

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup: ## Create venv, install editable with dev deps
	python3 -m venv .venv
	$(PIP) install -e ".[dev]"

test: ## Run pytest (skip pandoc tests if not installed)
	$(PYTEST) -m "not pandoc"

test-full: ## Run all tests including pandoc integration
	$(PYTEST)

check: ## Run tex2obsidian check
	$(PYTHON) -m tex2obsidian check

convert: ## Run tex2obsidian convert (all files)
	$(PYTHON) -m tex2obsidian convert

clean: ## Remove caches and build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
