#
# Makefile for pycologne
#

PKG = pycgnweb

.PHONY: all check run test lint format typecheck

all:
	@echo "Targets: run, test, check, lint, format, typecheck"

# Lokaler Entwicklungsserver mit Debug-Modus und Auto-Reload
# (-d schaltet beides ueber Flask ein).
run:
	uv run python -m $(PKG) -d

test:
	uv run pytest

lint:
	uv run ruff check .

# Prueft nur (wie die CI); zum Anwenden: uv run ruff format .
format:
	uv run ruff format --check .

typecheck:
	uv run mypy $(PKG)

check: lint format typecheck test
