.PHONY: help install pip-install dev run test lint fmt fmt-check type check clean

PY ?= python
UV ?= uv

help:
	@echo "Targets:"
	@echo "  install      Install deps with uv (recommended)"
	@echo "  pip-install  Install deps with pip (fallback)"
	@echo "  dev          Run dev server with reload"
	@echo "  run          Run server (no reload)"
	@echo "  test         Run pytest"
	@echo "  lint         Run ruff lint"
	@echo "  fmt          Run ruff format"
	@echo "  fmt-check    Run ruff format --check"
	@echo "  type         Run mypy"
	@echo "  check        Lint + format check + type check + tests"
	@echo "  clean        Remove caches"

install:
	@$(UV) sync --dev

pip-install:
	@$(PY) -m pip install -e .

dev:
	@$(PY) -m uvicorn app:app --reload

run:
	@$(PY) -m uvicorn app:app

test:
	@$(PY) -m pytest -q

lint:
	@$(PY) -m ruff check .

fmt:
	@$(PY) -m ruff format .

fmt-check:
	@$(PY) -m ruff format --check .

type:
	@$(PY) -m mypy src

check: lint fmt-check type test

clean:
	@$(PY) - <<'PY'
import shutil
from pathlib import Path

roots = [Path(".")]
names = {"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
for root in roots:
    for p in root.rglob("*"):
        if p.is_dir() and p.name in names:
            shutil.rmtree(p, ignore_errors=True)
PY
