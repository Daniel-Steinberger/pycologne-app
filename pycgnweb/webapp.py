#!/usr/bin/env python
"""A Flask-based webapp for the homepage of the pyCologne Python user group."""

import argparse
import hashlib
import hmac
import inspect
import os
import re
import sys
import textwrap
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache, partial
from importlib.metadata import PackageNotFoundError, version
from typing import Any, cast
from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import quoteattr

from babel.dates import format_datetime
from flask import Flask, Response, abort, render_template, request, send_from_directory, url_for
from markdown_it import MarkdownIt
from markupsafe import Markup, escape
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers.python import PythonLexer

from .config import (
    CONTENT_REPO_URL,
    CONTENT_TRIGGER_FILE,
    DATE_FORMAT_DAY,
    DATE_FORMAT_LONG,
    MEETUP_URL,
    OG_IMAGE,
    REPO_URL,
    SITE_DESCRIPTION,
    WEBHOOK_SECRET_FILE,
    WEBSITE_URL,
)
from .events import meeting_dates
from .matrixstyle import MatrixStyle
from .sayings import get_saying
from .search import HIGHLIGHT_CLOSE, HIGHLIGHT_OPEN, ProtocolIndex, build_query, first_heading

app = Flask(__name__.split(".")[0])

# Quellcode der Flip-Kacheln, per inspect zur Laufzeit aus den jeweiligen
# Modulen gelesen. Wenn der Code dort geaendert wird, aktualisiert sich
# automatisch auch die auf der Webseite gezeigte Variante. Gerendert wird
# mit dem eigenen Matrix-Stil, die Rueckseiten sind themenfest gruen.
_PY_LEXER = PythonLexer()
_MX_FORMATTER = HtmlFormatter(style=MatrixStyle, cssclass="mx-highlight")
PYGMENTS_CSS_MATRIX = _MX_FORMATTER.get_style_defs(".mx-highlight")


def _make_reveal(func: Callable[..., Any]) -> dict[str, str]:
    """Beschreibe eine Funktion fuer die Rueckseite einer Flip-Kachel.

    Liefert Modulpfad (fuer die Terminal-Kopfzeile), GitHub-Link mit
    Zeilenanker (der No-JS-Fallback des Griffs) und den gehighlighteten
    Quelltext.
    """
    source = textwrap.dedent(inspect.getsource(func))
    lineno = inspect.getsourcelines(func)[1]
    filename = os.path.basename(inspect.getsourcefile(func) or "")
    path = f"pycgnweb/{filename}"
    return {
        "path": path,
        "github": f"{REPO_URL}/blob/main/{path}#L{lineno}",
        "html": cast(str, highlight(source, _PY_LEXER, _MX_FORMATTER)),
    }


@lru_cache(maxsize=1)
def get_code_reveals() -> dict[str, dict[str, str]]:
    """Das Register der Flip-Kacheln: Kennung zu Rueckseite.

    Bewusst lazy (erster Request statt Importzeit), weil _ics_fold weiter
    unten in diesem Modul definiert ist.
    """
    return {
        "meeting": _make_reveal(meeting_dates),
        "saying": _make_reveal(get_saying),
        "query": _make_reveal(build_query),
        "ics": _make_reveal(_ics_fold),
    }


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
def inject_code_reveal() -> dict[str, Any]:
    """Provide the flip tile registry plus its Pygments style defs."""
    return {
        "code_reveals": get_code_reveals(),
        "pygments_css_matrix": PYGMENTS_CSS_MATRIX,
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


def _content_root() -> str:
    """Return the root of the content checkout, found via the templates/md link."""
    return os.path.dirname(os.path.realpath(os.path.join(app.template_folder or "", "md")))


def _git_ref_commit(git_dir: str, ref: str) -> str | None:
    """Return the commit a ref points at, from a loose file or packed-refs."""
    try:
        with open(os.path.join(git_dir, ref), encoding="utf-8") as file_:
            return file_.read().strip()
    except OSError:
        pass
    try:
        with open(os.path.join(git_dir, "packed-refs"), encoding="utf-8") as file_:
            for line in file_:
                if line.startswith(("#", "^")):
                    continue
                commit, _, name = line.strip().partition(" ")
                if name == ref:
                    return commit
    except OSError:
        pass
    return None


def content_commit() -> str | None:
    """Return the commit the delivered content sits on, or None.

    Wird direkt aus dem Git-Verzeichnis des Content-Checkouts gelesen, ohne
    Unterprozess: zwei kleine Dateien, das faellt neben dem Rendern einer
    Protokollseite nicht ins Gewicht. Liegen die Inhalte nicht in einem
    Checkout, etwa im Test oder wenn jemand sie von Hand hinlegt, kommt None
    zurueck und die Fusszeile laesst die Angabe weg.
    """
    git_dir = os.path.join(_content_root(), ".git")
    try:
        with open(os.path.join(git_dir, "HEAD"), encoding="utf-8") as file_:
            head = file_.read().strip()
    except OSError:
        return None
    commit = (
        _git_ref_commit(git_dir, head.removeprefix("ref: ").strip())
        if head.startswith("ref: ")
        else head
    )
    if commit is None or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        return None
    return commit


@app.context_processor
def inject_content_version() -> dict[str, str]:
    """Make the content checkout's commit available to the footer."""
    commit = content_commit()
    if commit is None:
        return {"content_commit": "", "content_commit_url": ""}
    return {
        "content_commit": commit[:7],
        "content_commit_url": f"{CONTENT_REPO_URL}/commit/{commit}",
    }


# So lang darf eine Beschreibung fuer die Vorschau werden. Facebook und X
# schneiden laengere selbst ab, dann lieber an einer Wortgrenze.
OG_DESCRIPTION_MAX = 200


def _untag(html: str) -> str:
    """HTML-Tags entfernen, fuer Felder die reinen Text verlangen."""
    return re.sub(r"<[^>]+>", "", html)


def _shorten(text: str, limit: int = OG_DESCRIPTION_MAX) -> str:
    """Text auf *limit* Zeichen kuerzen, an der letzten Wortgrenze davor."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + " …"


@app.context_processor
def inject_open_graph() -> dict[str, str]:
    """Absolute Angaben fuer die Vorschau in sozialen Netzen.

    Facebook und X holen sich diese Werte von aussen und koennen mit
    relativen Pfaden nichts anfangen. Vorangestellt wird bewusst WEBSITE_URL
    und nicht der Host des laufenden Requests: die Vorschau soll auf die
    richtige Adresse zeigen, auch wenn die Seite gerade unter einem anderen
    Namen erreicht wurde.
    """
    return {
        "site_description": SITE_DESCRIPTION,
        "og_url": f"{WEBSITE_URL}{request.path}",
        "og_image": f"{WEBSITE_URL}{OG_IMAGE}",
    }


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
        ("/news", "News"),
        ("/contact", "Kontakt"),
    ]


# Platzhalter-Satz aus meeting_placeholder. Steht er (ohne Protokoll-
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


_ORT_LINE = re.compile(
    r"^\*\*Ort:\*\*\s*(?P<loc>.+?)\s*(?:\(\[[^\]]*\]\([^)]*\)\))?\s*$", re.MULTILINE
)

DEFAULT_LOCATION = "DVS AG, Schanzenstraße 30, 51063 Köln"


def _protocol_location(md_text: str) -> str:
    """Return the plain-text location from a meeting file's '**Ort:**' line.

    Faellt auf DEFAULT_LOCATION zurueck, wenn die Datei keine eigene
    Ort-Zeile hat (z. B. noch nicht angelegt). Damit zeigen Ausweich-Termine
    (z. B. Cologne Game Lab statt DVS AG) auch im ICS-Feed die richtige
    Adresse, statt immer den Standardort zu tragen.
    """
    match = _ORT_LINE.search(md_text)
    if match is None:
        return DEFAULT_LOCATION
    return match.group("loc").strip()


def get_meeting_location(date: datetime) -> str:
    """Return the location for a given meeting date, read from its file if present."""
    return _protocol_location(meeting_markdown(date))


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


def _dir_state(directory: str) -> tuple[tuple[str, int], ...]:
    """Fingerabdruck eines Inhalts-Verzeichnisses (Dateiname und mtime).

    Traegt die Caches der Termin-Uebersicht und der News. Eine geaenderte
    oder neue Datei aendert den Fingerabdruck, ein Abgleich des
    Content-Checkouts ist damit sofort sichtbar, ohne Neustart.
    """
    return tuple(
        sorted(
            (entry.name, entry.stat().st_mtime_ns)
            for entry in os.scandir(directory)
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

    cache_key = (_dir_state(events_dir), reference.date())
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


# News-Eintraege liegen als md/news/JJJJ-MM-TT-slug.md im Content-Repo.
#
# Das Datum steht im Dateinamen und nicht in der Datei, aus demselben Grund
# wie bei den Terminen: nur der Dateiname uebersteht einen frischen Checkout
# unveraendert. Git uebertraegt keine mtimes, ein Sortieren nach Dateizeit
# wuerde die Reihenfolge im Feed also bei jedem Abgleich neu erfinden und in
# den Readern alles erneut als ungelesen zeigen.
_NEWS_SLUG = re.compile(r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*")

# Uhrzeit, mit der ein Eintrag im Atom-Feed steht. Reine Konvention: der
# Dateiname gibt nur den Tag her, Atom verlangt einen vollen Zeitstempel.
# Auf der Seite selbst wird die Uhrzeit nie gezeigt.
NEWS_HOUR = 9

# So viele Eintraege stehen im Feed. Wie beim ICS-Feed bewusst begrenzt,
# damit er nicht mit dem Archiv mitwaechst.
NEWS_FEED_LIMIT = 20

# So viele Eintraege zeigt die Kachel auf der Startseite.
HOME_NEWS = 3

_news_cache: dict[tuple[Any, ...], list[dict[str, Any]]] = {}


def _news_date(stem: str) -> datetime | None:
    """Datum eines News-Dateinamens, oder None wenn er nicht passt.

    Eine Stelle fuer beides, Muster und Datum, damit Uebersicht, Feed und
    Einzelseite nie auseinanderlaufen: eine Datei, die in der Uebersicht
    fehlt, darf auch nicht unter ihrer URL erreichbar sein.
    """
    if _NEWS_SLUG.fullmatch(stem) is None:
        return None
    try:
        return datetime.strptime(stem[:10], "%Y-%m-%d").replace(hour=NEWS_HOUR)
    except ValueError:
        return None


def _news_teaser(md_text: str) -> Markup:
    """Ersten Textabsatz eines News-Eintrags als gerendertes HTML.

    Anders als bei den Protokollen wird nur die Ueberschrift uebersprungen
    (und ein einleitendes Bild): ein News-Absatz darf mit Fettschrift
    beginnen, waehrend die Termin-Dateien an derselben Stelle ihre
    Datum- und Ort-Zeilen tragen, vgl. _protocol_teaser().
    """
    paragraph: list[str] = []
    for line in md_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "!")):
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    # Markdown-Quelle stammt ausschliesslich aus Maintainer-Commits, kein
    # XSS-Risiko, vgl. Kommentar bei der _md-Definition weiter oben.
    return Markup(_md.renderInline(" ".join(paragraph)))  # noqa: S704


def get_news() -> list[dict[str, Any]]:
    """Alle News-Eintraege, neuester zuerst.

    Dateien, deren Name nicht dem Muster JJJJ-MM-TT-slug entspricht, werden
    uebersprungen. Gemeldet werden sie von der Pruefung im Content-Repo, die
    Seite soll daran nicht zerbrechen.

    Gecacht, solange sich im Verzeichnis nichts aendert, analog zu
    get_past_meetings(). Fehlt das Verzeichnis ganz, etwa weil der
    Content-Checkout aelter ist als diese Funktion, kommt eine leere Liste
    zurueck und die Seite bleibt heil.
    """
    news_dir = os.path.join(app.template_folder or "", "md", "news")
    if not os.path.isdir(news_dir):
        return []

    cache_key = (_dir_state(news_dir),)
    cached = _news_cache.get(cache_key)
    if cached is not None:
        return cached

    entries = []
    # ISO-Datum am Anfang: absteigende Dateinamen == absteigende Daten
    for name in sorted(os.listdir(news_dir), reverse=True):
        stem, ext = os.path.splitext(name)
        date = _news_date(stem) if ext == ".md" else None
        if date is None:
            continue
        with open(os.path.join(news_dir, name), encoding="utf-8") as file_:
            md_text = file_.read()
        entries.append(
            {
                "date": date,
                "slug": stem,
                "url": f"/news/{stem}",
                "title": first_heading(md_text, stem),
                "teaser": _news_teaser(md_text),
            }
        )
    # Nur der aktuelle Verzeichniszustand ist interessant, vgl.
    # get_past_meetings().
    _news_cache.clear()
    _news_cache[cache_key] = entries
    return entries


def meeting_placeholder(date: datetime) -> str:
    """Return the Markdown shown for a meeting that has no file yet.

    Frueher legte ``ensure_next_meeting()`` genau diesen Text als Datei im
    Template-Ordner an. Seit die Inhalte aus einem eigenen Repo kommen und
    der Ordner ein Git-Checkout ist, wird dort nicht mehr geschrieben: der
    Platzhalter entsteht beim Rendern und verschwindet von selbst, sobald
    eine echte Termin-Datei da ist.
    """
    month = format_datetime(date, format="MMMM yyyy", locale="DE")
    return f"""# PyCologne Treffen {month}

**Datum:** Mi, {date:%d.%m.%Y}, 19:00 Uhr
**Ort:** {DEFAULT_LOCATION} ([Anfahrt](/join))

{_DEFAULT_PROGRAM_NOTE}

**Wir suchen Themen!** Wenn Du einen Vortrag halten, eine Demo zeigen
oder einen Programmpunkt anmelden möchtest, melde Dich gerne. Auch für
spontane Buch- oder Tool-Vorstellungen, Fragen und Coding-Ankündigungen
ist Platz, bring einfach mit, was Dich gerade beschäftigt.

Anmeldung läuft unverbindlich und kostenlos über
[Meetup](https://www.meetup.com/pycologne/).
"""


def meeting_markdown(date: datetime) -> str:
    """Return a meeting's Markdown source, or the placeholder if it has none."""
    path = os.path.join(
        app.template_folder or "",
        "md",
        "events",
        f"{date:%Y-%m-%d}.md",
    )
    if not os.path.isfile(path):
        return meeting_placeholder(date)
    with open(path, encoding="utf-8") as file_:
        return file_.read()


def get_next_meeting_teaser(next_date: datetime) -> Markup:
    """Return a short teaser for the next meeting's program, if known.

    Liefert '', solange nur der Platzhalter greift, das Programm also noch
    nicht angekuendigt ist.
    """
    return _protocol_teaser(meeting_markdown(next_date))


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
        next_meeting_url=f"/events/{next_meeting:%Y-%m-%d}",
        next_meeting_teaser=get_next_meeting_teaser(next_meeting),
        news_entries=get_news()[:HOME_NEWS],
        format_day=partial(format_datetime, format=DATE_FORMAT_DAY, locale="DE"),
        # Fuer die REPL-Zeilen der Flip-Kacheln: dieselben Werte, die die
        # Vorderseiten zeigen, als Python-repr. Die Rueckseite luegt nie.
        next_meeting_repr=repr(next_meeting),
        saying_repr=repr((saying, author)),
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
        reveal=get_code_reveals()["saying"],
        saying_repr=repr(get_saying()),
        code_caption="Zitate-Generator (live)",
        code_explainer=(
            "Das Zen-Zitat auf der Startseite kommt aus dieser Funktion in "
            "<code>pycgnweb/sayings.py</code>. Bei jedem Aufruf wird ein "
            "Spruch aus der Liste gelost, unten das Ergebnis von gerade eben."
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
        next_meeting_repr=repr(next_meeting),
        past_meetings=past_meetings[:RECENT_MEETINGS],
        past_by_year=group_meetings_by_year(past_meetings[RECENT_MEETINGS:]),
        events=events_,
        format_date=format_date,
    )


@app.route("/events/<date>")
def events_date(date: str) -> str:
    """Serve an event page for a specific meeting.

    Steht fuer einen anstehenden Termin noch keine Datei bereit, kommt der
    Platzhalter statt eines 404. Frueher entstand dafuer beim ersten
    Seitenaufruf eine Datei im Template-Ordner, s. meeting_placeholder().
    """
    content = get_template("md", "events", f"{date}.md")
    if content == "":
        try:
            wanted = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            abort(404)
        upcoming = {meeting.date(): meeting for meeting in meeting_dates(count=12)}
        if wanted not in upcoming:
            abort(404)
        content = cast(str, _md.render(meeting_placeholder(upcoming[wanted])))
    return render_content("event", content)


@app.route("/news")
def news() -> str:
    """Uebersicht der News-Eintraege, neuester zuerst."""
    format_date = partial(format_datetime, format=DATE_FORMAT_DAY, locale="DE")
    return render_template(
        "news.html",
        act="news",
        urls=get_urls(),
        entries=get_news(),
        format_date=format_date,
    )


@app.route("/news/<slug>")
def news_entry(slug: str) -> str:
    """Einen einzelnen News-Eintrag ausliefern.

    Der Slug wird gegen das Namensmuster geprueft, bevor daraus ein Pfad
    wird. Anders als bei den Terminen gibt es hier keinen Platzhalter: was
    es nicht gibt, gibt es nicht.
    """
    if _news_date(slug) is None:
        abort(404)
    path = os.path.join(app.template_folder or "", "md", "news", f"{slug}.md")
    if not os.path.isfile(path):
        abort(404)
    with open(path, encoding="utf-8") as file_:
        md_text = file_.read()
    # Titel und Teaser gehen zusaetzlich in die Vorschau: geteilt wird ein
    # einzelner Eintrag, nicht die Seite als Ganzes.
    return render_content(
        "news",
        cast(str, _md.render(md_text)),
        og_type="article",
        og_title=first_heading(md_text, "News"),
        og_description=_shorten(_untag(_news_teaser(md_text))),
    )


# Autoritaet und Datum der Atom-IDs, nach RFC 4151. Beides muss auf immer
# unveraendert bleiben: die ID ist das Merkmal, an dem ein Reader einen
# bekannten Eintrag wiedererkennt. Deshalb bewusst nicht die URL selbst, die
# sich mit Host oder Schema aendern kann.
_ATOM_TAG_AUTHORITY = "pycologne.de"
_ATOM_TAG_DATE = "2026"


def _atom_tag(path: str) -> str:
    """Stabile Atom-ID als tag-URI."""
    return f"tag:{_ATOM_TAG_AUTHORITY},{_ATOM_TAG_DATE}:{path}"


# Wurzelrelative Verweise ("/events/...", "/static/images/...") zeigen ins
# Nichts, sobald der Text die Webseite verlaesst: ein Feed-Reader hat keinen
# Bezugspunkt, gegen den er sie aufloesen koennte, Bilder blieben leer und
# Links toter Text. Im Feed werden sie deshalb absolut gemacht. Bewusst nicht
# ueber xml:base, das nicht jeder Reader beachtet.
_ROOT_REF = re.compile(r'(href|src)="/(?!/)')


def _absolutize(html: str) -> str:
    """Wurzelrelative Verweise auf die eigene Adresse umschreiben."""
    return _ROOT_REF.sub(lambda match: f'{match.group(1)}="{WEBSITE_URL}/', html)


def _rfc3339(moment: datetime) -> str:
    """Zeitstempel im Format, das Atom verlangt.

    Die News-Daten sind naive Zeitstempel aus einem Dateinamen, deren
    Uhrzeit ohnehin nur Konvention ist (NEWS_HOUR). Sie werden als UTC
    ausgegeben, statt eine Zeitzonendatenbank dafuer heranzuziehen.
    """
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


@app.route("/news.atom")
def news_feed() -> Response:
    """Atom-Feed der News-Eintraege (RFC 4287).

    Wie beim ICS-Feed wird das XML hier zusammengesetzt und nicht als
    Jinja-Template gerendert. Grund ist das Deployment: es installiert nur
    templates/*.html, ein .xml-Template kaeme auf dem Server nie an und der
    Feed waere im Betrieb leer, ohne dass lokal etwas aufgefallen waere.
    """
    entries = get_news()[:NEWS_FEED_LIMIT]
    # Ohne Eintraege gibt es kein Datum, das der Bestand hergibt. Der
    # Zeitpunkt des Abrufs ist dann die ehrlichste Angabe.
    updated = _rfc3339(entries[0]["date"]) if entries else _rfc3339(datetime.now())
    self_href = quoteattr(f"{WEBSITE_URL}/news.atom")
    page_href = quoteattr(f"{WEBSITE_URL}/news")
    atom_type = 'type="application/atom+xml"'

    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        "  <title>PyCologne, Neuigkeiten</title>",
        "  <subtitle>Neuigkeiten der Python User Group Köln</subtitle>",
        f"  <id>{_atom_tag('news')}</id>",
        f"  <updated>{updated}</updated>",
        f'  <link rel="self" {atom_type} href={self_href}/>',
        f'  <link rel="alternate" type="text/html" href={page_href}/>',
        "  <author><name>PyCologne</name></author>",
    ]

    for entry in entries:
        stamp = _rfc3339(entry["date"])
        slug = entry["slug"]
        href = quoteattr(f"{WEBSITE_URL}{entry['url']}")
        title = xml_escape(entry["title"])
        summary = xml_escape(_absolutize(str(entry["teaser"])))
        # Der ganze Eintrag, nicht nur der Teaser: ein Feed, den man im
        # Reader zu Ende lesen kann, ist der Sinn der Sache.
        body = xml_escape(_absolutize(get_template("md", "news", f"{slug}.md")))
        lines.extend(
            [
                "  <entry>",
                f"    <title>{title}</title>",
                f"    <id>{_atom_tag('news/' + slug)}</id>",
                f'    <link rel="alternate" type="text/html" href={href}/>',
                f"    <updated>{stamp}</updated>",
                f"    <published>{stamp}</published>",
                f'    <summary type="html">{summary}</summary>',
                f'    <content type="html">{body}</content>',
                "  </entry>",
            ]
        )

    lines.append("</feed>")
    return Response("\n".join(lines) + "\n", mimetype="application/atom+xml")


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
    # REPL-Zeile der Flip-Kachel: die gerade laufende Suche als
    # FTS5-Ausdruck, ohne Suchbegriff ein Beispiel.
    fts_input = query or "pandas dataframe"
    return render_template(
        "search.html",
        act="search",
        urls=get_urls(),
        query=query,
        results=results,
        highlight=_highlight,
        format_date=format_date,
        fts_call=f"build_query({fts_input!r})",
        fts_out=repr(build_query(fts_input)),
    )


def _configured_path(variable: str, default: str) -> str:
    """Return a runtime path, overridable via environment variable."""
    return os.environ.get(variable, default)


def _webhook_secret() -> bytes | None:
    """Return the shared secret for the refresh hook, or None if unset."""
    path = _configured_path("PYCOLOGNE_WEBHOOK_SECRET_FILE", WEBHOOK_SECRET_FILE)
    try:
        with open(path, "rb") as file_:
            secret = file_.read().strip()
    except OSError:
        return None
    return secret or None


@app.route("/_content/refresh", methods=["POST"])
def content_refresh() -> tuple[str, int]:
    """Nimm den Anstoss entgegen, dass es neue Inhalte gibt.

    Der Endpunkt prueft die Signatur und beruehrt danach eine Datei, sonst
    nichts. Das Holen selbst erledigt eine systemd-Unit, die diese Datei
    beobachtet. Deshalb laeuft hier kein git im Request-Handler, es braucht
    kein Locking gegen die anderen Gunicorn-Worker, und die Anwendung kommt
    ohne erhoehte Rechte aus. Derselbe Sync laeuft zusaetzlich stuendlich
    per Timer, ein verlorener Anstoss heilt sich also von selbst.
    """
    secret = _webhook_secret()
    if secret is None:
        return "kein Secret hinterlegt", 503
    signature = request.headers.get("X-Hub-Signature-256", "")
    expected = "sha256=" + hmac.new(secret, request.get_data(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return "Signatur passt nicht", 403
    # Inhalt der Datei ist beliebig, nur das Schreiben zaehlt. Die
    # Delivery-ID von GitHub steht drin, damit sich ein einzelner Anstoss
    # im Zweifel bis zur Auslieferung zurueckverfolgen laesst.
    delivery = request.headers.get("X-GitHub-Delivery", "ohne Delivery-ID")
    path = _configured_path("PYCOLOGNE_CONTENT_TRIGGER", CONTENT_TRIGGER_FILE)
    try:
        with open(path, "w", encoding="utf-8") as trigger:
            trigger.write(f"{delivery}\n")
    except OSError:
        return "Trigger-Datei nicht schreibbar", 500
    return "", 202


@app.errorhandler(404)
def page_not_found(_err: Exception) -> tuple[str, int]:
    """Default error handler. Serve error page for 404 responses."""
    msg = "Seite nicht gefunden"
    # Bewusst request.path statt request.url: die absolute URL braucht den
    # Host-Header, und bei kaputten Headern (Scanner schicken z. B. offene
    # eckige Klammern) warf request.url unter Werkzeug 3.1.4 einen
    # ValueError, aus dem 404 wurde dann ein 500. Upstream zwischen 3.1.4
    # und 3.1.8 behoben, aber der Pfad genuegt hier ohnehin.
    info = f"Die angeforderte URL ({request.path}) existiert nicht oder ist nicht mehr verfügbar."
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
        # immer gleichen Hinweistext. Abonnenten sehen das Thema direkt
        # im Kalendereintrag.
        # ICS-DESCRIPTION ist Klartext, kein HTML: die von get_next_meeting_teaser
        # gerenderten Tags (<strong> etc.) wieder entfernen, statt sie roh zu zeigen.
        teaser = _untag(get_next_meeting_teaser(date))
        description = _ics_escape(f"{teaser}\n\n{boilerplate}" if teaser else boilerplate)
        location = _ics_escape(get_meeting_location(date))
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
