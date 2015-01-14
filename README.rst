Installation
------------

First you have to clone this repository and all its submodules::
   hg clone ssh://hg@bitbucket.org/PySV/pycologne-app
   cd pycologne-app

Next create a virtualenv and install all the requirments into it. In this
example we are using virtualenvwrapper to manage the virtualenv::

    mkvirtualenv pycologne-app-env

This repository provides requirements and configurations.

For local development, install the requirements specified in
requirements::

    pip install -r requirements.txt

Now that this is complete, you can run pymove3d in that environment::

    python ./webapp.py

Testing and developing is done with::

   pip install -r requirements-dev.txt

Now you have additional packages for development and testing:

 - pep8
 - py.test
 - selenium
