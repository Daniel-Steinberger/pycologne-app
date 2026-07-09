"""Smoke-Tests fuer HTTP-Status aller Routen via Flask-Test-Client."""

import os
from datetime import datetime

import pytest

from pycgnweb.webapp import app, get_past_meetings


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
