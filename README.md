# PyCologne Webseite

Flask-Webanwendung für die Webseite der Python-User-Group Köln
([pycologne.de](https://www.pycologne.de)).

## Voraussetzungen

- Python 3.11 oder neuer
- [uv](https://docs.astral.sh/uv/) für Dependency-Management
- `lessc` (Paket `node-less` unter Debian/Ubuntu) zum Kompilieren der CSS-Dateien

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
uv sync
```

## Entwicklung

Server starten (mit Debug-Modus und Auto-Reload):

```sh
make run
# oder direkt:
uv run python -m pycgnweb -d
```

CSS aus LESS-Quellen bauen:

```sh
make less
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

## Projektstruktur

```
pycgnweb/        Hauptmodul (Flask-Routen, Konfiguration, Sitzungs-Logik)
templates/       Jinja2-Templates und ReST-Inhalte
static/          CSS, LESS-Quellen, Bilder
_tests/          pytest-Tests
docs/            Projekt-Dokumentation (z.B. Renovierungsplan)
```

## Inhalte und Trust-Boundary

Die Inhalte der einzelnen Seiten liegen als Markdown-Dateien unter
`templates/md/` und werden vom Server zu HTML gerendert (`markdown-it-py` mit
`html=True`) und mit `|safe` ins Template eingebunden. Inline-HTML in den
Markdown-Dateien ist erlaubt, weil einzelne Seiten (z.B. die Anfahrt mit
Leaflet-Karte) HTML-Snippets benötigen. Quelle dieser Dateien sind
ausschließlich Maintainer-Commits — es gibt keinen Upload-Pfad zur
Laufzeit.

## Beitragende

Siehe [`AUTHORS`](AUTHORS) und `git log`.

## Lizenz

GPL-3.0-or-later
