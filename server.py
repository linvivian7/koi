import os
import json
import re
from datetime import datetime, tzinfo, timedelta


class UTC(tzinfo):
    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)

utc = UTC()

from jinja2 import StrictUndefined
from flask import Flask, render_template, request, session, flash, redirect
from flask import make_response, jsonify, send_file
from flask_bcrypt import Bcrypt
from flask_moment import Moment

from sqlalchemy.orm.exc import NoResultFound

from model import connect_to_db, db, User, Ratio, Balance, Program, Action, Transfer, TransactionHistory


app = Flask(__name__)
moment = Moment(app)

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
            match_obj = re.search(r"(\w+)@(\w+\.\w+)", email)

            if match_obj:
                user = User(email=email, password=pw_hash, fname=fname, lname=lname)
                db.session.add(user)
                db.session.commit()

                flash("registered!")
                return redirect('/map')

            else:
                flash("Please enter a valid email!")
                return redirect('/')

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

            return redirect("/dashboard")

        else:
            flash("This is not a valid email/password combination")

    return render_template("login.html")


@app.route("/dashboard")
# @login_required
def show_dashboard():
    """Show user dashboard."""

    if "user" in session:
        user_id = session["user"]
        user = User.query.options(db.joinedload('balances')).get(user_id)

        balances = user.balances
        programs = Program.query.all()
        transactions = TransactionHistory.query.filter_by(user_id=user_id).all()

        return render_template("dashboard.html", programs=programs, balances=balances, user=user, activities=transactions)

    flash("Please sign in first")
    return redirect("/login")


@app.route("/custom-d3.json")
def d3_info():
    """ """

    return 'static/map.json'


@app.route("/update-balance", methods=["POST"])
# @login_required
def update_balance():
    """Update user balance."""

    if "user" in session:
        user_id = session["user"]

        program = request.form.get("program")
        balance = request.form.get("balance")

        existing_balance = Balance.query.filter((Balance.program_id == program) & (Balance.user_id == user_id)).first()

        if existing_balance:
            existing_balance.current_balance = balance

        else:
            balance = Balance(user_id=user_id, program_id=program, current_balance=balance)
            db.session.add(balance)

        db.session.commit()

        new_bal = Balance.query.filter((Balance.program_id == program) & (Balance.user_id == user_id)).first().__dict__

        # for jsonification of User object
        del new_bal['_sa_instance_state']

        new_bal['program_name'] = Program.query.get(program).program_name

        return jsonify(new_bal)

    flash("Please sign in first")
    return redirect("/login")


@app.route("/remove-balance", methods=["POST"])
# @login_required
def remove_balance():
    """Delete user balance."""

    if "user" in session:
        user_id = session["user"]

        program = request.form.get("program_id")

        balance = Balance.query.filter((Balance.program_id == program) & (Balance.user_id == user_id)).one()

        db.session.delete(balance)

        db.session.commit()

        return "deleted"

    flash("Please sign in first")
    return redirect("/login")


@app.route("/logout")
# @login_required
def process_logout():
    """Show logout page."""

    session.pop('user')

    flash("You've been succesfully logged out!")

    return redirect("/")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    app.run(port=5000, host='0.0.0.0')
