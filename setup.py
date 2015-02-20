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
    author_email="webteam@pycologne.de",
    packages=['pycgnweb'],
    entry_points={
        'console_scripts': [
            'pycologne-webapp = pycgnweb.webapp:main'
        ]
    },
    zip_safe=False
)
