Installation
============

First you have to clone this repository and all its submodules::

    $ hg clone ssh://hg@bitbucket.org/PySV/pycologne-app
    $ cd pycologne-app

Next create a virtualenv and install all the requirments into it. In this
example we are using virtualenvwrapper to manage the virtualenv::

    $ mkvirtualenv -p `which python2` pycologne-app-env

This repository provides requirements and configurations.

For local development, install the requirements specified in
requirements::

    $ pip install -r requirements.txt

Now that this is complete, you can run the pycologne webapp in that
environment::

    $ python webapp.py


Development
===========

Instead of cloning the original repository, create your own fork of the
repository through the Bitbucket web interface. You'll need an account on
bitbucket.org to create and manage your fork.

Create an SSH key for your Bitbucket account and import the public key via
"Manage account/SSH keys". Also make sure that you have set up your Bitbucket
account name as your mercurial username. Edit `~/.hg/hgrc` to look something
like this, substituting your Bitbucket accout name and email address::

    [ui]
    # Name data to appear in commits
    username = YourAccountName <me@pycologne.de>

Then clone your fork::

    $ hg clone ssh://hg@bitbucket.org/YourAccountName/pycologne-app
    $ cd pycologne-app

Create a virtual environment as described above and install the development
requirements with::

    $ pip install -r requirements-dev.txt

Now you have additional packages for development and testing:

- pep8
- py.test
- selenium


Creating a Commit and a Pull Request
------------------------------------

After you edited some file(s), you can check what has been changed with::

    $ hg stat
    M README.rst

To view a diff of your changes::

    $ hg diff

Now commit them, giving a meaningful commit log message::

    $ hg commit -m "Added development workflow description to README"

Your changes are now commited to your local repository clone only. Push them to
your fork on Bitbucket::

    $ hg push

Now you can go to the Bitbucket page for your repository and create a pull
request by clicking on the three dots in the upper left area and then on
"Create pull request". Review your changes and write a message intended for the
project coordinator, who will review and hopefully accept your pull request and
merge your changes into the central repository. A good pull request should
include a description of why the change was made and, if applicable, a
reference to a matching issue in the issue tracker.

Sending the pull request will trigger a message to the project coordinator,
who will in time review your changes and either accept or decline them.
