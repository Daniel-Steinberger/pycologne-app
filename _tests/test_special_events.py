"""Sonderveranstaltungen: Termine mit eigener Datei abseits der regulaeren Mittwoche.

Vorschau, Kalender-Abo und Link-Vorschau kannten frueher nur die errechneten
Treffen. Eine Datei fuer einen anderen Tag war zwar als Seite erreichbar,
tauchte aber sonst nirgends auf.
"""

import os
import re
from datetime import timedelta

import pytest
from babel.dates import format_datetime

from _tests.conftest import SPECIAL_TITLE
from pycgnweb.config import DATE_FORMAT_LONG
from pycgnweb.webapp import _event_start, app, get_special_events, upcoming_events


@pytest.fixture
def client(template_root):
    """Flask-Test-Client auf dem Inhaltsbestand der Tests."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return app.test_client()


def _ics_events(client):
    body = client.get("/events.ics").get_data(as_text=True)
    return body.replace("\r\n ", "").split("BEGIN:VEVENT")[1:]


def test_special_event_is_found_with_its_own_start(client, special_day):
    """Datum aus dem Dateinamen, Uhrzeit aus der Datum-Zeile, Titel aus der Ueberschrift."""
    with app.app_context():
        specials = get_special_events(special_day - timedelta(days=1))
    assert [event.title for event in specials] == [SPECIAL_TITLE]
    assert specials[0].start == special_day
    assert specials[0].url == f"/events/{special_day:%Y-%m-%d}"
    assert specials[0].special


def test_regular_meeting_with_a_file_is_not_special(client, upcoming, special_day):
    """Auch der naechste Mittwoch hat eine Datei, bleibt aber ein normales Treffen."""
    with app.app_context():
        specials = get_special_events(upcoming[0] - timedelta(days=1))
    assert all(event.start.date() != upcoming[0].date() for event in specials)


def test_past_special_event_drops_out(client, special_day):
    """Ist der Tag vorbei, gehoert die Veranstaltung nicht mehr in die Vorschau."""
    with app.app_context():
        assert get_special_events(special_day + timedelta(days=1)) == []


def test_upcoming_events_are_sorted_and_keep_all_meetings(client, upcoming, special_day):
    """Die regulaeren Treffen bleiben vollstaendig, die Sonderveranstaltung steht dazwischen."""
    with app.app_context():
        events = upcoming_events()
    starts = [event.start for event in events]
    assert starts == sorted(starts)
    assert [event.start for event in events if not event.special] == upcoming[:7]
    assert [event.start for event in events if event.special] == [special_day]


def test_start_falls_back_to_seven_pm(special_day):
    """Ohne Uhrzeit in der Datum-Zeile gilt 19:00, wie bei den Treffen."""
    day = special_day.replace(hour=0)
    assert _event_start(day, "# Titel\n\n**Datum:** Do, irgendwann\n").hour == 19
    assert _event_start(day, "# Titel ohne Datum-Zeile\n").hour == 19


def test_preview_shows_special_event_highlighted_and_linked(client, special_day):
    """In der Terminvorschau: hervorgehoben, verlinkt und mit der echten Uhrzeit."""
    html = client.get("/events").get_data(as_text=True)
    assert "upcoming-list__item--special" in html
    assert f'href="/events/{special_day:%Y-%m-%d}"' in html
    assert SPECIAL_TITLE in html
    assert format_datetime(special_day, format=DATE_FORMAT_LONG, locale="DE") in html


def test_hero_stays_with_the_next_regular_meeting(client, upcoming):
    """Die Karte 'Naechstes Treffen' zeigt weiter den naechsten Mittwoch."""
    html = client.get("/events").get_data(as_text=True)
    hero = html.split("event-next")[1].split("event-upcoming")[0]
    assert format_datetime(upcoming[0], format=DATE_FORMAT_LONG, locale="DE") in hero
    assert SPECIAL_TITLE not in hero


def test_ics_carries_special_event(client, special_day):
    """Eigener Eintrag: eigene UID-Form, echte Startzeit, drei Stunden, Titel und Ort."""
    events = [event for event in _ics_events(client) if "UID:event-" in event]
    assert len(events) == 1
    event = events[0]
    assert f"UID:event-{special_day:%Y-%m-%d}@pycologne.de" in event
    assert f"DTSTART;TZID=Europe/Berlin:{special_day:%Y%m%dT%H%M%S}" in event
    end = special_day + timedelta(hours=3)
    assert f"DTEND;TZID=Europe/Berlin:{end:%Y%m%dT%H%M%S}" in event
    assert f"SUMMARY:{SPECIAL_TITLE}" in event
    # Der harte Zeilenumbruch am Ende der Ort-Zeile gehoert nicht zum Ort
    location = re.search(r"LOCATION:(.*)", event).group(1).strip()
    assert location.endswith("Arena One")
    assert "Monatliches Treffen" not in event


def test_ics_keeps_regular_meetings(client, upcoming):
    """Die zwoelf regulaeren Treffen stehen unveraendert im Feed."""
    uids = re.findall(r"UID:meeting-(\d{4}-\d{2}-\d{2})@", "".join(_ics_events(client)))
    assert uids == [f"{day:%Y-%m-%d}" for day in upcoming[:12]]


def test_event_page_has_its_own_link_preview(client, special_day):
    """Geteilt zeigt die Terminseite ihren Titel statt nur 'PyCologne'."""
    html = client.get(f"/events/{special_day:%Y-%m-%d}").get_data(as_text=True)
    assert f'<meta property="og:title" content="{SPECIAL_TITLE}">' in html
