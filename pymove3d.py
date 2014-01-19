from flask import Flask
from flask import render_template
from flask import request
from flask import abort, redirect, url_for
import os
from flask import send_from_directory
import logging
from logging import Formatter

from flask.ext.babel import gettext as _
from flask.ext.babel import Babel

from config import LANGUAGES
from sayings import get_saying
from jinja2 import Environment, FileSystemLoader

import codecs
from docutils.core import publish_parts


LANGUAGE_SELECTED = "de"
#ToDo after engelish is implemented set LANGUAGE_SELECTED = None

app = Flask(__name__)
babel = Babel(app)

app.config['BABEL_DEFAULT_LOCALE'] = 'de'

def get_content(filename):
    content = u""
    if os.path.isfile(filename):
        with codecs.open(filename, 'r', 'utf-8') as f:
            rst_data = f.read()
        f.close()
        content = publish_parts(rst_data, writer_name='html')['html_body']
    return content

def get_topmenue():
    menue =  [('/competition', _(u'Competition')),
              ('/task', _(u'Task')),
              ('/submission', _(u'Submission')),
              ('/coursematerial', _(u'Coursematerial')),
              ]
    return menue

app.jinja_env.globals.update(get_topmenue=get_topmenue)


@babel.localeselector
def get_locale():
    """ToDo: if translation is completed, switch to en """
    return LANGUAGE_SELECTED or request.accept_languages.best_match(LANGUAGES.keys()) or 'de'


@app.route("/")
@app.route("/index")
def index():
    saying, author = get_saying()
    return render_template("/index.html", 
                           saying = saying,
                           author = author)

@app.route('/de')
def de():
    global LANGUAGE_SELECTED
    LANGUAGE_SELECTED = "de"
    saying, author = get_saying()
    return render_template("/index.html",
                           saying = saying,
                           author = author)

@app.route('/en')
def en():
    saying, author = get_saying()
    global LANGUAGE_SELECTED
    LANGUAGE_SELECTED = "en"
    return render_template("/index.html",
                           saying = saying,
                           author = author)

@app.route("/competition")
def competition():
    filename = os.path.join("templates", get_locale(), "rst", "competition.rst")
    content = get_content(filename)
    return render_template("/competition.html", act="competition", content=content)

@app.route("/task")
def task():
    filename = os.path.join("templates", get_locale(), "rst", "task.rst")
    content = get_content(filename)
    return render_template("/task.html", act="task", content=content)

@app.route("/submission")
def submission():
    return render_template(get_locale() + "/submission.html", act="submission")

@app.route("/coursematerial")
def coursematerial():
    filename = os.path.join("templates", get_locale(), "rst", "coursematerial.rst")
    content = get_content(filename)
    return render_template("/coursematerial.html", act="coursematerial", content=content)

@app.route("/imprint")
def imprint():
    filename = os.path.join("templates", get_locale(), "rst", "imprint.rst")
    content = get_content(filename)
    return render_template("/imprint.html", act="imprint", content=content)

@app.route("/privacy")
def privacy():
    filename = os.path.join("templates", get_locale(), "rst", "privacy.rst")
    content = get_content(filename)
    return render_template("/privacy.html", act="privacy", content=content)

@app.route("/competition/2013")
def competition_2013():
    print get_locale() + "/archive/competitions/2013/index.html"
    return render_template(get_locale() + "/archive/competitions/2013/index.html", 
                           act="coursematerial")

@app.route("/competition/2014")
def competition_2014():
    print get_locale() + "/archive/competitions/2014/index.html"
    return render_template(get_locale() + "/archive/competitions/2014/index.html", 
                           act="coursematerial")


@app.route("/dates")
def dates():
    filename = os.path.join("templates", get_locale(), "rst", "dates.rst")
    content = get_content(filename)
    return render_template("/dates.html",
                           act="dates", content=content)


@app.errorhandler(404)
def page_not_found(e):
    msg = _(u"Url: %(url)s not found" , url=request.url)
    info = _(u"This information is not available!")
    return render_template("404.html", msg=msg, info=info)

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)
