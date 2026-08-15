"""Configuration settings for the webapp."""

from typing import Final

# Format strings for babel.dates.format_datetime
DATE_FORMAT_LONG: Final[str] = "EEEE, d. MMMM yyyy, HH:mm 'Uhr'"


WEBSITE_URL: Final[str] = "https://www.pycologne.de"
MEETUP_URL: Final[str] = "https://www.meetup.com/pyCologne/"
REPO_URL: Final[str] = "https://github.com/Daniel-Steinberger/pycologne-app"

GOOGLE_CAL_URL: Final[str] = (
    "https://www.google.com/calendar/embed?src=fm26mlvtjlqsjqpj53jq1pd128"
    "@group.calendar.google.com&ctz=Europe/Berlin"
)
GOOGLE_CAL_ICS: Final[str] = (
    "https://www.google.com/calendar/ical/fm26mlvtjlqsjqpj53jq1pd128"
    "@group.calendar.google.com/public/basic.ics"
)

# Inhalte (Termine, Protokolle, Bilder) liegen in einem eigenen Repo und
# werden auf dem Server dorthin verlinkt, statt mit der Anwendung gebaut zu
# werden.
CONTENT_REPO_URL: Final[str] = "https://github.com/Daniel-Steinberger/pycologne-content"

# Anstoss von aussen, dass es neue Inhalte gibt, s. webapp.content_refresh().
# Das Secret steht bewusst in einer Datei und nicht hier, denn dieses Repo ist
# oeffentlich. Beide Pfade lassen sich zur Laufzeit per Umgebungsvariable
# umbiegen (PYCOLOGNE_WEBHOOK_SECRET_FILE bzw. PYCOLOGNE_CONTENT_TRIGGER),
# damit sich die Mechanik auch ausserhalb des Servers ausprobieren laesst.
# noqa unten: der Wert ist der Pfad zur Secret-Datei, nicht das Secret selbst.
WEBHOOK_SECRET_FILE: Final[str] = "/var/lib/pycologne/webhook-secret"  # noqa: S105
CONTENT_TRIGGER_FILE: Final[str] = "/var/lib/pycologne/content-refresh.trigger"
