# -*- coding: utf-8 -*-

import os
import codecs

from docutils.core import publish_parts
from flask import Flask
from flask import render_template
from flask import request
# from config import LANGUAGES
LANGUAGE_SELECTED = "de"
from sayings import get_saying

# gets the path where all stuff is located
APP_PATH = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# dummy translation function
_ = lambda s: s

def get_locale():
    # note: PyCologne app currently has DE  only
    return LANGUAGE_SELECTED

def get_content(filename, overrides=None):
    filename = os.path.join(APP_PATH, filename)
    content = u""
    if os.path.isfile(filename):
        with codecs.open(filename, 'r', 'utf-8') as f:
            rst_data = f.read()
        f.close()
        content = publish_parts(rst_data, writer_name='html', settings_overrides=overrides)['html_body']
    return content

def get_topmenue():
    menue = [
        ('/about', _(u'Die User Group')),
        ('/join', _(u'Mitmachen')),
        ('/events', _(u'Termine')),
        ('/contact', _(u'Kontakt')),
    ]
    return menue

app.jinja_env.globals.update(get_topmenue=get_topmenue)

# main page

@app.route("/")
@app.route("/index")
def index():
    saying, author = get_saying()
    return render_template("/index.html", saying=saying, author=author)
# sub pages

# TODO:  add real pycologne content ...

@app.route("/about")
def about():
    filename = os.path.join("templates", get_locale(), "rst", "about.rst")
    content = get_content(filename)
    return render_template("/content.html", act="about", content=content)

@app.route("/join")
def join():
    filename = os.path.join("templates", get_locale(), "rst", "join.rst")
    content = get_content(filename)
    return render_template("/content.html", act="join", content=content)

@app.route("/events")
def events():
    filename = os.path.join("templates", get_locale(), "rst", "events.rst")
    content = get_content(filename)
    return render_template("/content.html", act="events", content=content)

@app.route("/contact")
def contact():
    filename = os.path.join("templates", get_locale(), "rst", "contact.rst")
    content = get_content(filename)
    return render_template("/content.html", act="contact", content=content)

# default error handler

@app.errorhandler(404)
def page_not_found(e):
    msg = u"Url: %s not found" % request.url
    info = u"This information is not available!"
    return render_template("404.html", msg=msg, info=info)

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)
