Installation
============

First you have to clone this repository and all its submodules::

    $ hg clone https://bitbucket.org/PySV/pycologne-app
    $ cd pycologne-app

Next create a virtualenv and install all the requirments into it. In this
example we are using virtualenvwrapper to manage the virtualenv::

    $ mkvirtualenv -p `which python2` pycologne-app-env

This repository provides requirements and configurations.

To provide the run-time environment for the application, install the
requirements specified in ``requirements.txt``::

    $ pip install -r requirements.txt

Now that this is complete, you can run the pycologne webapp in that
environment::

    $ PYTHONPATH="$(pwd)" python -m pycgnweb

Or, if you have ``make``::

    make run


Development
===========

Instead of cloning the original repository, create your own fork of the
repository through the Bitbucket web interface. You'll need an account on
bitbucket.org to create and manage your fork.

Create an SSH key for your Bitbucket account and import the public key via
"Manage account/SSH keys". Also make sure that you have set up your Bitbucket
account name as your mercurial user name. Edit ``~/.hg/hgrc`` to look something
like this, substituting your Bitbucket account name and email address::

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

For compiling the custom css files from less, you need to install the less
compiler ``lessc``. Under Debian and similar Linux systems, you can install the
packages ``node-less``.


Creating a Commit and a Pull Request
------------------------------------

After you edited some file(s), you can check what has been changed with::

    $ hg stat
    M README.rst

To view a diff of your changes::

    $ hg diff

Now commit them, giving a meaningful commit log message::

    $ hg commit -m "Added development workflow description to README"

Your changes are now committed to your local repository clone only. Push them
to your fork on Bitbucket::

    $ hg push

Now you can go to the Bitbucket page for your repository fork and create a pull
request by clicking on the three dots in the upper left area and then on
"Create pull request". Review your changes and write a message intended for the
project coordinator, who will review and hopefully accept your pull request and
merge your changes into the central repository. A good pull request should
include a description of why the change was made and, if applicable, a
reference to a matching issue in the issue tracker.


Keeping Your Fork in Sync With the Central Repository
-----------------------------------------------------

Sending a pull request will trigger a message to the project coordinator,
who will in time review your changes and either accept or decline them. If your
pull request is accepted, your changes are merged into the central repository.
The central repository will over time likely merge changes from several other
forks. These changes are not automatically propagated to your fork, so you need
to sync your fork with the central repository regularly.

If your fork is out-of-sync with the central repository, the Bitbucket page of
your fork will tell you so and provide a "Sync now" link, with which you can
merge the changes from the central repository into your fork. But this will
only work, if there are no merge conflicts. So it's usually better (and
quicker) to do the syncing via the command line, by pulling of the changes from
the original repository into your local clone::

    $ hg pull -u https://bitbucket.org/PySV/pycologne-app

You can avoid having to type the full URL of the original repository in the
above command every time by creating an alias for it in the ``.hg/hgrc`` file
in your local repository clone::

    [paths]
    default = ssh://hg@bitbucket.org/YourAccountName/pycologne-app
    upstream = https://bitbucket.org/PySV/pycologne-app

Then you can use this alias in your ``hg pull`` command::

    $ hg pull -u upstream

Finally, don't forget to push these changes to your repository fork on
Bitbucket as well::

    $ hg push
