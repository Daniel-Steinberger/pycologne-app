#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A Flask-based webapp for the homepage of the pyCologne Python user group."""

import argparse
import codecs
import os
import sys

from functools import partial

from babel.dates import format_datetime
from docutils.core import publish_parts
from flask import abort
from flask import Flask
from flask import render_template
from flask import request

from .config import (DATE_FORMAT_LONG, MEETUP_URL, REPO_URL)

from .sayings import get_saying
from .events import meeting_dates

# pylint: disable=C0103
app = Flask(__name__.split('.')[0])
# pylint: enable=C0103


def get_urls():
    """Return a dictionary with fixed (external) URLs."""
    return {
        'repo': REPO_URL,
        'meetup': MEETUP_URL,
    }


def get_content(filename, overrides=None):
    """Read ReST document from file and return it as a HTML unicode string.

    If the file does not exist, returns an empty string.

    """
    content = ""

    if os.path.isfile(filename):
        with codecs.open(filename, 'r', 'utf-8') as file_:
            rst_data = file_.read()

        content = publish_parts(
            rst_data,
            writer_name='html',
            settings_overrides=overrides)['html_body']

    return content


def get_template(*args):
    """Return contents of given template as a unicode string.

    The location of the template is specified with its path name
    components as positional parameters. The path name components are
    interpreted as being relative to the template directory. If
    multiple path name components are given, they are joined with
    ``os.path.join``. The last component must be the template
    filename.

    The contents of the template file are expected to be UTF-8 encoded.

    """
    return get_content(os.path.join(app.template_folder, *args))


def get_topmenue():
    """Return top-level menu structure as a list of (urlpath, label) tuples."""
    menue = [
        ('/', 'Startseite'),
        ('/about', 'Die User Group'),
        ('/join', 'Mitmachen'),
        ('/events', 'Termine'),
        ('/contact', 'Kontakt'),
    ]
    return menue


def ensure_next_meeting(next_date):
    """ensure that an .rst file for the next meeting is present
    """
    path = os.path.join(
        app.template_folder,
        'rst',
        'events',
        '{:%Y-%m-%d}.rst'.format(next_date),
    )
    if os.path.isfile(path):
        return True
    title = "PyCologne Treffen {:%B %Y}".format(next_date)
    line = '=' * len(title)
    header = title + '\n' + line

    with open(path, 'w+') as meeting:
        meeting.write("""{header}

Datum:
  Mi, {next_date:%d.%m.%Y}
Uhrzeit:
  19:00
Ort:
  ReHub
  Deutz-Mülheimer Straße 121
  51063 Köln (Anfahrt_)

Das Programm für das Treffen steht noch nicht fest.

**Wir suchen noch Themen!** Wenn Du einen Vortrag halten oder andere Programmpunkte
anmelden willst, schreibe einfach auf die Mailingliste_! Daneben gibt es Raum für
spontan eingebrachte Themen, z.B. Buch- und Programm-Vorstellungen, Fragen,
Ankündigungen und alles was euch so zum Thema Python einfällt.

Hast Du vor, zu kommen oder bist verhindert? Sag' uns unverbindlich
über Meetup_ Bescheid (kostenlose Anmeldung erforderlich).

Etherpad Protokoll_

.. _Anfahrt: /join
.. _Meetup: http://www.meetup.com/pyCologne/
.. _Protokoll: http://yourpart.eu/p/pyc_{next_date:%Y%m%d}
""".format(header=header, next_date=next_date))


app.jinja_env.globals.update(get_topmenue=get_topmenue)


def render_content(page, content, **kw):
    """Render page with given name and content with content template."""
    return render_template("/content.html", act=page, content=content,
                           urls=get_urls(), **kw)


# main page
@app.route("/")
@app.route("/index")
def index():
    """Serve main index page."""
    saying, author = get_saying()
    # get dates for next twelve user group meetings
    meetings = meeting_dates()
    next_meeting = next(meetings)
    # curry date formatting function
    format_date = partial(format_datetime,
                          format=DATE_FORMAT_LONG,
                          locale="DE")

    return render_template("/index.html", urls=get_urls(),
                           act='',
                           next_meeting=next_meeting,
                           format_date=format_date,
                           saying=saying, author=author)


# sub pages
@app.route("/about")
def about():
    """Return about page."""
    content = get_template("rst", "about.rst")
    return render_content("about", content)


@app.route("/join")
def join():
    """Return join page."""
    content = get_template("rst", "join.rst")
    return render_content("join", content)


@app.route("/events")
def events():
    """Serve events page with list of upcoming meetings."""
    # get dates for next twelve user group meetings
    meetings = meeting_dates()
    next_meeting = next(meetings)
    # get manually added extra events from ReST file
    events_ = get_template("rst", "events.rst")
    # curry date formatting function
    format_date = partial(format_datetime,
                          format=DATE_FORMAT_LONG,
                          locale="DE")

    next_meeting_url = '/events/{:%Y-%m-%d}'.format(next_meeting)
    ensure_next_meeting(next_meeting)
    return render_template("/events.html",
                           act='events',
                           meetings=meetings,
                           next_meeting=next_meeting,
                           next_meeting_url=next_meeting_url,
                           events=events_,
                           format_date=format_date)


@app.route("/events/<date>")
def events_date(date):
    """Serve an event page for a specific meeting."""
    content = get_template("rst/events/", "{}.rst".format(date))
    if content == u'':
        abort(404)
    return render_content("event", content)


@app.route("/contact")
def contact():
    """Return contact page."""
    content = get_template("rst", "contact.rst")
    return render_content("contact", content)


# pylint: disable=W0613
@app.errorhandler(404)
def page_not_found(err):
    """Default error handler. Serve error page for 404 responses."""
    msg = "URL not found: %s" % request.url
    info = "This information is not available!"
    return render_template("404.html", msg=msg, info=info)
# pylint: enable=W0613


def main(args=None):
    """Main command line script entry point for starting the development
    server or WSGI server."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        '--debug',
        action="store_true",
        help="Run server in debug mode (default: %(default)s).")
    parser.add_argument(
        '--host',
        default="localhost",
        help="Hostname/IP address to bind server to (default: %(default)s).")
    parser.add_argument(
        '--port',
        type=int,
        default=5014,
        help="Port number to bind server to (default: %(default)s).")
    parser.add_argument(
        '--static-folder',
        default=os.path.join(os.getcwd(), 'static'),
        help="Path to web server static files (default: %(default)s).")
    parser.add_argument(
        '--template-folder',
        default=os.path.join(os.getcwd(), 'templates'),
        help="Path to HTML and ReST templates (default: %(default)s).")
    parser.add_argument(
        '--wsgi',
        default=False,
        action="store_true",
        help="If given, start the webapp as WSGI server")
    args = parser.parse_args(args if args is not None else sys.argv[1:])

    app.static_folder = args.static_folder
    app.template_folder = args.template_folder

    if args.wsgi:
        from flipflop import WSGIServer
        WSGIServer(app).run()
    else:
        app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
