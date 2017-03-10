# import pdb
import os
import re

from collections import OrderedDict

# For calculation
from helper import optimize
from helper import generate_random_color

# Flask-related
from jinja2 import StrictUndefined
from flask_bcrypt import Bcrypt
from flask_moment import Moment
from flask import abort
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

# SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from model import Action
from model import add_balance
from model import add_feedback
from model import add_transfer
from model import add_user
from model import Balance
from model import connect_to_db
from model import db
from model import FeedbackCategory
from model import mapping
from model import Program
from model import ratio_instance
from model import User
from model import Vendor

import smtplib

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET']

app.config["CACHE_TYPE"] = 'null'
bcrypt = Bcrypt(app)
moment = Moment(app)

app.jinja_env.undefined = StrictUndefined

# move to security.py
from itsdangerous import URLSafeTimedSerializer
ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


###### Homepage-related routes ######

@app.route('/')
def homepage():
    """Return homepage."""

    contact_us = FeedbackCategory.query.all()

    return render_template("homepage.html", menu=contact_us)


# For processing form only (AJAX)
@app.route('/login', methods=['POST'])
def show_login():
    """Show login form."""

    email = request.form.get('email')
    password = request.form.get('password')

    # Check user existence in database
    try:
        user = User.query.filter_by(email=email).one()

    except NoResultFound:
        return "This email has not been registered"

    # Validate log in information
    if bcrypt.check_password_hash(user.password, password):
        if user.is_email_confirmed is False:
            return "Please verify your email first"
        else:
            session["user"] = user.user_id
            return "Successful login"

    else:
        return "This is not a valid email/password combination"


@app.route("/logout")
def process_logout():
    """Show logout page."""

    session.pop('user')

    return redirect("/")


@app.route('/register')
def register_page():

    return render_template("register.html")


@app.route('/registration', methods=['POST'])
def register_user():

    if "user" in session:
        flash("Please log out prior to registration")
        return redirect('/dashboard')

    fname = request.form.get('fname').rstrip()
    lname = request.form.get('lname').rstrip()
    email = request.form.get('email').rstrip()
    pw_hash = bcrypt.generate_password_hash(request.form.get('password'))

    if User.query.filter_by(email=email).first():
        flash("This email has already been registered")
        return redirect('/register')

    else:
        match_obj = re.search(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)

        if match_obj:
            user = add_user(email, pw_hash, fname, lname)
            db.session.commit()

            gmail_user = os.environ['MAIL_USERNAME']
            gmail_password = os.environ['MAIL_PASSWORD']

            sender = gmail_user
            to = user.email

            subject = "[Welcome to Koi] Account Confirmation"

            token = ts.dumps(user.email, salt='email-confirm-key')

            confirm_url = url_for(
                'confirm_email',
                token=token,
                _external=True)

            body = """Your account was successfully created. Please verify your email within 24 hours. Click the link below to confirm your email address and activate your account:\n{}\nQuestions? Comments? Fill out feedback at https://koirewards.herokuapp.com/.\n- Koi Team :)""".format(confirm_url)

            msg = 'Subject: {}\n\n{}'.format(subject, body)

            try:
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                server.ehlo()
                server.login(gmail_user, gmail_password)
                server.sendmail(sender, to, msg)
                server.close()
            except:
                print 'Something went wrong...'

            flash("A confirmation email has been sent! Please verify your account.")
            return redirect("/")

        else:
            flash("Please enter a valid email.")
            return redirect('/register')


@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except:
        abort(404)

    user = User.query.filter_by(email=email).first()

    user.is_email_confirmed = True

    db.session.add(user)
    db.session.commit()

    flash("Your account has been verified! Please log in.")
    return redirect('/')


# For processing form only (AJAX)
@app.route('/contact', methods=['POST'])
def contact_page():
    """ Store information from feedback form."""

    user_id = session["user"]
    email = request.form.get('email')

    category_id = int(request.form.get('feedback-type').rstrip())

    if category_id == 0:
        flash("Please choose a feedback category before submission")
        return redirect("/")

    elif category_id == 1:
        vendor = request.form.get('vendor').rstrip()
        program = request.form.get('program').rstrip()

        add_feedback(email=email,
                     user_id=user_id,
                     category_id=category_id,
                     vendor=vendor,
                     program=program,
                     )

    elif category_id == 2:
        outgoing = request.form.get('outgoing').rstrip()
        receiving = request.form.get('receiving').rstrip()
        numerator = int(request.form.get('numerator'))
        denominator = int(request.form.get('denominator'))

        add_feedback(email=email,
                     user_id=user_id,
                     category_id=category_id,
                     outgoing=outgoing,
                     receiving=receiving,
                     numerator=numerator,
                     denominator=denominator,
                     )
    else:
        feedback_content = request.form.get('feedback').rstrip()

        add_feedback(email=email,
                     user_id=user_id,
                     category_id=category_id,
                     feedback_content=feedback_content)

    flash("Your feedback has been received!")
    return redirect("/")


###### User Dashboard routes ######

@app.route('/dashboard')
def user_dashboard():
    """Return dashboard."""

    if "user" not in session:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')

    user = User.query.options(db.joinedload('balances')).get(session["user"])

    programs = Program.query.all()  # For update-balance form
    outgoing = user.user_outgoing()  # For transfer-balance form

    return render_template("dashboard.html", programs=programs, outgoing=outgoing)


@app.route('/balance-distribution.json')
def donut_chart_data():
    """Return data about user's points."""

    user = User.query.get(session["user"])
    base = Balance.query.filter_by(user_id=session["user"]).options(db.joinedload('program'))
    balances = base.all()
    count = base.count()
    colors = generate_random_color(ntimes=count)

    data_dict = {
        "labels": [],
        "datasets": [
            {
                "data": [],
                "backgroundColor": [
                ],
                "hoverBackgroundColor": [
                ]
            }]
        }

    for balance in balances:
        color = "rgb" + str(colors.pop())
        data_dict["labels"].append(balance.program.program_name)
        data_dict["datasets"][0]["data"].append(user.get_balance(balance.program_id).current_balance)
        data_dict["datasets"][0]["backgroundColor"].append(color)
        data_dict["datasets"][0]["hoverBackgroundColor"].append(color)

    return jsonify(data_dict)


@app.route('/balances.json')
def balances_json():

    if "user" not in session:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')

    balances = db.session.query(Balance.program_id,
                                Vendor.vendor_name,
                                Program.program_name,
                                Balance.updated_at,
                                Balance.current_balance, Vendor.vendor_name)\
        .join(Program)\
        .join(Vendor)\
        .filter(Balance.user_id == session["user"]).all()

    i = 1
    program_balances = {}
    for balance in balances:
        program_balances["("+str(i)+")"] = {
            "index": i,
            "program_id": balance.program_id,
            "vendor": balance.vendor_name,
            "program": balance.program_name,
            "balance": "{:,}".format(balance.current_balance),
            "timestamp": balance.updated_at,
        }
        i += 1

    return jsonify(program_balances)


@app.route('/activity')
def transaction_history():
    if "user" not in session:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')

    return render_template("activity.html")


@app.route('/activity.json')
def transactions_json():
    if "user" not in session:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')

    user = User.query.get(session["user"])
    transactions = user.get_transactions()

    i = 1
    transaction_history = {}
    for transaction in transactions:
        change = transaction.ending_balance - transaction.beginning_balance
        key = "("+str(transaction.transaction_id)+")"

        transaction_history[key] = {
            "index": i,
            "type": transaction.action.action_type,
            "program": transaction.program.program_name,
            "timestamp": transaction.created_at,
        }

        if transaction.beginning_balance == 0:
            transaction_history[key]["beginning"] = "-"
        else:
            transaction_history[key]["beginning"] = "{:,}".format(transaction.beginning_balance)

        if transaction.ending_balance == 0:
            transaction_history[key]["ending"] = "-"
        else:
            transaction_history[key]["ending"] = "{:,}".format(transaction.ending_balance)

        if change < 0:
            transaction_history[key]["change"] = "(" + "{:,}".format(change * -1) + ")"
        else:
            transaction_history[key]["change"] = "{:,}".format(change)

        i += 1

    return jsonify(transaction_history)


@app.route('/transfers')
def transfer_history():
    if "user" not in session:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')

    return render_template("transfers.html")


@app.route('/transfers.json')
def transfer_json():

    if "user" not in session:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')

    user = User.query.get(session["user"])
    transfers = user.get_transfers()

    i = 1
    transfer_history = {}
    for transfer in transfers:
        ratio = ratio_instance(transfer.outgoing_program, transfer.receiving_program)

        receiving_amount = int(transfer.outgoing_amount * ratio.ratio_to())

        transfer_history["("+str(transfer.transfer_id)+")"] = {
            "transfer_id": i,
            "outgoing": transfer.outgoing.program_name,
            "outgoing_amount": "{:,}".format(transfer.outgoing_amount),
            "receiving": transfer.receiving.program_name,
            "receiving_amount": "{:,}".format(receiving_amount),
            "timestamp": transfer.transferred_at,
            "ratio": str(ratio.numerator) + " : " + str(ratio.denominator),
        }

        i += 1

    return jsonify(transfer_history)


### D3-related ###
@app.route('/dynamic-d3.json')
def all_d3_info():
    """ """

    return jsonify(mapping())


@app.route('/custom-d3.json')
def d3_info():
    """ """
    if "user" not in session:
        flash("Please sign in first")
        return redirect("/login")

    return jsonify(mapping(session["user"]))


@app.route('/process')
def display_process():

    if "user" not in session:
        flash("Please sign in first")
        return redirect("/login")

    return render_template("process.html")


### Balance-related ###
@app.route('/update-balance', methods=['POST'])
def update_balance():
    """Update user balance."""

    if "user" not in session:
        flash("Please sign in first")
        return redirect("/login")

    user_id = session["user"]
    user = User.query.get(user_id)

    program = request.form.get("program")
    new_balance = int(request.form.get("balance"))

    balance = user.get_balance_first(program)
    update_id = Action.query.filter(Action.action_type == 'Update').one().action_id

    if balance:
        balance.current_balance = new_balance
        balance.action_id = update_id

    else:
        add_balance(user_id, program, new_balance)

    db.session.commit()

    vendor = Program.query.get(program).vendor.vendor_name
    balance = user.get_balance(program)

    new_bal = {
        "program_id": program,
        "vendor_name": vendor,
        "program_name": Program.query.get(program).program_name,
        "updated_at": balance.updated_at,
        "current_balance": balance.current_balance
    }

    return jsonify(new_bal)


@app.route('/remove-balance', methods=['POST'])
def remove_balance():
    """Delete user balance."""

    if "user" in session:
        user = User.query.get(session["user"])
        program = request.form.get("program_id")
        balance = user.get_balance(program)

        db.session.delete(balance)
        db.session.commit()

        return "Balance deleted"

    flash("Please sign in first")
    return redirect("/login")


@app.route('/transfer-balance', methods=['POST'])
def transfer_balance():
    """transfer user balance from one program to another."""

    if "user" not in session:
        flash("Please sign in first")
        return redirect("/login")

    user_id = session["user"]
    user = User.query.get(session["user"])

    outgoing_id = int(request.form.get("outgoing"))
    receiving_id = int(request.form.get("receiving"))
    amount = int(request.form.get("amount"))

    balance_from = user.get_balance(outgoing_id)

    # Constraint for positive balance
    if balance_from.current_balance < amount:
        return "Not enough outstanding points for this transfer"

    balance_to = user.get_balance(receiving_id)
    ratio = ratio_instance(outgoing_id, receiving_id)

    if amount % ratio.denominator != 0:
        return "Please enter a transferable amount. See ratio above"

    add_transfer(user_id, outgoing_id, receiving_id, amount)

    # Update to receiving & outgoing program in balances table
    balance_from.transferred_from(amount)
    balance_to.transferred_to(amount, ratio.ratio_to())

    db.session.commit()

    # For updating program balance table via jQuery

    transferred = {}

    transferred["outgoing"] = {"program_id": outgoing_id,
                               "program_name": ratio.outgoing.program_name,
                               "current_balance": balance_from.current_balance,
                               "updated_at": balance_from.updated_at,
                               }

    transferred["receiving"] = {"program_id": receiving_id,
                                "program_name": ratio.receiving.program_name,
                                "current_balance": balance_to.current_balance,
                                "updated_at": balance_to.updated_at,
                                }

    return jsonify(transferred)


@app.route('/ratio.json')
def return_ratio():
    """Return ratio."""

    if "user" not in session:
        flash("Please sign in first")
        return redirect("/login")

    user = User.query.get(session["user"])
    outgoing = request.args.get("outgoing")
    receiving = request.args.get("receiving")

    if receiving:
        ratio = ratio_instance(outgoing, receiving)
        ratio = str(ratio.denominator) + " to " + str(ratio.numerator)
        return jsonify(ratio)

    else:
        receiving_programs = user.user_receiving_for(outgoing)

        program_id = [program.receiving_program for program in receiving_programs]
        vendor_name = [program.receiving.vendor.vendor_name for program in receiving_programs]
        program_name = [program.receiving.program_name for program in receiving_programs]

        receiving = {
            "program_id": program_id,
            "vendor_name": vendor_name,
            "program_name": program_name
        }

        return jsonify(receiving)


### Optimization ###

@app.route('/optimization.json', methods=['POST'])
def optimize_transfer():
    """ Process optimization of points transfer to achieve user goal. """

    user_id = session["user"]

    goal_program = int(request.form.get("goal_program"))
    goal_amount = int(request.form.get("goal_amount"))
    commit = request.form.get("commit")

    suggestion = optimize(user_id, goal_program, goal_amount, commit)

    return jsonify(suggestion)


@app.route('/optimize')
def optimization_dashboard():
    """Display optimization page as well as available outgoing sources"""

    if "user" not in session:
        flash("Please log in first")
        return redirect('/')

    user = User.query.get(session["user"])
    goal = request.args.get("goal_program")

    if not goal:
        programs = Program.query.all()
        return render_template('optimize.html', programs=programs)

    outgoing = OrderedDict(sorted(user.user_outgoing_collection(goal).items()))

    return jsonify(outgoing)


if __name__ == "__main__":
    connect_to_db(app, os.environ.get("DATABASE_URL"))
    db.create_all(app=app)

    DEBUG = "NO_DEBUG" not in os.environ
    PORT = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=PORT)
