#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functional tests for webapp using Selenium."""

import unittest

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


class HTTPStatusTest(unittest.TestCase):
    """Test case checking that all URLs return valid pages."""

    def checkURL(self, url):
        """Check that page content is found."""
        self.browser.get(url)
        try:
            h1 = self.browser.find_element_by_xpath("//h1")
            self.assertNotEqual(h1.text, "Page Not Found")
        except NoSuchElementException:
            pass

    def runTest(self):
        """Check all URLs."""
        self.browser = webdriver.Firefox()
        path = "http://127.0.0.1:5014/"
        urls = ("", "index", "about", "join", "events", "contact")

        for url in urls:
            self.checkURL(path + url)


if __name__ == "__main__":
    unittest.main()
