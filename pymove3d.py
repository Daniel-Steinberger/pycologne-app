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

@app.route(_("/index"))
def index():
    return render_template(_("en/index.html"))

@app.route(_("/competition"))
def competition():
    return render_template(_("en/competition.html"), act="competition")

@app.route(_("/task"))
def task():
    return render_template(_("en/task.html"), act="task")

@app.route(_("/submission"))
def submission():
    return render_template(_("en/submission.html"), act="submission")

@app.route(_("/coursematerial"))
def coursematerial():
    return render_template(_("en/coursematerial.html"), act="coursematerial")

@app.route(_("/imprint"))
def imprint():
    return render_template(_("en/imprint.html"), act="imprint")

@app.route(_("/privacy"))
def privacy():
    return render_template(_("en/privacy.html"), act="privacy")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)


