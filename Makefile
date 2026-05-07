#
# Makefile for pycologne
#

PKG = pycgnweb
CSSFILES = pycologne.css
STATICDIR = static
LESSDIR = $(STATICDIR)/less
CSSDIR = $(STATICDIR)/css

.PHONY: all check less run test lint typecheck

all:
	@echo "Targets: run, test, check, lint, typecheck, less"

%.css: $(LESSDIR)/%.less
	lessc $< > $(CSSDIR)/$@

less: $(CSSFILES)

# Lokaler Entwicklungsserver mit Debug-Modus und Auto-Reload
# (-d schaltet beides ueber Flask ein).
run:
	uv run python -m $(PKG) -d

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy $(PKG)

check: lint typecheck test
