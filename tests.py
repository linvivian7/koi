import os
import unittest
from server import app
from model import connect_to_db, db
import helper


def add_user_session(TestCaseInstance):
    with TestCaseInstance.client as c:
        with c.session_transaction() as session:
            session['user'] = 1

# Tests that don't involve browsers


class TestRoutesWithDB(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

        connect_to_db(app, "postgresql:///koi")
        app.config['SECRET_KEY'] = os.environ['APP_SECRET']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    def test_login(self):
        email = os.environ['TEST_EMAIL']
        password = os.environ['TEST_PASSWORD']
        result = self.client.post("/login",
                                  data={"email": email, "password": password
                                        },
                                  follow_redirects=True
                                  )
        self.assertIn("You've been succesfully logged in", result.data)

    def test_login_not_registered(self):
        email = "needtoregister"
        password = "imwrong"
        result = self.client.post("/login",
                                  data={"email": email, "password": password
                                        },
                                  follow_redirects=True
                                  )
        self.assertIn("This email has not been registered", result.data)

    def test_login_wrong_password(self):
        email = os.environ['TEST_EMAIL']
        password = "imwrong"
        result = self.client.post("/login",
                                  data={"email": email, "password": password
                                        },
                                  follow_redirects=True
                                  )
        self.assertIn("This is not a valid email/password combination", result.data)

    def test_register_invalid_email(self):
        result = self.client.post("/registration",
                                  data={"fname": "meow",
                                        "lname": "smith",
                                        "email": "imnotreal@.com",
                                        "password": "alsonotreal"},
                                  follow_redirects=True,
                                  )
        self.assertIn("Please enter a valid email", result.data)

    def test_logout(self):
        add_user_session(self)

        result = self.client.get("/logout", follow_redirects=True)
        self.assertIn("Get Started", result.data)

        with self.client as c:
            with c.session_transaction() as session:
                self.assertIsNone(session.get("user"))


class SimpleDashboardPages(unittest.TestCase):

    def setUp(self):
        """Stuff to do before every test."""

        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = os.environ['APP_SECRET']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
        self.client = app.test_client()

        add_user_session(self)
        connect_to_db(app, "postgresql:///koi")

    def homepage(self):
        result = self.client.get("/")
        self.assertIn("feedback-form", result.data)

    def test_ratio(self):
        result = self.client.get("/ratio.json",
                                 query_string={"outgoing": 164,
                                               "receiving": 212,
                                               })
        self.assertIn("3 to 1", result.data)


class TestOptimization(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        app.config['TESTING'] = True

        connect_to_db(app, "postgresql:///koi")
        app.config['SECRET_KEY'] = os.environ['APP_SECRET']
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    def test_bellman_ford(self):
        graph = {68: {212: -0.0}, 134: {187: -0.0, 212: 0.6931471805599453}, 170: {187: -0.0}, 16: {212: -0.0}, 212: {164: 1.0986122886681098}, 164: {}, 187: {}, 61: {212: -0.0}, 95: {187: -0.0}}
        source = 170
        d, p = helper.bellman_ford(graph, source)
        self.assertEqual(d, {164: float('inf'), 134: float('inf'), 170: 0, 16: float('inf'), 212: float('inf'), 68: float('inf'), 187: 0.0, 61: float('inf'), 95: float('inf')})
        self.assertEqual(p, {164: None, 134: None, 170: None, 16: None, 212: None, 68: None, 187: 170, 61: None, 95: None})

if __name__ == "__main__":
    unittest.main()
