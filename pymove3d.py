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


app = Flask(__name__)
babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.route("/")

@app.route("/index")
def index():
    return render_template(get_locale() + "/index.html")

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
    return render_template(get_locale () + "/imprint.html", act="imprint")

@app.route("/privacy")
def privacy():
    return render_template(get_locale() + "/privacy.html", act="privacy")


@app.errorhandler(404)
def page_not_found(e):
    return render_template(get_locale() + "/404.html")

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)


