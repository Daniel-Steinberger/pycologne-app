"""Tests fuer die Flip-Kacheln (Code hinter der Kachel, s. docs/design.md)."""

import os

import pytest

from pycgnweb.webapp import app, get_code_reveals

GITHUB_PREFIX = "https://github.com/Daniel-Steinberger/pycologne-app/blob/main/pycgnweb/"


@pytest.fixture
def client(template_root):
    """Flask-Test-Client auf dem Inhaltsbestand der Tests."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return app.test_client()


def test_registry_covers_all_four_tiles():
    """Das Register kennt genau die vier Kandidaten aus dem Konzept."""
    reveals = get_code_reveals()
    assert set(reveals) == {"meeting", "saying", "query", "ics"}
    for reveal in reveals.values():
        # Quelltext kommt gehighlightet im Matrix-Stil
        assert 'class="mx-highlight"' in reveal["html"]
        # der No-JS-Fallback zeigt auf die Funktion, mit Zeilenanker
        assert reveal["github"].startswith(GITHUB_PREFIX)
        assert "#L" in reveal["github"]
        assert reveal["path"].startswith("pycgnweb/")


def test_source_is_read_live_not_copied():
    """Die Rueckseite zeigt den echten Quelltext, nicht eine Kopie."""
    html = get_code_reveals()["meeting"]["html"]
    # das charakteristische Stueck der Terminberechnung
    assert "WE" in html
    assert "meeting_dates" in html


def test_index_has_two_flip_tiles(client):
    """Startseite: Termin-Kachel und Zen-Kachel lassen sich umdrehen."""
    html = client.get("/").get_data(as_text=True)
    assert html.count("flip__face--back") == 2
    assert "pycgnweb/events.py" in html
    assert "pycgnweb/sayings.py" in html
    # REPL-Zeilen: Aufruf und live ausgewertetes Ergebnis
    assert "next(meeting_dates())" in html
    assert "datetime.datetime(" in html
    assert "get_saying()" in html


def test_chip_falls_back_to_github_link(client):
    """Ohne JavaScript ist der Griff ein Link auf den Quelltext."""
    html = client.get("/").get_data(as_text=True)
    assert f'href="{GITHUB_PREFIX}sayings.py#L' in html
    assert "data-flip-toggle" in html


def test_controls_carry_tooltips(client):
    """Griff und Schliessen-Knopf tragen ihre Tooltips."""
    html = client.get("/").get_data(as_text=True)
    assert html.count('title="Peek into the code"') == 2
    assert html.count('title="Exit the Matrix"') == 2


def test_hero_and_features_stay_plain(client):
    """Kacheln ohne Code dahinter bekommen keinen Griff."""
    html = client.get("/").get_data(as_text=True)
    # 2 Griffe auf der Startseite, nicht 4
    assert html.count("flip__chip") == 2


def test_chip_sits_inside_the_front_face(client):
    """Der Griff gehoert zur Vorderseite und dreht mit ihr weg.

    Deshalb muss er im Markup innerhalb der Front stehen, nicht als
    Geschwister daneben, sonst bliebe er beim Drehen stehen.
    """
    html = client.get("/").get_data(as_text=True)
    for chunk in html.split("flip__face--front")[1:]:
        face = chunk.split("</article>")[0].split("flip__face--back")[0]
        assert "flip__chip" in face


def test_back_brings_its_own_close_control(client):
    """Jede Rueckseite hat ihren Schliessen-Knopf in der Kopfzeile."""
    html = client.get("/").get_data(as_text=True)
    assert html.count("data-flip-close") == 2
    assert html.count("mx__close") == 2


def test_events_page_flips_meeting_and_ics(client):
    """Termine: Termin-Karte und Kalender-Abo tragen ihre Rueckseiten."""
    html = client.get("/events").get_data(as_text=True)
    assert html.count("flip__face--back") == 2
    assert "_ics_fold" in html
    assert "pycgnweb/webapp.py" in html
    # die alte details-Mechanik ist ersetzt
    assert "code-reveal" not in html


def test_search_page_shows_running_query_as_fts(client):
    """Suche: die REPL-Zeile zeigt die gerade laufende Suche als FTS5."""
    html = client.get("/suche?q=pandas+dataframe").get_data(as_text=True)
    assert "build_query" in html
    # build_query('pandas dataframe') liefert "pandas"* AND "dataframe"*
    assert "pandas" in html
    assert "AND" in html


def test_search_page_without_query_shows_example(client):
    """Ohne Suchbegriff zeigt die Rueckseite ein Beispiel statt Leere."""
    html = client.get("/suche").get_data(as_text=True)
    assert "build_query" in html
    assert "flip__face--back" in html


def test_about_keeps_its_terminal(client):
    """/about behaelt den Code-Einblick, jetzt als Matrix-Terminal."""
    html = client.get("/about").get_data(as_text=True)
    assert "mx__bar" in html
    assert "pycgnweb/sayings.py" in html
    assert "Zitate-Generator" in html
