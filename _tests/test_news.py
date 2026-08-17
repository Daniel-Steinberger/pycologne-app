"""Tests fuer den News-Bereich und den Atom-Feed.

Der Inhaltsbestand kommt aus `conftest.py`, nicht aus dem Content-Repo,
s. dort die Begruendung.
"""

import os
import shutil
from xml.etree import ElementTree

import pytest

from pycgnweb.webapp import app, get_news

from .conftest import NEWEST_NEWS, NEWS_ENTRIES, OLDEST_NEWS, REPO_ROOT

ATOM = "{http://www.w3.org/2005/Atom}"


@pytest.fixture
def client(template_root):
    """Flask-Test-Client auf dem Inhaltsbestand der Tests."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def client_without_news(tmp_path):
    """Client auf einem Bestand, in dem md/news/ ganz fehlt.

    Genau der Zustand auf dem Server, solange der Content-Checkout noch
    keinen News-Ordner hat: die Seite muss trotzdem stehen.
    """
    for template in (REPO_ROOT / "templates").glob("*.html"):
        shutil.copy(template, tmp_path)
    (tmp_path / "md").mkdir()
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(tmp_path)
    app.config["TESTING"] = True
    return app.test_client()


def _feed(client):
    """Den Feed holen und geparst zurueckgeben, mit dem Rohtext daneben."""
    response = client.get("/news.atom")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    # noqa unten: geparst wird der Feed, den diese Anwendung gerade selbst
    # gebaut hat, keine fremde Eingabe. Genau das ist der Zweck des Tests.
    return ElementTree.fromstring(body), body, response  # noqa: S314


# ---- Uebersicht ---------------------------------------------------------


def test_news_page_lists_entries_newest_first(client):
    """Die Uebersicht zeigt alle Eintraege, den neuesten oben."""
    page = client.get("/news").get_data(as_text=True)
    assert "Facebook nach zehn Jahren" in page
    assert "Neue Webseite" in page
    assert page.index("Facebook nach zehn Jahren") < page.index("Neue Webseite")


def test_news_page_skips_files_that_do_not_match_the_pattern(client):
    """Ein Dateiname ohne Datum taucht nicht in der Uebersicht auf."""
    page = client.get("/news").get_data(as_text=True)
    assert "Ohne Datum" not in page


def test_news_teaser_keeps_leading_bold_text(client):
    """Ein Absatz, der mit Fettschrift beginnt, ist der Teaser.

    Anders als bei den Terminen, wo an derselben Stelle die Datum- und
    Ort-Zeilen stehen und uebersprungen werden muessen.
    """
    entries = {entry["slug"]: entry for entry in get_news()}
    teaser = str(entries[OLDEST_NEWS]["teaser"])
    assert "<strong>Endlich:</strong>" in teaser
    # Das einleitende Bild gehoert nicht in den Teaser.
    assert "<img" not in teaser


def test_news_menu_entry_is_marked_active(client):
    """Der Menuepunkt News ist auf der News-Seite als aktuell markiert."""
    page = client.get("/news").get_data(as_text=True)
    assert '<a href="/news" aria-current="page">News</a>' in page


# ---- Einzelseite --------------------------------------------------------


def test_news_entry_is_served(client):
    """Ein vorhandener Eintrag wird ausgeliefert."""
    response = client.get(f"/news/{NEWEST_NEWS}")
    assert response.status_code == 200
    assert "Facebook nach zehn Jahren" in response.get_data(as_text=True)


@pytest.mark.parametrize(
    "slug",
    [
        "kein-datum",  # passt nicht aufs Muster
        "2026-08-17-Gross",  # Grossbuchstaben sind nicht vorgesehen
        "2026-13-45-unmoegliches-datum",  # Muster passt, Datum nicht
        "2026-08-17-gibt-es-nicht",  # Muster passt, Datei fehlt
    ],
)
def test_unknown_news_entry_returns_404(client, slug):
    """Was es nicht gibt, gibt es nicht. Kein Platzhalter wie bei Terminen."""
    assert client.get(f"/news/{slug}").status_code == 404


def test_news_entry_does_not_escape_the_content_directory(client):
    """Ein Slug kann nicht aus dem News-Ordner herausfuehren."""
    assert client.get("/news/..%2F..%2Fabout").status_code == 404


# ---- Atom-Feed ----------------------------------------------------------


def test_feed_is_served_as_atom(client):
    """Der Feed kommt mit dem richtigen Medientyp."""
    _, _, response = _feed(client)
    assert response.mimetype == "application/atom+xml"


def test_feed_is_wellformed_and_ordered(client):
    """Der Feed ist gueltiges XML und fuehrt den neuesten Eintrag zuerst."""
    root, _, _ = _feed(client)
    titles = [entry.findtext(f"{ATOM}title") for entry in root.findall(f"{ATOM}entry")]
    assert titles == ["Facebook nach zehn Jahren", "Neue Webseite"]
    assert root.findtext(f"{ATOM}title") == "PyCologne, Neuigkeiten"


def test_feed_entry_carries_stable_id_and_absolute_link(client):
    """Die ID ist ein tag-URI, der Link eine absolute Adresse."""
    root, _, _ = _feed(client)
    entry = root.find(f"{ATOM}entry")
    assert entry is not None
    assert entry.findtext(f"{ATOM}id") == f"tag:pycologne.de,2026:news/{NEWEST_NEWS}"
    link = entry.find(f"{ATOM}link")
    assert link is not None
    assert link.get("href") == f"https://www.pycologne.de/news/{NEWEST_NEWS}"


def test_feed_timestamps_are_rfc3339(client):
    """Zeitstempel tragen Datum, Uhrzeit und Zonenangabe."""
    root, _, _ = _feed(client)
    entry = root.find(f"{ATOM}entry")
    assert entry is not None
    assert entry.findtext(f"{ATOM}updated") == "2026-08-17T09:00:00Z"
    assert entry.findtext(f"{ATOM}published") == "2026-08-17T09:00:00Z"


def test_feed_content_is_escaped_html(client):
    """Der Eintrag steht vollstaendig im Feed, als escapetes HTML.

    Beides zusammen ist der Punkt: auf der Leitung escaped, damit das XML
    gueltig bleibt, und nach dem Parsen wieder echtes HTML, damit der Reader
    den Beitrag zu Ende zeigen kann.
    """
    root, body, _ = _feed(client)
    assert "&lt;a href=" in body
    entry = root.find(f"{ATOM}entry")
    assert entry is not None
    content = entry.findtext(f"{ATOM}content") or ""
    assert '<a href="https://www.meetup.com/pycologne/">' in content
    assert content.strip().startswith("<h1>")


def test_feed_makes_relative_references_absolute(client):
    """Verweise auf die eigene Seite sind im Feed absolut.

    Ein Reader hat keinen Bezugspunkt fuer "/static/images/...", ein
    relativer Verweis waere dort ein leeres Bild oder ein toter Link.
    """
    root, _, _ = _feed(client)
    entries = root.findall(f"{ATOM}entry")
    content = entries[-1].findtext(f"{ATOM}content") or ""
    assert 'src="https://www.pycologne.de/static/images/events/beispiel.svg"' in content
    assert 'src="/static/' not in content
    # Fremde Adressen bleiben unangetastet.
    first = entries[0].findtext(f"{ATOM}content") or ""
    assert 'href="https://www.meetup.com/pycologne/"' in first


def test_feed_skips_files_that_do_not_match_the_pattern(client):
    """Der Feed enthaelt genau die Eintraege der Uebersicht."""
    root, _, _ = _feed(client)
    assert len(root.findall(f"{ATOM}entry")) == len(NEWS_ENTRIES)


def test_feed_is_discoverable_from_every_page(client):
    """Der Feed ist im Head verlinkt, sonst findet ihn kein Reader."""
    page = client.get("/").get_data(as_text=True)
    assert 'rel="alternate" type="application/atom+xml"' in page
    assert 'href="/news.atom"' in page


# ---- Ohne Inhalte -------------------------------------------------------


def test_news_page_without_any_entries(client_without_news):
    """Ohne News-Ordner steht die Seite und sagt, dass nichts da ist."""
    response = client_without_news.get("/news")
    assert response.status_code == 200
    assert "Noch ist nichts eingetragen" in response.get_data(as_text=True)


def test_feed_without_any_entries_is_still_valid(client_without_news):
    """Ein leerer Feed ist gueltiges Atom, kein Fehler."""
    root, _, _ = _feed(client_without_news)
    assert root.findall(f"{ATOM}entry") == []
    assert root.findtext(f"{ATOM}updated")


def test_home_page_hides_the_news_tile_when_there_is_nothing(client_without_news):
    """Ohne Eintraege bleibt die Startseite unveraendert."""
    page = client_without_news.get("/").get_data(as_text=True)
    assert "tile--news" not in page
