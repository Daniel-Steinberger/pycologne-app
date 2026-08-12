"""Tests fuer die Protokolldateien selbst, nicht fuer die Auslieferung."""

import pathlib
import re

import pytest

EVENTS_DIR = pathlib.Path("templates/md/events")

# Adressen im Fliesstext, die nicht als Link ausgezeichnet sind. Markdown-Links
# ``[text](url)``, Autolinks ``<url>`` und Codebloecke sind ausgenommen.
BARE_URL = re.compile(r'(?<![(<"\w])https?://')
BARE_HOST = re.compile(r"(?<![/\w.>(])www\.[\w.-]+\.[a-z]{2,}", re.I)
MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
AUTOLINK = re.compile(r"<https?://[^>]*>")


def protocol_files():
    """Alle Protokolldateien, nach Datum sortiert."""
    return sorted(EVENTS_DIR.glob("*.md"))


def text_lines(path):
    """Zeilen einer Datei ohne Codebloecke und ohne fertige Links."""
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        yield number, AUTOLINK.sub("", MD_LINK.sub("", line))


def test_protocol_directory_is_populated():
    """Die Protokolle liegen ausgeliefert im Template-Ordner."""
    assert len(protocol_files()) > 50


@pytest.mark.parametrize("path", protocol_files(), ids=lambda p: p.stem)
def test_addresses_are_linked(path):
    """Adressen im Protokolltext muessen klickbar sein.

    Ein Link braucht Markdown-Syntax, denn die linkify-Option des Parsers
    greift ohne das Paket linkify-it-py nicht: eine nackte URL bliebe
    schlichter Text.
    """
    offenders = [
        f"{path.name}:{number}: {stripped.strip()[:80]}"
        for number, stripped in text_lines(path)
        if BARE_URL.search(stripped) or BARE_HOST.search(stripped)
    ]
    assert not offenders, "nicht verlinkte Adressen:\n" + "\n".join(offenders)


@pytest.mark.parametrize("path", protocol_files(), ids=lambda p: p.stem)
def test_protocol_starts_with_heading(path):
    """Jedes Protokoll beginnt mit seiner Ueberschrift."""
    first = path.read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("# "), first
