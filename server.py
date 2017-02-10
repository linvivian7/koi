import os
import json

from jinja2 import StrictUndefined
from flask import Flask, render_template, request, session, flash, redirect
from flask import make_response, jsonify, send_file
from flask.ext.bcrypt import Bcrypt

from sqlalchemy.orm.exc import NoResultFound

from model import connect_to_db, db, User, Ratio, Transaction, Program


app = Flask(__name__)
app.config["CACHE_TYPE"] = 'null'
bcrypt = Bcrypt(app)

# Required to use Flask sessions and the debug toolbar
app.secret_key = os.environ['APP_SECRET']

app.jinja_env.undefined = StrictUndefined

@app.route('/', methods=['GET', 'POST'])
def homepage():
    """Return homepage."""

    if request.method == 'POST':
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        email = request.form.get('email')
        pw_hash = bcrypt.generate_password_hash(request.form.get('password'))

        if User.query.filter_by(email=email).first():
            flash("the account already exists")
            return redirect('/')

        else:
            user = User(email=email, password=pw_hash, fname=fname, lname=lname)
            db.session.add(user)
            db.session.commit()

            flash("registered!")
            return redirect('/map')

    else:
        return render_template("homepage.html")


@app.route('/map')
def map():
    """Return mapping of reward programs."""

    return render_template("/mapping.html")


@app.route("/login", methods=['GET', 'POST'])
def show_login():
    """Show login form."""

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Check user existence in database
        try:
            User.query.filter_by(email=email).one()

        except NoResultFound:
            flash("This email has not been registered")
            return redirect('/login')

        user = User.query.filter_by(email=email).one()

        # Validate log in information
        if bcrypt.check_password_hash(user.password, password):
            user.authenticated = True
            session["user"] = user.user_id

            return redirect("/")

        else:
            flash("This is not a valid email/password combination")

    return render_template("login.html")


@app.route("/dashboard")
# @login_required
def show_dashboard():
    """Show user dashboard."""

    user_id = 2
    user = User.query.get(user_id)

    transactions = user.transactions

    return render_template("dashboard.html", transactions=transactions, user=user)


@app.route("/logout")
# @login_required
def process_logout():
    """Show logout page."""

    session.pop('user')

    # user = current_user
    # user.authenticated = False
    # db.session.add(user)
    # db.session.commit()
    # logout_user()

    flash("You've been succesfully logged out!")

    return redirect("/")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    app.run(port=5000, host='0.0.0.0')
