"""Smoke-Tests fuer HTTP-Status aller Routen via Flask-Test-Client."""

import os
import re
from datetime import datetime

import pytest

from pycgnweb.webapp import (
    app,
    get_next_meeting_teaser,
    get_past_meetings,
    group_meetings_by_year,
)


@pytest.fixture
def client():
    """Flask-Test-Client mit Pfaden auf das Repo-Root konfiguriert."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = os.path.join(os.getcwd(), "templates")
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
    assert 'href="/events/2026-07-08"' in html


def test_past_event_page_returns_ok(client):
    """Protokollseiten vergangener Treffen muessen erreichbar sein."""
    response = client.get("/events/2026-07-08")
    assert response.status_code == 200


def test_get_past_meetings_metadata(client):  # pylint: disable=unused-argument
    """get_past_meetings liefert Daten absteigend samt Inhaltshinweisen.

    Die client-Fixture wird nur gebraucht, um app.template_folder auf das
    Repo-Root zu setzen.
    """
    meetings = get_past_meetings(datetime(2026, 7, 9))

    dates = [meeting["date"] for meeting in meetings]
    assert dates == sorted(dates, reverse=True)
    # Treffen finden um 19:00 statt, nicht um Mitternacht
    assert all(date.hour == 19 for date in dates)

    by_url = {meeting["url"]: meeting for meeting in meetings}
    # zukuenftige Termine tauchen nicht in der Vergangenheitsliste auf
    assert "/events/2026-08-12" not in by_url
    # Protokoll mit Zusammenfassung: ###-Ueberschriften als Themen
    assert any("HPC" in topic for topic in by_url["/events/2026-07-08"]["topics"])
    # Datei ohne Protokoll-Abschnitte: erste Textzeile als Teaser
    assert by_url["/events/2026-06-10"]["teaser"].startswith("Da Daniel")
    # altes Protokoll mit Programmliste
    assert by_url["/events/2017-08-09"]["topics"]


def test_group_meetings_by_year(client):  # pylint: disable=unused-argument
    """Die Gruppierung liefert Jahrgaenge absteigend, Treffen darin ebenso."""
    meetings = get_past_meetings(datetime(2026, 7, 9))
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
    reference = datetime(2026, 7, 9)
    first = get_past_meetings(reference)
    second = get_past_meetings(reference)
    assert first is second


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
    for event in unfolded.split("BEGIN:VEVENT")[1:]:
        date = re.search(r"UID:meeting-(\d{4}-\d{2}-\d{2})@", event).group(1)
        teaser = get_next_meeting_teaser(datetime.strptime(date, "%Y-%m-%d"))
        if teaser:
            # erstes Wort genuegt: der Rest ist ICS-escaped
            assert teaser.split(",")[0] in event
        # der allgemeine Hinweistext bleibt in jedem Fall erhalten
        assert "Monatliches Treffen der Python User Group" in event
