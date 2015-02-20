#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functional tests for webapp using Selenium."""

import unittest

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException


class HTTPStatusTest(unittest.TestCase):
    """Test case checking that all URLs return valid pages."""

    def setUp(self):
        self.browser = webdriver.Firefox()

    def check_url(self, url):
        """Check that page content is found."""
        self.browser.get(url)
        try:
            heading1 = self.browser.find_element_by_xpath("//h1")
            self.assertNotEqual(heading1.text, "Page Not Found")
        except NoSuchElementException:
            pass

    def test_page_status(self):
        """Check all URLs."""

        path = "http://localhost:5014/"
        urls = ("", "index", "about", "join", "events", "contact")

        for url in urls:
            self.check_url(path + url)


if __name__ == "__main__":
    unittest.main()
