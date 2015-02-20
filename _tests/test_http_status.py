#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functional tests for webapp using Selenium."""

from __future__ import unicode_literals, print_function

import os

# we don't use 'from flask.ext.testing import ...'
# because pylint can't cope with the custom Flask importer
from flask_testing import LiveServerTestCase

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from pycgnweb.webapp import app


class HTTPStatusTest(LiveServerTestCase):
    """Test case checking that all URLs return valid pages."""

    def setUp(self):
        """Create Selenium webdriver instance for Firefox."""
        self.browser = webdriver.Firefox()

    def tearDown(self):
        """Close the browser window and delete webdriver instance."""
        self.browser.close()
        del self.browser

    def create_app(self):
        """Create Flask application instance."""
        print("Current dir: %s" % os.getcwd())
        app.static_folder = os.path.join(os.getcwd(), 'static')
        app.template_folder = os.path.join(os.getcwd(), 'templates')
        app.config['TESTING'] = True
        app.config['LIVESERVER_PORT'] = 5014
        app.debug = True
        return app

    def check_url(self, url):
        """Check that page content is found."""
        self.browser.get(url)
        try:
            heading1 = self.browser.find_element_by_xpath(
                "//h3[@id='message']")
            self.assertNotEqual(heading1.text[:15], "URL not found: ")
        except NoSuchElementException:
            pass

    def test_page_status(self):
        """Check all URLs."""
        path = "http://localhost:5014/"
        urls = ("", "index", "about", "join", "events", "contact")

        for url in urls:
            self.check_url(path + url)


if __name__ == "__main__":
    import unittest
    unittest.main()
