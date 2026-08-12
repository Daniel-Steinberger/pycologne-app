"""Tests fuer die Volltextsuche ueber die Protokolle."""

import os

import pytest

from pycgnweb.search import HIGHLIGHT_CLOSE, HIGHLIGHT_OPEN, ProtocolIndex, build_query
from pycgnweb.webapp import app

PROTOCOL = """# PyCologne Treffen Mai 2019

**Datum:** 08.05.2019, 19:00 Uhr

Ein Abend über Datenanalyse mit pandas und eine Diskussion über Überraschungen
im Typsystem.

## Lightning Talks

### Datenanalyse mit pandas - Henning Dickten

Notizen dazu unter https://github.com/example/talk
"""

OTHER_PROTOCOL = """# PyCologne Treffen Juni 2019

**Datum:** 12.06.2019, 19:00 Uhr

Kurzer Abend, im Wesentlichen eine Runde über Testwerkzeuge.
"""


@pytest.fixture
def index(tmp_path):
    """Index ueber zwei Protokolle in einem temporaeren Verzeichnis."""
    (tmp_path / "2019-05-08.md").write_text(PROTOCOL, encoding="utf-8")
    (tmp_path / "2019-06-12.md").write_text(OTHER_PROTOCOL, encoding="utf-8")
    # Nicht datumsbenannte Dateien gehoeren nicht in den Index
    (tmp_path / "notizen.md").write_text("pandas pandas pandas", encoding="utf-8")
    return ProtocolIndex(str(tmp_path))


@pytest.fixture
def client():
    """Flask-Test-Client mit Pfaden auf das Repo-Root konfiguriert."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = os.path.join(os.getcwd(), "templates")
    app.config["TESTING"] = True
    return app.test_client()


def test_finds_protocol_by_word(index):
    """Ein Begriff aus dem Text findet das passende Protokoll."""
    results = index.search("pandas")
    assert [hit["url"] for hit in results] == ["/events/2019-05-08"]
    assert results[0]["title"] == "PyCologne Treffen Mai 2019"
    assert results[0]["date"].hour == 19


def test_prefix_and_diacritics(index):
    """Wortanfang genuegt, und Umlaute muessen nicht getippt werden."""
    assert index.search("panda")
    assert index.search("uberraschung")
    assert index.search("Überraschung")


def test_multiple_terms_are_combined_with_and(index):
    """Mehrere Begriffe muessen alle vorkommen."""
    assert index.search("pandas Datenanalyse")
    assert not index.search("pandas Testwerkzeuge")


def test_urls_are_searchable(index):
    """Auch Linkziele sind indexiert."""
    assert index.search("github")


def test_only_date_named_files_are_indexed(index):
    """Dateien ohne Datumsnamen bleiben aussen vor."""
    assert len(index.search("pandas")) == 1


def test_excerpt_marks_the_match(index):
    """Der Ausschnitt markiert die Fundstelle mit den Steuerzeichen."""
    excerpt = index.search("pandas")[0]["excerpt"]
    assert HIGHLIGHT_OPEN in excerpt
    assert HIGHLIGHT_CLOSE in excerpt


def test_index_picks_up_changes(index, tmp_path):
    """Eine neue Datei taucht ohne Neustart in den Ergebnissen auf."""
    assert not index.search("Metaklassen")
    (tmp_path / "2019-07-10.md").write_text(
        "# PyCologne Treffen Juli 2019\n\nEin Vortrag über Metaklassen.\n",
        encoding="utf-8",
    )
    assert index.search("Metaklassen")


@pytest.mark.parametrize("user_input", ["", "   ", "***", "((", '"', "AND OR NEAR"])
def test_odd_input_does_not_break(index, user_input):
    """FTS5-Syntax in der Eingabe darf keinen Fehler ausloesen."""
    assert isinstance(index.search(user_input), list)


def test_build_query_quotes_terms():
    """Aus der Eingabe wird ein AND-verknuepfter Praefix-Ausdruck."""
    assert build_query("pandas django") == '"pandas"* AND "django"*'
    assert build_query("  ") == ""


def test_search_page_without_query(client):
    """Die Suchseite ist auch ohne Suchbegriff erreichbar."""
    response = client.get("/suche")
    assert response.status_code == 200
    assert "Protokolle durchsuchen" in response.get_data(as_text=True)


def test_search_page_lists_hits(client):
    """Eine Suche auf den echten Protokollen liefert verlinkte Treffer."""
    html = client.get("/suche?q=Protokoll").get_data(as_text=True)
    assert 'class="search-results__item"' in html
    assert "<mark>" in html


def test_search_page_escapes_content(client):
    """Der Ausschnitt darf kein Markup aus dem Protokolltext einschleusen."""
    html = client.get("/suche?q=Protokoll").get_data(as_text=True)
    # die Steuerzeichen selbst duerfen nicht in der Seite landen
    assert HIGHLIGHT_OPEN not in html
    assert HIGHLIGHT_CLOSE not in html


def test_events_page_offers_search(client):
    """Von der Termine-Seite fuehrt ein Suchfeld zur Protokollsuche."""
    html = client.get("/events").get_data(as_text=True)
    assert 'action="/suche"' in html
