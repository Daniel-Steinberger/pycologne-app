"""Gemeinsame Fixtures: die Tests laufen auf einem eigenen Inhaltsbestand.

Die Inhalte der Webseite (Termine, Protokolle, Bilder) liegen seit August
2026 in einem eigenen Repo und sind hier nicht ausgecheckt. Die Tests bauen
sich deshalb einen kleinen Bestand selbst, der jeden Fall einmal abbildet:
ein Protokoll mit ``###``-Themen, eines nur mit Teaser, ein altes mit
``## Programm``-Liste, dazu ein anstehender Termin mit angekuendigtem
Programm und einer mit abweichendem Ort.

Zwei Gruende dafuer. Erstens bleibt die CI dieses Repos unabhaengig vom
Content-Repo, eine reine Textaenderung dort kann die Code-CI hier also
nicht rot faerben. Zweitens waren die Tests vorher an den Kalender
gebunden: sie behaupteten konkrete Termine wie den 08.07.2026 und einen
Ausweichort am 09.09.2026, waeren also irgendwann von selbst rot geworden.
Die anstehenden Termine werden hier stattdessen zur Laufzeit aus
``meeting_dates()`` bestimmt.
"""

import pathlib
import shutil
from datetime import datetime

import pytest

from pycgnweb.events import meeting_dates

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# Bezugstag fuer die Tests der Vergangenheitsliste. Alle Protokolle unten
# liegen davor, alle anstehenden Termine dahinter.
PAST_REFERENCE = datetime(2021, 1, 1)

# Die juengsten drei Treffen stehen auf /events einzeln, der Rest nach
# Jahrgang gruppiert. Der Bestand hier liefert beides.
NEWEST_PAST = "2020-01-08"
TEASER_PAST = "2019-06-12"
OLD_STYLE_PAST = "2017-08-09"

DEFAULT_ORT = "**Ort:** DVS AG, Schanzenstraße 30, 51063 Köln ([Anfahrt](/join))"

PAST_PROTOCOLS = {
    # Protokoll mit Themen-Ueberschriften
    NEWEST_PAST: f"""# PyCologne Treffen Januar 2020

**Datum:** Mi, 08.01.2020, 19:00 Uhr
{DEFAULT_ORT}

Ein Abend mit zwei Vortraegen, das Protokoll fasst beide zusammen.

### 1. HPC mit Python

Numerische Rechnungen auf dem Cluster, mit Beispielen aus der Praxis.

### 2. Datenanalyse mit pandas

Ein Rundgang durch DataFrames, siehe [die Doku](https://pandas.pydata.org/).
""",
    # Protokoll ohne Gliederung: die erste Textzeile wird zum Teaser
    TEASER_PAST: f"""# PyCologne Treffen Juni 2019

**Datum:** Mi, 12.06.2019, 19:00 Uhr
{DEFAULT_ORT}

Da Daniel verhindert war, wurde daraus eine offene Runde. Das Protokoll
gibt es nur in Stichworten.
""",
    "2019-05-08": f"""# PyCologne Treffen Mai 2019

**Datum:** Mi, 08.05.2019, 19:00 Uhr
{DEFAULT_ORT}

### 1. Ueberraschungen im Typsystem

Ein Protokoll ueber Metaklassen und andere Feinheiten.
""",
    # Alter Stil: das Programm steht als Aufzaehlung, nicht als Abschnitte
    OLD_STYLE_PAST: """# PyCologne Treffen August 2017

**Datum:** Mi, 09.08.2017, 19:00 Uhr

## Programm

- Einfuehrung in Metaklassen
- Kurzvorstellung von flake8

## Notizen

Das Protokoll stammt aus dem alten Etherpad-Archiv.
""",
    # Aeltester Jahrgang, damit die Archiv-Gruppierung mehr als ein Jahr hat
    "2013-08-14": """# PyCologne Treffen August 2013

**Datum:** Mi, 14.08.2013, 19:00 Uhr

Von diesem Abend ist nur eine Stichwortliste als Protokoll erhalten.
""",
}

ABOUT = """# Die User Group

PyCologne ist die Python User Group Koeln.
"""

# News-Eintraege. Der aelteste beginnt bewusst mit Fettschrift und einem
# Bild, das ist der Unterschied zu den Termin-Dateien: dort stehen an
# derselben Stelle die Datum- und Ort-Zeilen, hier gehoert es zum Text.
NEWEST_NEWS = "2026-08-17-facebook-nach-zehn-jahren"
OLDEST_NEWS = "2026-08-01-neue-webseite"

NEWS_ENTRIES = {
    NEWEST_NEWS: """# Facebook nach zehn Jahren

Unsere alte Facebook-Seite lebt wieder, der erste Beitrag seit 2016 ist
draussen. Mehr dazu auf [Meetup](https://www.meetup.com/pycologne/).
""",
    OLDEST_NEWS: """# Neue Webseite

![Ein Screenshot](/static/images/events/beispiel.svg)

**Endlich:** die Seite laeuft wieder unter eigener Adresse.
""",
}

CONTACT = """# Kontakt

Am einfachsten ueber [Meetup](https://www.meetup.com/pycologne/).
"""


def _upcoming_program(date: datetime) -> str:
    """Anstehender Termin, dessen Programm schon feststeht."""
    return f"""# PyCologne Treffen {date:%Y-%m}

**Datum:** Mi, {date:%d.%m.%Y}, 19:00 Uhr
{DEFAULT_ORT}

Ein **Deep Dive** in die Standardbibliothek, mit Beispielen zum Mitmachen.
"""


def _upcoming_elsewhere(date: datetime) -> str:
    """Anstehender Termin an einem anderen Ort als dem Standardort."""
    return f"""# PyCologne Treffen {date:%Y-%m}

**Datum:** Mi, {date:%d.%m.%Y}, 19:00 Uhr
**Ort:** Cologne Game Lab, Schanzenstraße 28, 51063 Köln ([Anfahrt](/join))

Ausweichtermin im Cologne Game Lab.
"""


@pytest.fixture(scope="session")
def upcoming() -> list[datetime]:
    """Die naechsten Termine, wie der ICS-Feed sie auch berechnet."""
    return list(meeting_dates(count=12))


@pytest.fixture(scope="session")
def template_root(tmp_path_factory, upcoming) -> pathlib.Path:
    """Template-Ordner aus echten HTML-Templates und erfundenen Inhalten.

    Die HTML-Templates sind Code und liegen in diesem Repo, sie werden
    unveraendert uebernommen. Nur der Markdown-Teil, der sonst aus dem
    Content-Repo kaeme, wird hier erfunden.
    """
    root = tmp_path_factory.mktemp("templates")
    for template in (REPO_ROOT / "templates").glob("*.html"):
        shutil.copy(template, root)

    events = root / "md" / "events"
    events.mkdir(parents=True)
    (root / "md" / "about.md").write_text(ABOUT, encoding="utf-8")
    (root / "md" / "contact.md").write_text(CONTACT, encoding="utf-8")
    for stem, text in PAST_PROTOCOLS.items():
        (events / f"{stem}.md").write_text(text, encoding="utf-8")

    news = root / "md" / "news"
    news.mkdir(parents=True)
    for stem, text in NEWS_ENTRIES.items():
        (news / f"{stem}.md").write_text(text, encoding="utf-8")
    # Ein Name, der dem Muster nicht entspricht: die Uebersicht muss ihn
    # ueberspringen, statt daran zu zerbrechen.
    (news / "kein-datum.md").write_text("# Ohne Datum\n", encoding="utf-8")

    # Der naechste Termin hat ein angekuendigtes Programm, der uebernaechste
    # weicht vom Standardort ab. Beides braucht der ICS-Feed.
    (events / f"{upcoming[0]:%Y-%m-%d}.md").write_text(
        _upcoming_program(upcoming[0]), encoding="utf-8"
    )
    (events / f"{upcoming[1]:%Y-%m-%d}.md").write_text(
        _upcoming_elsewhere(upcoming[1]), encoding="utf-8"
    )
    return root
