# -*- coding: utf-8 -*-

import os
import codecs

from docutils.core import publish_parts
from flask import Flask
from flask import render_template
from flask import request
from flask.ext.babel import gettext as _
from flask.ext.babel import Babel
from config import LANGUAGES
from sayings import get_saying


LANGUAGE_SELECTED = "de"
#ToDo after engelish is implemented set LANGUAGE_SELECTED = None

# gets the path where all stuff is located
PYMOVE3D_PATH = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
babel = Babel(app)

app.config['BABEL_DEFAULT_LOCALE'] = 'de'


def get_content(filename, overrides=None):
    filename = os.path.join(PYMOVE3D_PATH, filename)
    content = u""
    if os.path.isfile(filename):
        with codecs.open(filename, 'r', 'utf-8') as f:
            rst_data = f.read()
        f.close()
        content = publish_parts(rst_data, writer_name='html', settings_overrides=overrides)['html_body']
    return content

def get_topmenue():
    menue = [('/competition', _(u'Competition')),
              ('/task', _(u'Task')),
              ('/coursematerial', _(u'Coursematerial')),
              ('/submission', _(u'Submission')),
              ('/prizes', _(u'Prizes')),
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
                           saying=saying,
                           author=author,
                           competition_info=_(u'About Competition'),
                           dates=_(u'Dates'),
                           impressions=_(u'Impressions'))

@app.route('/de')
def de():
    global LANGUAGE_SELECTED
    LANGUAGE_SELECTED = "de"
    saying, author = get_saying()
    return render_template("/index.html",
                           saying=saying,
                           author=author,
                           competition_info=_(u'About Competition'),
                           dates=_(u'Dates'),
                           impressions=_(u'Impressions'))

@app.route('/en')
def en():
    saying, author = get_saying()
    global LANGUAGE_SELECTED
    LANGUAGE_SELECTED = "en"
    return render_template("/index.html",
                           saying=saying,
                           author=author,
                           competition_info=_(u'About Competition'),
                           dates=_(u'Dates'),
                           impressions=_(u'Impressions'))

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



@app.route("/competition/2013")
def competition_2013():
    competition = _(u'Competition 2013')
    introduction = _(u'The winners of the programming competition, '
                     u'showed at the PyCon.DE 2013 in Cologne their results. '
                     u'A short presentation inlcuding a movie about their work done.')
    article = [_(u'Both students presented to the astonished audience of over 250 Python developers their work.'),
               _(u'A long applause showed up.'
                 u' Valentin had 9 months ago learned Python and Blender discovered earlier. '
                 u'His Skatsimulation even includes 3D sound.'),
               _(u'The preparatory courses were made by volunteers, such as the '
                 u'employees of the magazine "Time Online" performed. '
                 u'The following blog entry is a little impression of the success of the courses'),
              ]
    game_of_life = _(u'Anne a 15 year old girl showed a 3D-Version of the »Game of life«')
    skat_simulation = _(u'Valentin (13 years) demomstrates his »Skat-Simulation«')
    awards = _(u'The award ceremony')
    return render_template("/impressions_2013.html",
                           act="competition_2013",
                           competition=competition,
                           introduction=introduction,
                           article=article,
                           game_of_life=game_of_life,
                           skat_simulation=skat_simulation,
                           awards=awards)


@app.errorhandler(404)
def page_not_found(e):
    msg = _(u"Url: %(url)s not found", url=request.url)
    info = _(u"This information is not available!")
    return render_template("404.html", msg=msg, info=info)

if __name__ == "__main__":
    app.run(host='localhost', port=5014, debug=True)
