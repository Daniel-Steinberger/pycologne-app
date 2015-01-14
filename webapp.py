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
    menue = [('/competition', u'Competition'),
              ('/task', u'Task'),
              ('/coursematerial', u'Coursematerial'),
              ('/submission', u'Submission'),
              ('/prizes', u'Prizes'),
            ]
    return menue

app.jinja_env.globals.update(get_topmenue=get_topmenue)

# main page

@app.route("/")
@app.route("/index")
def index():
    saying, author = get_saying()
    return render_template("/index.html",
                           saying=saying,
                           author=author,
                           competition_info='About Competition',
                           dates='Dates',
                           impressions='Impressions')
# sub pages

# TODO:  add real pycologne content ...

@app.route("/competition")
def competition():
    filename = os.path.join("templates", get_locale(), "rst", "competition.rst")
    content = get_content(filename)
    return render_template("/content.html", act="competition", content=content)

@app.route("/task")
def task():
    filename = os.path.join("templates", get_locale(), "rst", "task.rst")
    content = get_content(filename)
    return render_template("/content.html", act="task", content=content)

@app.route("/submission")
def submission():
    filename = os.path.join("templates", get_locale(), "rst", "submission.rst")
    content = get_content(filename)
    return render_template("/content.html", act="submission", content=content)

@app.route("/coursematerial")
def coursematerial():
    filename = os.path.join("templates", get_locale(), "rst", "coursematerial.rst")
    content = get_content(filename)
    return render_template("/content.html", act="coursematerial", content=content)

@app.route("/imprint")
def imprint():
    filename = os.path.join("templates", get_locale(), "rst", "imprint.rst")
    content = get_content(filename)
    return render_template("/content.html", act="imprint", content=content)

@app.route("/privacy")
def privacy():
    filename = os.path.join("templates", get_locale(), "rst", "privacy.rst")
    overrides = {
                 'initial_header_level': 2,
                }
    content = get_content(filename, overrides=overrides)
    return render_template("/content.html", act="privacy", content=content)

@app.route("/dates")
def dates():
    filename = os.path.join("templates", get_locale(), "rst", "dates.rst")
    content = get_content(filename)
    return render_template("/content.html",
                           act="dates", content=content)

@app.route("/prizes")
def prizes():
    filename = os.path.join("templates", get_locale(), "rst", "prizes.rst")
    overrides = {
                 'initial_header_level': 2,
                }
    content = get_content(filename, overrides=overrides)
    return render_template("/prizes.html",act="prizes", content=content)


# default error handler

@app.errorhandler(404)
def page_not_found(e):
    msg = u"Url: %s not found" % request.url
    info = u"This information is not available!"
    return render_template("404.html", msg=msg, info=info)

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)
