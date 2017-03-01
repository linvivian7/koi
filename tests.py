import os
import unittest
from selenium import webdriver
from server import app


class TestHomepage(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = os.environ['APP_SECRET']
        self.client = app.test_client()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['user_id'] = 1

    def tearDown(self):
        self.browser.quit()

    def test_title(self):
        self.browser.get('http://localhost:5000/')
        self.assertEqual(self.browser.title, 'Welcome to Koi')

    def test_content(self):
        result = self.client.get("/")
        self.assertIn("Smart, optimal tracking", result.data)

if __name__ == "__main__":
    unittest.main()
