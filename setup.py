#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py
#
"""Setup file for the PyCologne webapp."""

from setuptools import setup


setup(
    name="pycologne-app",
    description="A Flask app that drives the PyCologne web site",
    author="PyCologne",
    author_email="Webteam@pycologne.de",
    py_modules=['webapp', 'sayings'],
    test_suite='nose.collector',
    tests_require=['nose'],
    zip_safe=False
)
