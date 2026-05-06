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
