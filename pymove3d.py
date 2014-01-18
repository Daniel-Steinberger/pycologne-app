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

LANGUAGE_SELECTED = "de"
#ToDo after engelish is implemented set LANGUAGE_SELECTED = None

app = Flask(__name__)
babel = Babel(app)

@babel.localeselector
def get_locale():
    """ToDo: if translation is completed, switch to en """
    return LANGUAGE_SELECTED or request.accept_languages.best_match(LANGUAGES.keys()) or 'de'


@app.route("/")
@app.route("/index")
def index():
    saying, author = get_saying()
    return render_template(get_locale() + "/index.html", 
                           saying = saying,
                           author = author)

@app.route('/de')
def de():
    global LANGUAGE_SELECTED
    LANGUAGE_SELECTED = "de"
    return render_template("/de/index.html")

@app.route('/en')
def en():
    global LANGUAGE_SELECTED
    LANGUAGE_SELECTED = "en"
    return render_template("/en/index.html")

@app.route("/competition")
def competition():
    return render_template(get_locale() + "/competition.html", act="competition")

@app.route("/task")
def task():
    return render_template(get_locale() + "/task.html", act="task")

@app.route("/submission")
def submission():
    return render_template(get_locale() + "/submission.html", act="submission")

@app.route("/coursematerial")
def coursematerial():
    return render_template(get_locale() + "/coursematerial.html", act="coursematerial")

@app.route("/imprint")
def imprint():
    return render_template(get_locale() + "/imprint.html", act="imprint")

@app.route("/privacy")
def privacy():
    return render_template(get_locale() + "/privacy.html", act="privacy")

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

@app.route(_("/dates"))
def dates():
    return render_template(get_locale() + "/dates.html",
                           act="dates")


@app.errorhandler(404)
def page_not_found(e):
    return render_template(get_locale() + "/404.html")

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)
