Installation
------------

First you have to clone this repository and all its submodules::
   hg clone ssh://hg@bitbucket.org/pkoppatz/pymove3d-app
   cd pymove3d-app

Next create a virtualenv and install all the requirments into it. In this
example we are using virtualenvwrapper to manage the virtualenv::
    
    mkvirtualenv pymove3d-env

This repository provides requirements and configurations.

For local development, install the requirements specified in
requirements::

    pip install -r requirements.txt

Now that this is complete, you can run pymove3d in that environment::

    python ./pymove3d.py



    
