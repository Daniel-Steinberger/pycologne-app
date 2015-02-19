from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import unittest


class HTTPStatusTest(unittest.TestCase):

    def checkURL(self, url):
        self.browser.get(url)
        try:
            h1 = self.browser.find_element_by_xpath("//h1")
            self.assertNotEqual(h1.text, "Page Not Found")
        except NoSuchElementException:
            pass

    def runTest(self):
        self.browser = webdriver.Firefox()
        path = "http://127.0.0.1:5014/"
        urls = [
            "", "index", "competition", "task", "submission", "coursematerial",
                "imprint", "privacy"]
        for url in urls:
            self.checkURL(path + url)


if __name__ == "__main__":
    unittest.main()
