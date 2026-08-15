# PyCologne Webseite

Flask-Webanwendung für die Webseite der Python-User-Group Köln
([pycologne.de](https://www.pycologne.de)).

## Voraussetzungen

- Python 3.11 oder neuer
- [uv](https://docs.astral.sh/uv/) für Dependency-Management

uv-Installation:

```sh
pipx install uv
# oder
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

```sh
git clone https://github.com/Daniel-Steinberger/pycologne-app
cd pycologne-app
uv sync --group dev
uv run pre-commit install
```

## Inhalte

Die redaktionellen Inhalte (Termine, Protokolle, Bilder) liegen **nicht** in
diesem Repo, sondern in
[pycologne-content](https://github.com/Daniel-Steinberger/pycologne-content).
`make run` holt sie sich von selbst: fehlt der Checkout, wird er als
Schwester-Verzeichnis geklont, und `templates/md` sowie `static/images`
werden als Symlinks dorthin gelegt. Beide Symlinks stehen in der
`.gitignore`.

```sh
make content                          # nur verlinken, ohne Server
make run CONTENT=/anderer/pfad        # Checkout an anderer Stelle
```

Auf dem Server sieht es genauso aus, nur unter `/var/lib/pycologne/`. Damit
ist eine reine Textänderung ein Commit im Content-Repo, ohne neuen Build
dieses Pakets und ohne Neustart: die Anwendung liest Markdown bei jedem
Aufruf frisch von der Platte, und die beiden Zwischenspeicher (Übersicht der
vergangenen Treffen, Suchindex) hängen an Dateiname und mtime des
Verzeichnisses.

Die Tests brauchen den Content-Checkout **nicht**. Sie bauen sich einen
eigenen kleinen Bestand, s. `_tests/conftest.py`.

## Entwicklung

Server starten (mit Debug-Modus und Auto-Reload):

```sh
make run
# oder direkt:
uv run python -m pycgnweb -d
```

Tests:

```sh
uv run pytest
```

Linting / Type-Checks:

```sh
uv run ruff check .
uv run mypy pycgnweb
```

## Pre-Commit-Hook

`ruff check --fix` und `ruff format` laufen automatisch vor jedem Commit
(via [pre-commit](https://pre-commit.com/)), damit Formatierungsfehler
nicht erst in der CI auffallen. Einrichtung siehe Setup oben
(`uv run pre-commit install`); danach greift der Hook bei jedem
`git commit`. Manueller Lauf über alle Dateien:

```sh
uv run pre-commit run --all-files
```

## Projektstruktur

```
pycgnweb/        Hauptmodul (Flask-Routen, Konfiguration, Sitzungs-Logik)
templates/       Jinja2-Templates; templates/md ist ein Symlink ins Content-Repo
static/          CSS und JavaScript; static/images ist ein Symlink ins Content-Repo
_tests/          pytest-Tests, mit eigenem Inhaltsbestand in conftest.py
docs/            Projekt-Dokumentation (z.B. Renovierungsplan)
```

## Inhalte und Trust-Boundary

Die Inhalte der einzelnen Seiten liegen als Markdown-Dateien im Content-Repo
(unter `templates/md/` eingehängt, s. oben) und werden vom Server zu HTML
gerendert (`markdown-it-py` mit `html=True`) und mit `|safe` ins Template
eingebunden. Inline-HTML in den Markdown-Dateien ist erlaubt, weil einzelne
Seiten (z.B. die Anfahrt mit Leaflet-Karte) HTML-Snippets benötigen. Quelle
dieser Dateien sind ausschließlich Maintainer-Commits, es gibt keinen
Upload-Pfad zur Laufzeit.

Das gilt nach der Trennung unverändert weiter: Schreibzugriff auf das
Content-Repo haben nur Maintainer, Beiträge von außen laufen über Pull
Requests.

## Anstoß für neue Inhalte

`POST /_content/refresh` nimmt entgegen, dass es im Content-Repo etwas Neues
gibt. Der Endpunkt prüft die HMAC-SHA256-Signatur von GitHub
(`X-Hub-Signature-256`) und berührt danach eine Datei, sonst nichts. Das
Holen selbst erledigt auf dem Server eine systemd-Unit, die diese Datei
beobachtet. So läuft kein `git` im Request-Handler, es braucht kein Locking
gegen die anderen Gunicorn-Worker, und die Anwendung kommt ohne erhöhte
Rechte aus.

Beide Pfade dazu stehen in `pycgnweb/config.py` und lassen sich per
Umgebungsvariable umbiegen (`PYCOLOGNE_WEBHOOK_SECRET_FILE`,
`PYCOLOGNE_CONTENT_TRIGGER`). Ist keine Secret-Datei hinterlegt, wie bei der
lokalen Entwicklung, antwortet der Endpunkt mit 503 und tut nichts.

## Beitragende

Siehe [`AUTHORS`](AUTHORS) und `git log`.

## Lizenz

GPL-3.0-or-later
