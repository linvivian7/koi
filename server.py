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
from flask import flash
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session

# SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from model import Action
from model import add_balance
from model import add_transfer
from model import add_user
from model import Balance
from model import connect_to_db
from model import db
from model import Feedback
from model import mapping
from model import Program
from model import ratio_instance
from model import User


app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET']

app.config["CACHE_TYPE"] = 'null'
bcrypt = Bcrypt(app)
moment = Moment(app)

app.jinja_env.undefined = StrictUndefined


###### Homepage-related routes ######

@app.route('/')
def homepage():
    """Return homepage."""

    return render_template("homepage.html")


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
        session["user"] = user.user_id

        return "You've been succesfully logged in"

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

            session["user"] = user.user_id

            return redirect("/dashboard")

        else:
            flash("Please enter a valid email!")
            return redirect('/register')


# For processing form only (AJAX)
@app.route('/contact', methods=['POST'])
def contact_page():
    """ Store information from feedback form."""

    email = request.form.get('email')
    feedback_content = request.form.get('feedback')

    feedback = Feedback(email=email, feedback=feedback_content)
    db.session.add(feedback)
    db.session.commit()

    return "Your feedback has been received!"


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
    """Return data about Melon Sales."""

    user_id = session["user"]
    user = User.query.get(1)
    balances = Balance.query.filter_by(user_id=user_id).options(db.joinedload('program')).all()

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
        color = "rgb" + str(generate_random_color())
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

    user = User.query.options(db.joinedload('balances')).get(session["user"])
    balances = user.balances  # For program-balance table

    i = 1
    program_balances = {}
    for balance in balances:
        program_balances["("+str(balance.balance_id)+")"] = {
            "index": i,
            "program_id": balance.program_id,
            "vendor": balance.program.vendor.vendor_name,
            "program": balance.program.program_name,
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
            transaction_history[key]["change"] = "(" + "{:,}".format(change) + ")"
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

    balance = user.get_balance(program)
    update_id = Action.query.filter(Action.action_type == 'Update').one().action_id

    if balance:
        balance.current_balance = new_balance
        balance.action_id = update_id

    else:
        add_balance(user_id, program, new_balance)

    db.session.commit()

    balance = user.get_balance(program)

    new_bal = {
        "program_id": program,
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
        program_name = [program.receiving.program_name for program in receiving_programs]

        receiving = {
            "program_id": program_id,
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
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    app.run(port=5000, host='0.0.0.0')
