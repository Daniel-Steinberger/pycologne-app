#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A Flask-based webapp for the homepage of the pyCologne Python user group."""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import codecs
import os
import sys

from functools import partial

from babel.dates import format_datetime
from docutils.core import publish_parts
from flask import Flask
from flask import render_template
from flask import request

from .config import (DATE_FORMAT_LONG, FACEBOOK_URL, GOOGLE_PLUS_URL,
                     TWITTER_URL)
from .sayings import get_saying
from .events import meeting_dates

# set default language
LANGUAGE_SELECTED = "de"

# pylint: disable=C0103
app = Flask(__name__.split('.')[0])
# pylint: enable=C0103


def _(msg):
    """Dummy translation function."""
    return msg


# helper functions
def get_locale():
    """Return language code for locale used for translations and templates."""
    # note: PyCologne app currently has DE language only
    return LANGUAGE_SELECTED


def get_urls():
    """Return a dictionary with fixed (external) URLs."""
    urls = [('twitter', TWITTER_URL), ('facebook', FACEBOOK_URL),
            ('google', GOOGLE_PLUS_URL)]
    return dict(urls)


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

    The location of the template is specified with its path name components as
    positional parameters. The path name components are interpreted as being
    relative to the template directory for the currently selected language. If
    multiple path name components are given, they are joined with
    ``os.path.join``. The last component must be the template filename.

    The contents of the template file are expected to be UTF-8 encoded.

    """
    return get_content(os.path.join(app.template_folder, get_locale(), *args))


def get_topmenue():
    """Return top-level menu structure as a list of (urlpath, label) tuples."""
    menue = [
        ('/', _('Startseite')),
        ('/about', _('Die User Group')),
        ('/join', _('Mitmachen')),
        ('/events', _('Termine')),
        ('/contact', _('Kontakt')),
    ]
    return menue

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
                          format=DATE_FORMAT_LONG.get(get_locale(), 'long'),
                          locale=get_locale())

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
                          format=DATE_FORMAT_LONG.get(get_locale(), 'long'),
                          locale=get_locale())

    return render_template("/events.html",
                           act='events',
                           meetings=meetings,
                           next_meeting=next_meeting,
                           events=events_,
                           format_date=format_date)


@app.route("/contact")
def contact():
    """Return contact page."""
    content = get_template("rst", "contact.rst")
    return render_content("contact", content)


# pylint: disable=W0613
@app.errorhandler(404)
def page_not_found(err):
    """Default error handler. Serve error page for 404 responses."""
    msg = "Url: %s not found" % request.url
    info = "This information is not available!"
    return render_template("404.html", msg=msg, info=info)
# pylint: enable=W0613


def main(args=None):
    """Main command line script entry point."""
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
    args = parser.parse_args(args if args is not None else sys.argv[1:])

    app.static_folder = args.static_folder
    app.template_folder = args.template_folder
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
