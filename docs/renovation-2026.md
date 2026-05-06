# Renovierung PyCologne-App

## Context

Die PyCologne-App ist eine kleine Flask-Webseite (Vereinsseite, ReST→HTML, ~6
Python-Module, 2 Tests). Sie war seit 2018 quasi inaktiv, wurde Anfang 2024 von
Mercurial/Bitbucket nach Git migriert und einmalig auf Flask 3 / Poetry
gehoben. Heute ist 2026-05 — Dependencies sind ~2 Jahre alt, mehrere
Migrations-Reste sind noch da (.hgignore, README mit `hg clone`-Anleitung,
setup.py parallel zu pyproject.toml, `tox.ini` mit `envlist = py27`,
BITBUCKET_URL im Code), die AUTHORS-Datei listet nur 4 von 11+ Beitragenden, es
gibt keine CI/Security-Automation, und `webapp.py` importiert ein nicht
deklariertes, ungewartetes Paket (`flipflop`).

Ziel: Renovierung in 5 Phasen / 5 PRs, ohne fachliche Funktionsänderung. Jede
Phase eigenständig mergebar.

## Geklärte Entscheidungen

- Repo-URL: `https://github.com/Daniel-Steinberger/pycologne-app`
- flipflop / FastCGI: **komplett entfernen**
- E2E-Tests: **Selenium → Playwright** (mit `pytest-playwright`)
- Linter: **flake8 + pyflakes → ruff** (pylint bleibt optional)
- Package-Manager: **Poetry → uv** (Astral, gleiches Ökosystem wie ruff)
- **Type-Hints durchgängig** in `pycgnweb/` und `_tests/`, mit `mypy` im CI

## Branch & Commit-Konvention

- Alle Arbeiten auf Branch **`renovate-pycologne-app-2026`** (von `main`
  abgezweigt).
- Commit-Sprache: Deutsch (passt zur bestehenden History).

---

## Phase 1 — Repo-Hygiene & Metadaten (eine PR, mehrere Commits)

Risiko: trivial. Keine Code-Änderung an Laufzeitverhalten.

**1.1 .hgignore → .gitignore**
- Alte Mercurial-Reste (`pyhasse.similarity/*`, `oldies`, `level/Level*`,
  `*.aux`, `*.synctex.gz`, `*.out`, `sphinxdocs`, `modules1`, `dummy*`,
  `_build`, `static/js/prettify*`) prüfen — die meisten sind heute irrelevant.
- Standardmäßiges Python-`.gitignore` als Basis nehmen + Editor-Spezifika
  (`.idea`, `*.swp`, `.DS_Store`, `*~`) + uv/venv-Spezifika (`.venv/`,
  `__pycache__/`, `*.egg-info/`, `dist/`, `build/`, `.pytest_cache/`,
  `.ruff_cache/`, `.mypy_cache/`).
- `.hgignore` löschen.

**1.2 AUTHORS aus Git-Shortlog regenerieren**
- Quelle: `git shortlog -sne --all` — alphabetisch sortieren.
- Ergänzen: Chris Arndt (SpotlightKid), Rebecca Breu, Christian Geier, Kay
  Thust, Daniel Steinberger, Thomas Koch, Jan Leendertse.
- Header: "Beitragende zur PyCologne-Webseite. Siehe `git log` für
  vollständige Historie."

**1.3 pyproject.toml: Migration Poetry → uv (PEP 621)**
- `[tool.poetry]` → standardkonformes `[project]`:
  - `name`, `version`, `description`, `requires-python = ">=3.11"`,
  - `authors = [{name = "PyCologne", email = "webteam@pycologne.de"}]`,
  - `maintainers = [{name = "Daniel Steinberger", email = "daniel.steinberger@dvs.ag"}]`,
  - `license = {text = "GPL-3.0-or-later"}`,
  - `readme = "README.md"`,
  - `dependencies = [...]` als PEP-508-Strings statt Caret-Ranges,
  - `urls = {Repository = ".../pycologne-app", Homepage = "https://www.pycologne.de"}`.
- `[dependency-groups]` mit `dev = [...]` (uv-natives Format).
- `[build-system]` auf `hatchling` umstellen.
- `poetry.lock` löschen, `uv lock` regeneriert `uv.lock`.

**1.4 README → Markdown neu schreiben**
- Alte `README.rst` löschen, neue `README.md` mit Quickstart `git clone …`,
  `uv sync`, `uv run python -m pycgnweb`, `make less`, `uv run pytest`,
  Projektstruktur, Lizenz/AUTHORS-Verweis, Trust-Boundary-Hinweis.
- Hinweis auf uv-Installation.

**1.5 setup.py löschen, Console-Script in pyproject.toml**
- `setup.py` löschen.
- `[project.scripts] pycologne-webapp = "pycgnweb.webapp:main"`.
- Smoke-Test: `uv sync && uv run pycologne-webapp --help` muss laufen.

**1.6 tox.ini löschen**
- `envlist = py27` ist obsolet. Make + uv + GitHub Actions (Phase 3) decken
  alles ab.

**1.7 BITBUCKET_URL → REPO_URL**
- `pycgnweb/config.py`: Konstante umbenennen, Wert auf
  `https://github.com/Daniel-Steinberger/pycologne-app`.
- `pycgnweb/webapp.py`: Import + `get_urls()`-Key umbenennen
  (`'bitbucket'` → `'repo'`).
- Templates prüfen, `urls['bitbucket']` durch `urls['repo']` ersetzen.

**1.8 Makefile aufräumen**
- `flake` und `pylint`-Targets entfernen, `check`-Target auf
  `uv run ruff check && uv run pytest` umstellen. `run` und `run-debug`
  auf `uv run python -m pycgnweb …`.

**1.9 Renovierungsplan im Repo ablegen**
- Neu: `docs/renovation-2026.md`. Diese Datei.

---

## Phase 2 — Dependencies (eine PR, getrennte Commits)

Risiko: mittel. Ein Smoke-Test pro Commit.

**2.1 Verifizierte Befunde**
- `pytz`: nicht im Code verwendet → entfernen (Python 3.11+ hat `zoneinfo`).
- `six`: nicht im Code verwendet → entfernen.
- `python-dateutil`: in `pycgnweb/events.py` (`rrule`) verwendet → bleibt.
- `flipflop`: einziger Import in `pycgnweb/webapp.py` (FastCGI-Pfad) → wird
  mit dem FastCGI-Block entfernt.

**2.2 Änderungen**
- `pyproject.toml`:
  - `dependencies`: pytz, six raus. flask, docutils, babel, python-dateutil
    auf aktuelle Untergrenzen (`>=3.0`, `>=0.21`, `>=2.16`, `>=2.9`).
  - `[dependency-groups] dev`: `pytest>=8`, `pylint>=3.3`, `ruff>=0.6`,
    `mypy>=1.11`, `pytest-playwright>=0.5`. selenium, flake8-docstrings,
    pyflakes, flask-testing raus.
- `uv lock`, `uv sync`, `uv run pytest`, manueller Smoke-Test.

**2.3 flipflop / FastCGI-Block entfernen**
- `pycgnweb/webapp.py`: `--wsgi`-Argument und `if args.wsgi: from flipflop
  import …`-Block löschen. `main` rein als Development-Server-Starter.
- README aktualisieren (kein FastCGI-Deploy mehr; Hinweis auf
  waitress/gunicorn als Optionen für Production).

---

## Phase 3 — Security, CI, Linter-Migration (eine PR)

Risiko: niedrig (additiv).

**3.1 Migration auf ruff**
- `[tool.ruff]`-Section in `pyproject.toml` (target-version py311,
  line-length 100, `select = ["E", "F", "W", "I", "B", "UP", "S"]`).
- `flake8-docstrings`, `pyflakes` aus Dev-Deps entfernen (in Phase 2 schon
  passiert).
- Pylint optional als `make pylint`-Target, kein CI-Blocker.

**3.2 GitHub Actions**
- Neu: `.github/workflows/ci.yml`. Matrix py311 + py312, Steps:
  `astral-sh/setup-uv@v3`, `uv sync --frozen`, `uv run ruff check .`,
  `uv run mypy pycgnweb`, `uv run pytest`, `uvx pip-audit`.
- Optional zweiter Job mit `playwright install --with-deps chromium` und
  `pytest -m e2e`.

**3.3 Dependabot**
- Neu: `.github/dependabot.yml`, Ecosystems `uv` + `github-actions`, weekly.

**3.4 docutils-Hardening**
- `pycgnweb/webapp.py` `publish_parts`-Aufruf um sichere Settings ergänzen:
  `{'doctitle_xform': False, 'report_level': 5, 'halt_level': 5,
  'file_insertion_enabled': False, 'raw_enabled': False}`.
- Trust-Boundary in README dokumentieren.

**3.5 Playwright-Tests (klein)**
- Neu: `_tests/test_e2e.py` mit zwei Smoke-Tests (Startseite, Termine), Marker
  `@pytest.mark.e2e`.

**3.6 mypy-Konfiguration**
- `pyproject.toml` `[tool.mypy]` mit `python_version = "3.11"`,
  progressiv: `disallow_untyped_defs = true`, `warn_unused_ignores = true`,
  `warn_return_any = true`.
- Bei externen Libs ohne Stubs gezielt `[[tool.mypy.overrides]]` mit
  `ignore_missing_imports = true`.

---

## Phase 4 — Code Review / Cleanup (eine PR)

Risiko: niedrig. Reine Idiomatik-Bumps, kein Verhaltenswechsel.

**4.1 webapp.py modernisieren**
- `import codecs` raus, `codecs.open(filename, 'r', 'utf-8')` →
  `open(filename, encoding='utf-8')`.
- `%`/`.format()`/Konkatenation auf f-strings normalisieren.
- pylint-disable/enable-Kommentare prüfen — bei ruff überflüssig.
- `# pylint: disable=W0613` ersetzen durch Argument-Rename `_err`.

**4.2 ensure_next_meeting (out of scope, nur kommentieren)**
- Schreibt bei jedem GET /events eine Datei in den Templates-Ordner.
  Größerer Refactor, nicht Teil dieser Renovierung — TODO-Kommentar mit
  Verweis auf GitHub-Issue.

**4.3 Coding-Style normalisieren**
- `ruff format` (oder `ruff check --fix`) über `pycgnweb/` und `_tests/`.

**4.4 Type-Hints durchgängig**
- Alle Funktionen in `pycgnweb/` annotieren. Modern Syntax (PEP 604/585).
- `_tests/`: pytest-Funktionen mit `-> None` annotieren.
- Verifikation: `uv run mypy pycgnweb` ohne Errors.

---

## Phase 5 — Inhalts-Migration ReST → Markdown (eigene PR)

Risiko: mittel. Inhalts-Diff aller 11 Seiten manuell verifizieren.

**Bestand**: 11 ReST-Dateien in `templates/rst/`:
- 4 statisch: `about.rst`, `contact.rst`, `events.rst`, `join.rst`
- 7 Event-Dateien: `events/2017-08-09.rst` bis `events/2024-02-14.rst`

**5.1 Konvertierung**
- `pandoc -f rst -t gfm` für jede Datei einzeln.
- Ziel-Verzeichnis: `templates/md/`, `templates/rst/` nach erfolgreichem
  Smoke-Test löschen.
- Stolperfalle: ReST-Field-Lists. Konvention: `**Datum:** Mi, 14.02.2024`
  (kein Plugin nötig) — alternativ Definition-Lists per `mdit-py-plugins`.

**5.2 Code-Umbau in webapp.py**
- Import: `from docutils.core import publish_parts` →
  `from markdown_it import MarkdownIt`.
- Module-Konstante:
  `_md = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])`.
- `get_content`: `publish_parts(...)['html_body']` → `_md.render(rst_data)`.
- `get_template`-Aufrufe: Pfad `"rst"` → `"md"`, Endung `.rst` → `.md`.
- `ensure_next_meeting`: RST-Template-String durch Markdown-Template
  ersetzen.

**5.3 Dependencies tauschen**
- `pyproject.toml`: `docutils` raus, `markdown-it-py>=3` rein.

**5.4 Hardening anpassen**
- `MarkdownIt(..., {"html": False})` ist Default-sicher. Phase 3.4
  docutils-Settings entfallen damit.
- Trust-Boundary in README.md aktualisieren.

**5.5 Verifikation**
- `uv run pytest` grün.
- Manuell: alle 5 statischen Routen + ein Event-Datum aufrufen,
  HTML-Diff vs. Vorzustand prüfen.
- `templates/rst/` erst nach Smoke-Test löschen.

---

## Critical Files

Bestehend (zu ändern):
- `pyproject.toml` (Migration Poetry → uv/PEP 621)
- `AUTHORS`
- `README.rst` → `README.md` (Phase 1.4)
- `Makefile`
- `.hgignore` (umwandeln → `.gitignore`, löschen)
- `setup.py` (löschen)
- `tox.ini` (löschen)
- `poetry.lock` (löschen, durch `uv.lock` ersetzt)
- `pycgnweb/config.py`
- `pycgnweb/webapp.py`
- `templates/rst/*.rst` (Phase 5: nach `templates/md/*.md` migrieren)

Neu:
- `.gitignore`
- `README.md`
- `uv.lock` (von uv generiert)
- `docs/renovation-2026.md` (diese Datei)
- `.github/workflows/ci.yml`
- `.github/dependabot.yml`
- `_tests/test_e2e.py`
- `templates/md/` (Phase 5)

---

## Verification (nach jeder Phase)

1. `uv sync`
2. `uv run pytest` — bestehende Tests grün.
3. `uv run ruff check .` — keine Errors (ab Phase 3).
4. Smoke: `uv run python -m pycgnweb` startet, `curl localhost:5014/`,
   `/about`, `/events`, `/contact`, `/join` liefern jeweils 200.
5. `uvx pip-audit` — keine kritischen CVEs (ab Phase 3).
6. `git status` sauber, jeder Phasen-Commit selbsterklärend.

Nach allen Phasen: Push, GitHub-Actions grün, Dependabot-PRs prüfen.
