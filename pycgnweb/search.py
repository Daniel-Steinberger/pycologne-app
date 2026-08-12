"""Volltextsuche ueber die Treffenprotokolle, per SQLite FTS5.

Der Index entsteht beim ersten Suchaufruf im Speicher aus den
Markdown-Dateien unter ``templates/md/events/`` und wird neu gebaut, sobald
sich dort etwas aendert. Bei rund hundert Protokollen dauert das wenige
Millisekunden, deshalb braucht es keine Datei auf der Platte und keinen
Vorbereitungsschritt beim Deployment.

Warum FTS5 und keine Embeddings: Der Bestand ist klein und die Suchbegriffe
sind ueberwiegend Namen von Bibliotheken, Werkzeugen und Personen ("pandas",
"flake8", "Metaklassen"). Genau dort ist eine lexikalische Suche einer
semantischen ueberlegen, und sie kommt ohne Modell, ohne externen Dienst und
ohne Zustand aus.
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from typing import Any

# Marker fuer Treffer im Snippet. Bewusst Steuerzeichen, damit sie im
# Protokolltext nicht vorkommen koennen: Das Snippet wird erst HTML-escaped
# und danach werden die Marker durch <mark>-Tags ersetzt.
HIGHLIGHT_OPEN = "\x02"
HIGHLIGHT_CLOSE = "\x03"

_DEFAULT_LIMIT = 30

_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_FENCE_RE = re.compile(r"^\s*```")
_MARKUP_RE = re.compile(r"[*_`>]+")
_HEADING_RE = re.compile(r"^#+\s*")
_TERM_RE = re.compile(r"[\w\-.äöüÄÖÜß]+", re.UNICODE)


def _plain_text(md_text: str) -> str:
    """Markdown auf durchsuchbaren Text reduzieren.

    Auszeichnung fliegt raus, Linktexte und URLs bleiben beide erhalten, denn
    nach "github" oder einem Domainnamen wird durchaus gesucht.
    """
    lines: list[str] = []
    for line in md_text.splitlines():
        if _FENCE_RE.match(line):
            continue
        line = _LINK_RE.sub(r"\1 \2", line)
        line = _HEADING_RE.sub("", line)
        line = _MARKUP_RE.sub("", line)
        lines.append(line.strip())
    return "\n".join(lines)


def _title(md_text: str, fallback: str) -> str:
    """Erste Ueberschrift des Protokolls, sonst *fallback*."""
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return fallback


def build_query(user_input: str) -> str:
    """Nutzereingabe in einen FTS5-Ausdruck uebersetzen.

    Die FTS5-Syntax kennt eigene Operatoren (``AND``, ``NEAR``, ``*``,
    Klammern), an denen eine unbedachte Eingabe zu einem SQL-Fehler fuehrt.
    Deshalb wird die Eingabe in Terme zerlegt, jeder Term als Phrase
    gequotet und mit ``*`` zur Praefixsuche erweitert. Mehrere Begriffe
    werden mit AND verknuepft, es zaehlt also nur, was alle Begriffe
    enthaelt.
    """
    terms = _TERM_RE.findall(user_input)
    if not terms:
        return ""
    return " AND ".join(f'"{term}"*' for term in terms)


class ProtocolIndex:
    """FTS5-Index ueber die Protokolldateien eines Verzeichnisses."""

    def __init__(self, events_dir: str) -> None:
        self.events_dir = events_dir
        self._connection: sqlite3.Connection | None = None
        self._fingerprint: tuple[tuple[str, int], ...] | None = None

    def _current_fingerprint(self) -> tuple[tuple[str, int], ...]:
        """Zustand des Verzeichnisses (Dateiname und mtime)."""
        if not os.path.isdir(self.events_dir):
            return ()
        return tuple(
            sorted(
                (entry.name, entry.stat().st_mtime_ns)
                for entry in os.scandir(self.events_dir)
                if entry.name.endswith(".md")
            )
        )

    def _build(self, fingerprint: tuple[tuple[str, int], ...]) -> sqlite3.Connection:
        """Index aus den Protokolldateien neu aufbauen."""
        connection = sqlite3.connect(":memory:", check_same_thread=False)
        connection.execute(
            """
            CREATE VIRTUAL TABLE protocols USING fts5(
                date UNINDEXED,
                title,
                body,
                tokenize="unicode61 remove_diacritics 2",
                prefix='2 3 4'
            )
            """
        )
        rows = []
        for name, _ in fingerprint:
            stem = name.removesuffix(".md")
            try:
                datetime.strptime(stem, "%Y-%m-%d")
            except ValueError:
                continue
            path = os.path.join(self.events_dir, name)
            with open(path, encoding="utf-8") as file_:
                md_text = file_.read()
            rows.append((stem, _title(md_text, stem), _plain_text(md_text)))
        connection.executemany("INSERT INTO protocols VALUES (?, ?, ?)", rows)
        connection.commit()
        return connection

    def connection(self) -> sqlite3.Connection:
        """Verbindung zum aktuellen Index, bei Bedarf neu gebaut."""
        fingerprint = self._current_fingerprint()
        if self._connection is None or fingerprint != self._fingerprint:
            if self._connection is not None:
                self._connection.close()
            self._connection = self._build(fingerprint)
            self._fingerprint = fingerprint
        return self._connection

    def search(self, user_input: str, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
        """Protokolle zu *user_input* finden, bestes Ergebnis zuerst.

        Jeder Treffer enthaelt Datum, Titel, URL und ein Textausschnitt mit
        markierten Fundstellen (die Marker sind Steuerzeichen, siehe oben).
        """
        query = build_query(user_input)
        if not query:
            return []
        # Die Tokenzahl von snippet() muss ein Literal sein, sie laesst sich
        # nicht als Parameter binden; alle Nutzereingaben sind gebunden.
        sql = """
            SELECT date,
                   title,
                   snippet(protocols, 2, ?, ?, '…', 14) AS excerpt
            FROM protocols
            WHERE protocols MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        try:
            cursor = self.connection().execute(sql, (HIGHLIGHT_OPEN, HIGHLIGHT_CLOSE, query, limit))
        except sqlite3.OperationalError:
            # Fuer den Fall, dass eine Eingabe trotz build_query eine
            # FTS5-Syntaxmeldung ausloest: keine Treffer statt Serverfehler.
            return []
        return [
            {
                "date": datetime.strptime(row[0], "%Y-%m-%d").replace(hour=19),
                "title": row[1],
                "url": f"/events/{row[0]}",
                "excerpt": row[2],
            }
            for row in cursor.fetchall()
        ]
