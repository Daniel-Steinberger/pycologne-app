#
# Makefile for pycologne
#

PKG = pycgnweb

# Termine, Protokolle und Bilder liegen in einem eigenen Repo, das
# standardmaessig als Schwester-Verzeichnis erwartet wird. Anderer Ort:
# make run CONTENT=/pfad/zum/checkout
CONTENT ?= ../pycologne-content
CONTENT_REPO = https://github.com/Daniel-Steinberger/pycologne-content

.PHONY: all check run test lint format typecheck audit content

all:
	@echo "Targets: run, content, test, check, lint, format, typecheck, audit"

# Verlinkt die Inhalte in den Arbeitsbaum, genau wie es das Setup-Script auf
# dem Server im State-Verzeichnis tut. Fehlt der Checkout, wird er daneben
# geklont. Beide Symlinks stehen in der .gitignore.
content:
	@test -d "$(CONTENT)" || git clone $(CONTENT_REPO) "$(CONTENT)"
	@for pair in templates/md:md static/images:images; do \
		link="$${pair%%:*}"; \
		if [ -e "$$link" ] && [ ! -L "$$link" ]; then \
			echo "FEHLER: $$link ist kein Symlink, sondern liegt echt im Arbeitsbaum."; \
			echo "        Inhalte gehoeren ins Content-Repo, s. README."; \
			exit 1; \
		fi; \
		ln -sfn "$(abspath $(CONTENT))/$${pair#*:}" "$$link"; \
	done
	@echo "Inhalte verlinkt nach $(abspath $(CONTENT))"

# Lokaler Entwicklungsserver mit Debug-Modus und Auto-Reload
# (-d schaltet beides ueber Flask ein).
run: content
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

# Security-Audit der Abhaengigkeiten (wie in der CI); braucht Netzwerk.
audit:
	uvx pip-audit

check: lint format typecheck test audit
