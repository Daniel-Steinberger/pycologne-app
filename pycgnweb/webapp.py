#!/usr/bin/env python
"""A Flask-based webapp for the homepage of the pyCologne Python user group."""

import argparse
import inspect
import os
import re
import sys
import textwrap
from datetime import datetime
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from typing import Any, cast

from babel.dates import format_datetime
from flask import Flask, Response, abort, render_template, request, send_from_directory, url_for
from markdown_it import MarkdownIt
from markupsafe import Markup, escape
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer

from .config import DATE_FORMAT_LONG, MEETUP_URL, REPO_URL
from .events import meeting_dates
from .sayings import get_saying
from .search import HIGHLIGHT_CLOSE, HIGHLIGHT_OPEN, ProtocolIndex

app = Flask(__name__.split(".")[0])

# Quellcode-Snippets per inspect zur Render-Zeit aus den jeweiligen Modulen
# gelesen — wenn der Code dort geaendert wird, aktualisiert sich automatisch
# auch die auf der Webseite gezeigte Variante. Pygments rendert das Markup
# einmal; light/dark wird per CSS umgeschaltet.
_MEETING_SOURCE = textwrap.dedent(inspect.getsource(meeting_dates))
_SAYING_SOURCE = textwrap.dedent(inspect.getsource(get_saying))
_PY_LEXER = PythonLexer()
_PY_FORMATTER = HtmlFormatter(cssclass="highlight")
PYGMENTS_CSS_LIGHT = HtmlFormatter(style="default").get_style_defs(".highlight")
PYGMENTS_CSS_DARK = HtmlFormatter(style="monokai").get_style_defs(".highlight")


def _hl(source: str) -> str:
    """Render Python source via Pygments to highlighted HTML."""
    return cast(str, highlight(source, _PY_LEXER, _PY_FORMATTER))


HIGHLIGHTED_MEETING_SOURCE = _hl(_MEETING_SOURCE)
HIGHLIGHTED_SAYING_SOURCE = _hl(_SAYING_SOURCE)


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
    """Provide highlighted live source plus Pygments style defs."""
    return {
        "meeting_source": HIGHLIGHTED_MEETING_SOURCE,
        "pygments_css_light": PYGMENTS_CSS_LIGHT,
        "pygments_css_dark": PYGMENTS_CSS_DARK,
    }


# Markdown-Parser. html=True erlaubt Inline-HTML in den .md-Quellen (z.B. das
# Leaflet-Karten-Snippet auf /join); Quelle der .md-Dateien sind ausschliesslich
# Maintainer-Commits, daher kein XSS-Risiko, vgl. README.
#
# linkify verlangt zweierlei: die Option (unten) und die gleichnamige Regel,
# die das commonmark-Preset deaktiviert laesst. Dazu das Paket linkify-it-py,
# das als Extra von markdown-it-py in den Abhaengigkeiten steht. Fehlt es,
# bleibt die Regel wirkungslos, statt einen Fehler zu werfen; die Adressen in
# den Protokollen sind deshalb zusaetzlich explizit als Links ausgezeichnet.
_md = MarkdownIt("commonmark", {"html": True, "linkify": True}).enable(
    ["table", "strikethrough", "linkify"]
)


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


# Platzhalter-Satz aus ensure_next_meeting — steht er (ohne Protokoll-
# Abschnitte) in einer Termin-Datei, gibt es noch kein Protokoll.
_DEFAULT_PROGRAM_NOTE = "Das Programm für dieses Treffen steht noch nicht fest."

# So viele vergangene Treffen stehen auf /events einzeln untereinander,
# der Rest wird nach Jahrgang gruppiert.
RECENT_MEETINGS = 3


def _protocol_topics(md_text: str) -> list[str]:
    """Extract topic headings from a meeting protocol.

    Neuere Protokolle gliedern die Zusammenfassung in '###'-Abschnitte
    (mit Nummerierungs-Praefix), aeltere listen das Programm als
    Aufzaehlung unter '## Programm'.
    """
    lines = md_text.splitlines()
    topics = [
        re.sub(r"^\d+\.\s*", "", line.removeprefix("### ").strip())
        for line in lines
        if line.startswith("### ")
    ]
    if topics:
        return topics
    in_program = False
    for line in lines:
        if line.startswith("## "):
            in_program = line.removeprefix("## ").strip().lower() == "programm"
        elif in_program and line.startswith("- "):
            topics.append(line.removeprefix("- ").strip())
    return topics


def _protocol_teaser(md_text: str) -> Markup:
    """Return the first body paragraph of a meeting file, as rendered HTML.

    Ueberschriften, die fettgedruckten Datum/Ort-Zeilen und der immer
    gleiche Schlussteil ("Wir suchen Themen!" ff.) werden uebersprungen;
    umgebrochene Absatzzeilen werden wieder zusammengefuegt. Besteht die
    Datei nur aus dem Default-Platzhalter, kommt '' zurueck. Das Ergebnis
    ist inline-gerendertes Markdown (Fett/Kursiv/Links bleiben erhalten),
    damit es in den Templates nicht als rohes '**...**' auftaucht.
    """
    body = md_text.split("**Wir suchen Themen!**")[0]
    paragraph: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "**")):
            if paragraph:
                break
            continue
        if stripped == _DEFAULT_PROGRAM_NOTE:
            return Markup("")
        paragraph.append(stripped)
    # Markdown-Quelle stammt ausschliesslich aus Maintainer-Commits, kein
    # XSS-Risiko, vgl. Kommentar bei der _md-Definition weiter oben.
    return Markup(_md.renderInline(" ".join(paragraph)))  # noqa: S704


# Ergebnis-Cache fuer die Protokoll-Uebersicht. Ohne ihn liest jeder Aufruf
# von /events jede Protokolldatei komplett; mit dem Archiv ab 2013 sind das
# ueber neunzig Dateien pro Seitenaufruf. Der Schluessel enthaelt den Zustand
# des Verzeichnisses, eine geaenderte oder neue Datei laeuft also nicht in
# einen veralteten Cache.
_past_meetings_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}


def _events_dir_state(events_dir: str) -> tuple[tuple[str, int], ...]:
    """Fingerabdruck des Termin-Verzeichnisses (Dateiname und mtime)."""
    return tuple(
        sorted(
            (entry.name, entry.stat().st_mtime_ns)
            for entry in os.scandir(events_dir)
            if entry.name.endswith(".md")
        )
    )


def get_past_meetings(reference: datetime) -> list[dict[str, Any]]:
    """Return past meetings that have a Markdown file, newest first.

    Scannt templates/md/events/ nach datumsbenannten Dateien vor
    *reference* und liefert je Treffen einen Inhaltshinweis: die
    Themen-Ueberschriften des Protokolls ('topics') oder ersatzweise die
    erste Textzeile ('teaser'); beides leer, wenn nur der
    Default-Platzhalter drinsteht.

    Das Ergebnis wird gecacht, solange sich weder das Verzeichnis noch der
    Bezugstag aendert.
    """
    events_dir = os.path.join(app.template_folder or "", "md", "events")
    if not os.path.isdir(events_dir):
        return []

    cache_key = (_events_dir_state(events_dir), reference.date())
    cached = _past_meetings_cache.get(cache_key)
    if cached is not None:
        return cached

    meetings = []
    # ISO-Datumsnamen: absteigende Dateinamen == absteigende Daten
    for name in sorted(os.listdir(events_dir), reverse=True):
        stem, ext = os.path.splitext(name)
        if ext != ".md":
            continue
        try:
            # Treffen beginnen immer um 19:00 (vgl. events.meeting_dates);
            # der Dateiname enthaelt nur das Datum.
            date = datetime.strptime(stem, "%Y-%m-%d").replace(hour=19)
        except ValueError:
            continue
        if date.date() >= reference.date():
            continue
        with open(os.path.join(events_dir, name), encoding="utf-8") as file_:
            md_text = file_.read()
        topics = _protocol_topics(md_text)
        meetings.append(
            {
                "date": date,
                "url": f"/events/{stem}",
                "topics": topics,
                "teaser": "" if topics else _protocol_teaser(md_text),
            }
        )
    # Nur der aktuelle Verzeichniszustand ist interessant; alte Eintraege
    # wuerden den Cache mit jeder Aenderung weiter aufblaehen.
    _past_meetings_cache.clear()
    _past_meetings_cache[cache_key] = meetings
    return meetings


def group_meetings_by_year(
    meetings: list[dict[str, Any]],
) -> list[tuple[int, list[dict[str, Any]]]]:
    """Gruppiere Treffen nach Jahr, neuestes Jahr zuerst.

    Die Termine-Seite zeigt damit pro Jahrgang einen aufklappbaren Block,
    statt alle Protokolle seit 2013 in eine Liste zu schuetten.
    """
    grouped: dict[int, list[dict[str, Any]]] = {}
    for meeting in meetings:
        grouped.setdefault(meeting["date"].year, []).append(meeting)
    return sorted(grouped.items(), reverse=True)


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


def get_next_meeting_teaser(next_date: datetime) -> Markup:
    """Return a short teaser for the next meeting's program, if known.

    Reads the same Markdown file that ensure_next_meeting writes to;
    returns '' if the file does not exist yet or only contains the
    default placeholder (no program announced yet).
    """
    path = os.path.join(
        app.template_folder or "",
        "md",
        "events",
        f"{next_date:%Y-%m-%d}.md",
    )
    if not os.path.isfile(path):
        return Markup("")
    with open(path, encoding="utf-8") as file_:
        return _protocol_teaser(file_.read())


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
        next_meeting_teaser=get_next_meeting_teaser(next_meeting),
        format_date=format_date,
        saying=saying,
        author=author,
    )


# sub pages
@app.route("/about")
def about() -> str:
    """Return about page."""
    content = get_template("md", "about.md")
    return render_content(
        "about",
        content,
        code_block=HIGHLIGHTED_SAYING_SOURCE,
        code_caption="Zitate-Generator (live)",
        code_explainer=(
            "Das Zen-Zitat auf der Startseite kommt aus dieser Funktion in "
            "<code>pycgnweb/sayings.py</code> — bei jedem Aufruf wird ein "
            "Spruch aus der Liste gelost."
        ),
    )


@app.route("/join")
def join() -> str:
    """Return join page."""
    return render_template(
        "join.html",
        act="join",
        urls=get_urls(),
    )


@app.route("/events")
def events() -> str:
    """Serve events page with list of upcoming meetings."""
    # eines fuer den Hero, sechs fuer die Terminvorschau
    meetings = meeting_dates(count=7)
    next_meeting = next(meetings)
    # get manually added extra events from Markdown file
    events_ = get_template("md", "events.md")
    # curry date formatting function
    format_date = partial(format_datetime, format=DATE_FORMAT_LONG, locale="DE")

    next_meeting_url = f"/events/{next_meeting:%Y-%m-%d}"
    ensure_next_meeting(next_meeting)
    # Die jüngsten Treffen stehen einzeln, alles Ältere nach Jahrgang
    # gruppiert darunter.
    past_meetings = get_past_meetings(datetime.now())
    return render_template(
        "/events.html",
        act="events",
        meetings=meetings,
        next_meeting=next_meeting,
        next_meeting_url=next_meeting_url,
        next_meeting_teaser=get_next_meeting_teaser(next_meeting),
        past_meetings=past_meetings[:RECENT_MEETINGS],
        past_by_year=group_meetings_by_year(past_meetings[RECENT_MEETINGS:]),
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


@app.route("/favicon.ico")
def favicon() -> Response:
    """Serve favicon.ico from the static folder for the browser's default request."""
    return send_from_directory(
        app.static_folder or "", "favicon.ico", mimetype="image/vnd.microsoft.icon"
    )


@app.route("/contact")
def contact() -> str:
    """Return contact page."""
    content = get_template("md", "contact.md")
    return render_content("contact", content)


# Der Index haelt seine Daten im Speicher und baut sich neu, sobald sich im
# Protokollverzeichnis etwas aendert; er wird beim ersten Suchaufruf gefuellt.
_protocol_index: ProtocolIndex | None = None


def _index() -> ProtocolIndex:
    """Den Protokoll-Index liefern, passend zum aktuellen Template-Ordner."""
    global _protocol_index  # noqa: PLW0603
    events_dir = os.path.join(app.template_folder or "", "md", "events")
    if _protocol_index is None or _protocol_index.events_dir != events_dir:
        _protocol_index = ProtocolIndex(events_dir)
    return _protocol_index


def _highlight(excerpt: str) -> Markup:
    """Trefferausschnitt sicher als HTML aufbereiten.

    Erst escapen, dann die Marker aus der Suche zu <mark> machen: So kann
    aus dem Protokolltext kein Markup in die Seite gelangen.
    """
    # escape() liefert Markup; dessen replace() escapet das Argument, ein
    # bereits als Markup markiertes Tag also nicht. Damit bleibt der
    # Protokolltext escaped und nur die Marker werden zu echtem HTML.
    return (
        escape(excerpt)
        .replace(HIGHLIGHT_OPEN, Markup("<mark>"))
        .replace(HIGHLIGHT_CLOSE, Markup("</mark>"))
    )


@app.route("/suche")
def search() -> str:
    """Volltextsuche ueber die Protokolle vergangener Treffen."""
    query = request.args.get("q", "").strip()
    results = _index().search(query) if query else []
    format_date = partial(format_datetime, format=DATE_FORMAT_LONG, locale="DE")
    return render_template(
        "search.html",
        act="search",
        urls=get_urls(),
        query=query,
        results=results,
        highlight=_highlight,
        format_date=format_date,
    )


@app.errorhandler(404)
def page_not_found(_err: Exception) -> tuple[str, int]:
    """Default error handler. Serve error page for 404 responses."""
    msg = "Seite nicht gefunden"
    info = f"Die angeforderte URL ({request.url}) existiert nicht oder ist nicht mehr verfügbar."
    return render_template("404.html", msg=msg, info=info), 404


def _ics_escape(text: str) -> str:
    """Escape special chars per RFC 5545 (LOCATION/DESCRIPTION values)."""
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


def _ics_fold(line: str) -> str:
    """Fold a content line to 75 octets per RFC 5545, section 3.1.

    Fortsetzungszeilen beginnen mit einem Leerzeichen, das selbst als
    Oktett zaehlt. Gefaltet wird an Zeichen-, nicht an Byte-Grenzen,
    damit Umlaute nicht mitten in der UTF-8-Sequenz zerreissen.
    """
    parts: list[str] = []
    current = ""
    used = 0
    for char in line:
        size = len(char.encode("utf-8"))
        if used + size > 75:
            parts.append(current)
            current = ""
            used = 1  # das fuehrende Leerzeichen der Fortsetzungszeile
        current += char
        used += size
    parts.append(current)
    return "\r\n ".join(parts)


@app.route("/events.ics")
def events_feed() -> Response:
    """iCalendar-Feed mit den naechsten zwoelf Treffen.

    Standard-iCalendar-Format (RFC 5545), CRLF-Zeilenumbrueche,
    Europe/Berlin-Wallclock-Zeiten. Subscription-fertig fuer Apple
    Calendar, Google Calendar oder Thunderbird.
    """
    from datetime import UTC, datetime, timedelta

    location = _ics_escape("DVS AG, Schanzenstraße 30, 51063 Köln")
    boilerplate = (
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
        # Steht das Programm schon in der Termin-Datei, kommt es vor den
        # immer gleichen Hinweistext — Abonnenten sehen das Thema direkt
        # im Kalendereintrag.
        teaser = get_next_meeting_teaser(date)
        description = _ics_escape(f"{teaser}\n\n{boilerplate}" if teaser else boilerplate)
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
    body = "\r\n".join(_ics_fold(line) for line in lines) + "\r\n"
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
