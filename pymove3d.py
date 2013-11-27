from flask import Flask
from flask import render_template
from flask import request
from flask import abort, redirect, url_for
import os
from flask import send_from_directory
import logging
from logging import Formatter

from flask.ext.babel import gettext
from flask.ext.babel import Babel

app = Flask(__name__)
babel = Babel(app)

@babel.localeselector
def get_locale():
    return "en" #request.accept_languages.best_match(LANGUAGES.keys())

@app.route("/")

@app.route("/index")
def index():
    return render_template("index.html")

@app.route("/competition")
def competition():
    return render_template("competition.html", act="competition")

@app.route("/task")
def task():
    return render_template("task.html", act="task")

@app.route("/submission")
def submission():
    return render_template("submission.html", act="submission")

@app.route("/coursematerial")
def coursematerial():
    return render_template("coursematerial.html", act="coursematerial")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)


