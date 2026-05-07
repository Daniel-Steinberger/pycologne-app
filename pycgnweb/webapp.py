#!/usr/bin/env python
"""A Flask-based webapp for the homepage of the pyCologne Python user group."""

import argparse
import inspect
import os
import sys
import textwrap
from datetime import datetime
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from typing import Any, cast

from babel.dates import format_datetime
from flask import Flask, Response, abort, render_template, request, url_for
from markdown_it import MarkdownIt
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer

from .config import DATE_FORMAT_LONG, MEETUP_URL, REPO_URL
from .events import meeting_dates
from .sayings import get_saying

app = Flask(__name__.split(".")[0])

# Quellcode der Terminberechnung: per inspect zur Render-Zeit aus events.py
# gelesen — wenn der Code dort geaendert wird, aktualisiert sich auch die
# auf der Termine-Seite gezeigte Variante. Pygments rendert das Markup
# einmal, light/dark wird per CSS umgeschaltet.
_MEETING_SOURCE = textwrap.dedent(inspect.getsource(meeting_dates))
_PY_LEXER = PythonLexer()
_PY_FORMATTER = HtmlFormatter(cssclass="highlight")
PYGMENTS_CSS_LIGHT = HtmlFormatter(style="default").get_style_defs(".highlight")
PYGMENTS_CSS_DARK = HtmlFormatter(style="monokai").get_style_defs(".highlight")


def _pkg_version(name: str) -> str:
    """Return installed package version, or 'n/a' if not found."""
    try:
        return version(name)
    except PackageNotFoundError:
        return "n/a"


@app.context_processor
def inject_runtime() -> dict[str, dict[str, str]]:
    """Make Python/Flask/Library versions available in every template."""
    return {
        "runtime": {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "flask": _pkg_version("flask"),
            "markdown_it": _pkg_version("markdown-it-py"),
            "babel": _pkg_version("babel"),
        }
    }


@app.context_processor
def inject_code_reveal() -> dict[str, str]:
    """Provide the live source of meeting_dates(), highlighted for both themes."""
    return {
        "meeting_source": cast(str, highlight(_MEETING_SOURCE, _PY_LEXER, _PY_FORMATTER)),
        "pygments_css_light": PYGMENTS_CSS_LIGHT,
        "pygments_css_dark": PYGMENTS_CSS_DARK,
    }


# Markdown-Parser. html=True erlaubt Inline-HTML in den .md-Quellen (z.B. das
# Leaflet-Karten-Snippet auf /join); Quelle der .md-Dateien sind ausschliesslich
# Maintainer-Commits, daher kein XSS-Risiko, vgl. README.
_md = MarkdownIt("commonmark", {"html": True, "linkify": True}).enable(["table", "strikethrough"])


def get_urls() -> dict[str, str]:
    """Return a dictionary with fixed (external) URLs."""
    return {
        "repo": REPO_URL,
        "meetup": MEETUP_URL,
    }


def get_content(filename: str) -> str:
    """Read Markdown document from file and return it as a HTML string.

    If the file does not exist, returns an empty string.
    """
    if not os.path.isfile(filename):
        return ""

    with open(filename, encoding="utf-8") as file_:
        md_data = file_.read()

    return cast(str, _md.render(md_data))


def get_template(*args: str) -> str:
    """Return contents of the given template as a unicode string.

    The path name components are interpreted as being relative to the
    template directory. The contents are expected to be UTF-8 encoded.
    """
    return get_content(os.path.join(app.template_folder or "", *args))


def get_topmenue() -> list[tuple[str, str]]:
    """Return top-level menu structure as a list of (urlpath, label) tuples."""
    return [
        ("/", "Startseite"),
        ("/about", "Die User Group"),
        ("/join", "Mitmachen"),
        ("/events", "Termine"),
        ("/contact", "Kontakt"),
    ]


def ensure_next_meeting(next_date: datetime) -> bool:
    """Ensure that a Markdown file for the next meeting is present.

    TODO: side-effect-laden — schreibt Daten in den Templates-Ordner.
    Sollte in einen separaten data/-Pfad oder Cache wandern.
    """
    path = os.path.join(
        app.template_folder or "",
        "md",
        "events",
        f"{next_date:%Y-%m-%d}.md",
    )
    if os.path.isfile(path):
        return True

    with open(path, "w+", encoding="utf-8") as meeting:
        meeting.write(
            f"""# PyCologne Treffen {next_date:%B %Y}

**Datum:** Mi, {next_date:%d.%m.%Y}, 19:00 Uhr
**Ort:** DVS AG, Schanzenstraße 30, 51063 Köln ([Anfahrt](/join))

Das Programm für dieses Treffen steht noch nicht fest.

**Wir suchen Themen!** Wenn Du einen Vortrag halten, eine Demo zeigen
oder einen Programmpunkt anmelden möchtest, melde Dich gerne. Auch für
spontane Buch- oder Tool-Vorstellungen, Fragen und Coding-Ankündigungen
ist Platz — bring einfach mit, was Dich gerade beschäftigt.

Anmeldung läuft unverbindlich und kostenlos über
[Meetup](https://www.meetup.com/pycologne/).
"""
        )
    return True


app.jinja_env.globals.update(get_topmenue=get_topmenue)


def render_content(page: str, content: str, **kw: Any) -> str:
    """Render page with given name and content with content template."""
    return render_template("/content.html", act=page, content=content, urls=get_urls(), **kw)


# main page
@app.route("/")
@app.route("/index")
def index() -> str:
    """Serve main index page."""
    saying, author = get_saying()
    # get dates for next twelve user group meetings
    meetings = meeting_dates()
    next_meeting = next(meetings)
    # curry date formatting function
    format_date = partial(format_datetime, format=DATE_FORMAT_LONG, locale="DE")

    return render_template(
        "/index.html",
        urls=get_urls(),
        act="",
        next_meeting=next_meeting,
        format_date=format_date,
        saying=saying,
        author=author,
    )


# sub pages
@app.route("/about")
def about() -> str:
    """Return about page."""
    content = get_template("md", "about.md")
    return render_content("about", content)


@app.route("/join")
def join() -> str:
    """Return join page."""
    content = get_template("md", "join.md")
    return render_content("join", content)


@app.route("/events")
def events() -> str:
    """Serve events page with list of upcoming meetings."""
    # get dates for next twelve user group meetings
    meetings = meeting_dates()
    next_meeting = next(meetings)
    # get manually added extra events from Markdown file
    events_ = get_template("md", "events.md")
    # curry date formatting function
    format_date = partial(format_datetime, format=DATE_FORMAT_LONG, locale="DE")

    next_meeting_url = f"/events/{next_meeting:%Y-%m-%d}"
    ensure_next_meeting(next_meeting)
    return render_template(
        "/events.html",
        act="events",
        meetings=meetings,
        next_meeting=next_meeting,
        next_meeting_url=next_meeting_url,
        events=events_,
        format_date=format_date,
    )


@app.route("/events/<date>")
def events_date(date: str) -> str:
    """Serve an event page for a specific meeting."""
    content = get_template("md", "events", f"{date}.md")
    if content == "":
        abort(404)
    return render_content("event", content)


@app.route("/contact")
def contact() -> str:
    """Return contact page."""
    content = get_template("md", "contact.md")
    return render_content("contact", content)


@app.errorhandler(404)
def page_not_found(_err: Exception) -> tuple[str, int]:
    """Default error handler. Serve error page for 404 responses."""
    msg = "Seite nicht gefunden"
    info = (
        f"Die angeforderte URL ({request.url}) existiert nicht "
        "oder ist nicht mehr verfügbar."
    )
    return render_template("404.html", msg=msg, info=info), 404


def _ics_escape(text: str) -> str:
    """Escape special chars per RFC 5545 (LOCATION/DESCRIPTION values)."""
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


@app.route("/events.ics")
def events_feed() -> Response:
    """iCalendar-Feed mit den naechsten zwoelf Treffen.

    Standard-iCalendar-Format (RFC 5545), CRLF-Zeilenumbrueche,
    Europe/Berlin-Wallclock-Zeiten. Subscription-fertig fuer Apple
    Calendar, Google Calendar oder Thunderbird.
    """
    from datetime import UTC, datetime, timedelta

    location = _ics_escape("DVS AG, Schanzenstraße 30, 51063 Köln")
    description = _ics_escape(
        "Monatliches Treffen der Python User Group Köln. "
        "Programm und Anmeldung über https://www.meetup.com/pycologne/"
    )
    now_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PyCologne//pycologne.de//DE",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:PyCologne Treffen",
        "X-WR-TIMEZONE:Europe/Berlin",
    ]

    for date in meeting_dates(count=12):
        end = date + timedelta(hours=2)
        event_url = url_for("events_date", date=date.strftime("%Y-%m-%d"), _external=True)
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:meeting-{date:%Y-%m-%d}@pycologne.de",
                f"DTSTAMP:{now_stamp}",
                f"DTSTART;TZID=Europe/Berlin:{date:%Y%m%dT%H%M%S}",
                f"DTEND;TZID=Europe/Berlin:{end:%Y%m%dT%H%M%S}",
                "SUMMARY:PyCologne Treffen",
                f"LOCATION:{location}",
                f"DESCRIPTION:{description}",
                f"URL:{event_url}",
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    body = "\r\n".join(lines) + "\r\n"
    return Response(body, mimetype="text/calendar")


def main() -> None:
    """Main command line script entry point for the development server."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Run server in debug mode (default: %(default)s).",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Hostname/IP address to bind server to (default: %(default)s).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5014,
        help="Port number to bind server to (default: %(default)s).",
    )
    parser.add_argument(
        "--static-folder",
        default=os.path.join(os.getcwd(), "static"),
        help="Path to web server static files (default: %(default)s).",
    )
    parser.add_argument(
        "--template-folder",
        default=os.path.join(os.getcwd(), "templates"),
        help="Path to HTML and Markdown templates (default: %(default)s).",
    )
    args = parser.parse_args()

    app.static_folder = args.static_folder
    app.template_folder = args.template_folder

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
