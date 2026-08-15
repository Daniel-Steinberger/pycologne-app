"""Smoke-Tests fuer HTTP-Status aller Routen via Flask-Test-Client.

Die Inhalte kommen aus dem Bestand in `conftest.py`, nicht aus dem
Content-Repo, s. dort die Begruendung.
"""

import os
import re
from datetime import datetime

import pytest

from pycgnweb.webapp import (
    app,
    get_meeting_location,
    get_next_meeting_teaser,
    get_past_meetings,
    group_meetings_by_year,
)

from .conftest import NEWEST_PAST, OLD_STYLE_PAST, PAST_REFERENCE, TEASER_PAST


@pytest.fixture
def client(template_root):
    """Flask-Test-Client auf dem Inhaltsbestand der Tests."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize(
    "path",
    ["/", "/index", "/about", "/join", "/events", "/contact"],
)
def test_page_returns_ok(client, path):
    """Jede der oeffentlichen Routen muss HTTP 200 liefern."""
    response = client.get(path)
    assert response.status_code == 200


def test_unknown_url_returns_404(client):
    """Unbekannte URLs muessen 404 liefern."""
    response = client.get("/this-does-not-exist")
    assert response.status_code == 404


def test_events_page_lists_past_meetings(client):
    """Die Termine-Seite verlinkt vergangene Treffen mit Protokoll-Hinweis."""
    response = client.get("/events")
    html = response.get_data(as_text=True)
    assert "Vergangene Treffen" in html
    assert f'href="/events/{NEWEST_PAST}"' in html


def test_past_event_page_returns_ok(client):
    """Protokollseiten vergangener Treffen muessen erreichbar sein."""
    response = client.get(f"/events/{NEWEST_PAST}")
    assert response.status_code == 200


def test_upcoming_meeting_without_file_shows_placeholder(client, upcoming):
    """Ein anstehender Termin ohne eigene Datei zeigt den Platzhalter.

    Frueher legte `ensure_next_meeting()` dafuer eine Datei im
    Template-Ordner an. Seit die Inhalte aus einem Git-Checkout kommen,
    wird dort nicht mehr geschrieben, der Platzhalter entsteht beim
    Rendern.
    """
    # Der dritte anstehende Termin hat im Bestand bewusst keine Datei
    date = upcoming[2]
    response = client.get(f"/events/{date:%Y-%m-%d}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "steht noch nicht fest" in html
    # Der Monatsname muss deutsch sein, nicht in der Systemsprache
    assert "PyCologne Treffen" in html


def test_upcoming_meeting_writes_nothing(client, upcoming, template_root):
    """Der Platzhalter darf keine Datei im Inhaltsverzeichnis hinterlassen.

    Der Ordner ist auf dem Server ein Git-Checkout. Eine Datei, die die
    Anwendung dort anlegt, kollidiert mit dem naechsten Abgleich.
    """
    events_dir = template_root / "md" / "events"
    before = sorted(path.name for path in events_dir.iterdir())
    client.get(f"/events/{upcoming[2]:%Y-%m-%d}")
    client.get("/events")
    client.get("/")
    assert sorted(path.name for path in events_dir.iterdir()) == before


def test_date_that_is_no_meeting_returns_404(client):
    """Ein Datum ohne Datei und ohne Termin bleibt ein 404."""
    assert client.get("/events/2099-03-04").status_code == 404
    assert client.get("/events/kein-datum").status_code == 404


def test_get_past_meetings_metadata(client, upcoming):  # pylint: disable=unused-argument
    """get_past_meetings liefert Daten absteigend samt Inhaltshinweisen.

    Die client-Fixture wird nur gebraucht, um app.template_folder auf den
    Inhaltsbestand der Tests zu setzen.
    """
    meetings = get_past_meetings(PAST_REFERENCE)

    dates = [meeting["date"] for meeting in meetings]
    assert dates == sorted(dates, reverse=True)
    # Treffen finden um 19:00 statt, nicht um Mitternacht
    assert all(date.hour == 19 for date in dates)

    by_url = {meeting["url"]: meeting for meeting in meetings}
    # zukuenftige Termine tauchen nicht in der Vergangenheitsliste auf
    assert f"/events/{upcoming[0]:%Y-%m-%d}" not in by_url
    # Protokoll mit Zusammenfassung: ###-Ueberschriften als Themen
    assert any("HPC" in topic for topic in by_url[f"/events/{NEWEST_PAST}"]["topics"])
    # Datei ohne Protokoll-Abschnitte: erste Textzeile als Teaser
    assert by_url[f"/events/{TEASER_PAST}"]["teaser"].startswith("Da Daniel")
    # altes Protokoll mit Programmliste
    assert by_url[f"/events/{OLD_STYLE_PAST}"]["topics"] == [
        "Einfuehrung in Metaklassen",
        "Kurzvorstellung von flake8",
    ]


def test_group_meetings_by_year(client):  # pylint: disable=unused-argument
    """Die Gruppierung liefert Jahrgaenge absteigend, Treffen darin ebenso."""
    meetings = get_past_meetings(PAST_REFERENCE)
    grouped = group_meetings_by_year(meetings)

    years = [year for year, _ in grouped]
    assert years == sorted(years, reverse=True)
    # kein Treffen geht bei der Gruppierung verloren oder doppelt hinein
    assert sum(len(items) for _, items in grouped) == len(meetings)
    for year, items in grouped:
        assert all(meeting["date"].year == year for meeting in items)
        dates = [meeting["date"] for meeting in items]
        assert dates == sorted(dates, reverse=True)


def test_get_past_meetings_uses_cache(client):  # pylint: disable=unused-argument
    """Zwei Aufrufe ohne Dateiaenderung liefern dasselbe Listenobjekt."""
    first = get_past_meetings(PAST_REFERENCE)
    second = get_past_meetings(PAST_REFERENCE)
    assert first is second


def test_new_content_appears_without_restart(client, template_root):
    """Eine neue Protokolldatei wirkt sofort, ohne Neustart.

    Das ist die Annahme, auf der das ganze Content-Deployment ruht: der
    Abgleich legt Dateien auf die Platte, mehr passiert nicht. Beide
    Zwischenspeicher haengen an Dateiname und mtime des Verzeichnisses.
    """
    before = get_past_meetings(PAST_REFERENCE)
    new_file = template_root / "md" / "events" / "2018-04-11.md"
    new_file.write_text(
        "# PyCologne Treffen April 2018\n\nEin nachtraeglich ergaenztes Protokoll.\n",
        encoding="utf-8",
    )
    try:
        after = get_past_meetings(PAST_REFERENCE)
        assert len(after) == len(before) + 1
        assert "/events/2018-04-11" in {meeting["url"] for meeting in after}
        assert client.get("/events/2018-04-11").status_code == 200
    finally:
        new_file.unlink()


def test_events_page_groups_archive_by_year(client):
    """Aeltere Treffen erscheinen als aufklappbare Jahrgaenge."""
    html = client.get("/events").get_data(as_text=True)
    assert "Aus dem Archiv" in html
    assert 'class="past-year"' in html
    # das jeweils oberste Jahr ist aufgeklappt
    assert re.search(r'<details class="past-year" open>', html)


def test_events_ics_feed(client):
    """Der iCalendar-Feed muss Status 200 und text/calendar liefern."""
    response = client.get("/events.ics")
    assert response.status_code == 200
    assert response.mimetype == "text/calendar"
    body = response.get_data(as_text=True)
    assert body.startswith("BEGIN:VCALENDAR")
    assert "END:VCALENDAR" in body
    assert "BEGIN:VEVENT" in body
    assert "PyCologne Treffen" in body
    # RFC 5545, 3.1: keine Content-Zeile laenger als 75 Oktette
    assert all(len(line.encode("utf-8")) <= 75 for line in body.split("\r\n"))


def test_events_ics_feed_carries_program(client):
    """Ist das Programm bekannt, steht es in der DESCRIPTION des Termins."""
    body = client.get("/events.ics").get_data(as_text=True)
    # Faltung rueckgaengig machen, um die Werte am Stueck pruefen zu koennen
    unfolded = body.replace("\r\n ", "")
    seen_program = False
    for event in unfolded.split("BEGIN:VEVENT")[1:]:
        date = re.search(r"UID:meeting-(\d{4}-\d{2}-\d{2})@", event).group(1)
        # ICS-DESCRIPTION ist Klartext, HTML-Tags werden dort entfernt
        teaser = re.sub(
            r"<[^>]+>", "", get_next_meeting_teaser(datetime.strptime(date, "%Y-%m-%d"))
        )
        if teaser:
            seen_program = True
            # erstes Wort genuegt: der Rest ist ICS-escaped
            assert teaser.split(",")[0] in event
        # der allgemeine Hinweistext bleibt in jedem Fall erhalten
        assert "Monatliches Treffen der Python User Group" in event
    # Der Bestand enthaelt einen anstehenden Termin mit Programm, der Test
    # darf also nicht nur zufaellig durchlaufen, weil keiner eines hat.
    assert seen_program


def test_events_ics_feed_carries_actual_location(client):
    """Weicht ein Termin vom Standardort ab, muss LOCATION das auch zeigen.

    Bugfix: LOCATION war frueher fuer alle Termine hart auf die DVS AG
    codiert, auch fuer Ausweichtermine wie das Cologne Game Lab.
    """
    body = client.get("/events.ics").get_data(as_text=True)
    unfolded = body.replace("\r\n ", "")
    events = unfolded.split("BEGIN:VEVENT")[1:]
    found_deviation = False
    for event in events:
        date = re.search(r"UID:meeting-(\d{4}-\d{2}-\d{2})@", event).group(1)
        location = get_meeting_location(datetime.strptime(date, "%Y-%m-%d"))
        # LOCATION ist ICS-escaped (Komma), Vergleich also am ersten Wort genug
        assert f"LOCATION:{location.split(',')[0]}" in event
        if location != "DVS AG, Schanzenstraße 30, 51063 Köln":
            found_deviation = True
    # Stellt sicher, dass der Test ueberhaupt einen Ausweichtermin prueft
    # (im Bestand der uebernaechste Termin) und nicht nur zufaellig passt.
    assert found_deviation
