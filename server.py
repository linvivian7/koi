import os
import re

from jinja2 import StrictUndefined
from flask import Flask, render_template, request, session, flash, redirect, jsonify
from flask_bcrypt import Bcrypt
from flask_moment import Moment

from sqlalchemy.orm.exc import NoResultFound

from model import connect_to_db, db, User, Ratio, Balance, Program
from model import Transfer, Action, Feedback, UserFeedback, TransactionHistory

app = Flask(__name__)
app.secret_key = os.environ['APP_SECRET']

app.config["CACHE_TYPE"] = 'null'
bcrypt = Bcrypt(app)

moment = Moment(app)

app.jinja_env.undefined = StrictUndefined

###### Homepage-related routes ######


@app.route('/', methods=['GET', 'POST'])
def homepage():
    """Return homepage."""

    return render_template("homepage.html")


# For processing form only (AJAX)
@app.route("/login", methods=['POST'])
def show_login():
    """Show login form."""

    email = request.form.get('email')
    password = request.form.get('password')

    # Check user existence in database
    try:
        user = User.query.filter_by(email=email).one()

    except NoResultFound:
        return "This email has not been registered"

    user = User.query.filter_by(email=email).one()

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

    # flash("You've been succesfully logged out!")

    return redirect("/")


@app.route("/register", methods=['GET', 'POST'])
def register_user():

    if request.method == 'POST':

        if "user" not in session:
            fname = request.form.get('fname').rstrip()
            lname = request.form.get('lname').rstrip()
            email = request.form.get('email').rstrip()
            pw_hash = bcrypt.generate_password_hash(request.form.get('password'))

            if User.query.filter_by(email=email).first():
                flash("This email has already been registered")
                return redirect('/')

            else:
                match_obj = re.search(r"(\w+)@(\w+\.\w+)", email)

                if match_obj:
                    user = User(email=email, password=pw_hash, fname=fname, lname=lname)
                    db.session.add(user)
                    db.session.commit()

                    flash("You're registered!")
                    session["user"] = user.user_id

                    return redirect("/dashboard")

                else:
                    flash("Please enter a valid email!")
                    return redirect('/')

        else:
            flash("Please log out prior to making a new account")
            return render_template("dashboard.html")

    else:
        return render_template("register.html")


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

    if "user" in session:
        user_id = session["user"]
        user = User.query.options(db.joinedload('balances')).get(user_id)

        balances = user.balances

        programs = Program.query.all()

        return render_template("dashboard.html", balances=balances, programs=programs)
    else:
        flash("Please log in before navigating to the dashboard")
        return redirect('/')


@app.route('/activity')
def transaction_history():
    if "user" in session:
        user_id = session["user"]

        transactions = TransactionHistory.query.filter_by(user_id=user_id).all()

        return render_template("activity.html", activities=transactions)


### D3-related ###
@app.route("/dynamic-d3.json")
def all_d3_info():
    """ """

    all_programs = {}
    i = 0

    dynamic_d3 = {}
    dynamic_d3["nodes"] = []
    dynamic_d3["links"] = []

    outgoing = db.session.query(Ratio).distinct(Ratio.outgoing_program).all()

    for program in outgoing:
        if program.outgoing_program not in all_programs:
            all_programs[program.outgoing_program] = i
            i += 1
            dynamic_d3["nodes"].append({"name": program.outgoing.program_name,
                                       "group": program.outgoing.type_id,
                                       "img": program.outgoing.vendor.img})

    receiving = db.session.query(Ratio).distinct(Ratio.receiving_program).all()

    for program in receiving:
        if program.receiving_program not in all_programs:
            all_programs[program.receiving_program] = i
            i += 1
            dynamic_d3["nodes"].append({"name": program.receiving.program_name,
                                       "group": program.receiving.type_id,
                                       "img": program.receiving.vendor.img})

    ratios = db.session.query(Ratio).join(Program, Program.program_id == Ratio.outgoing_program).all()

    for ratio in ratios:

        dynamic_d3["links"].append({"source": all_programs[ratio.outgoing_program],
                                   "target": all_programs[ratio.receiving_program],
                                   "value": 1})

    return jsonify(dynamic_d3)


@app.route("/custom-d3.json")
def d3_info():
    """ """
    if "user" in session:
        user_id = session["user"]

        # User-specific data
        outgoing = db.session.query(Ratio)\
                             .distinct(Ratio.outgoing_program)\
                             .join(Balance, Balance.program_id == Ratio.outgoing_program)\
                             .filter(Balance.user_id == user_id).all()

        receiving = db.session.query(Ratio)\
                              .distinct(Ratio.receiving_program)\
                              .join(Balance, Balance.program_id == Ratio.receiving_program)\
                              .filter(Balance.user_id == user_id).all()

        user_programs = {}
        i = 0

        custom_d3 = {}
        custom_d3["nodes"] = []
        custom_d3["links"] = []

        # Refactor with eager-load

        for program in receiving:
            if program.receiving_program not in user_programs:
                user_programs[program.receiving_program] = i
                i += 1
                custom_d3["nodes"].append({"name": program.receiving.program_name,
                                           "group": program.receiving.type_id,
                                           "img": program.receiving.vendor.img})

        # O(n^2) refactor if possible
        for program_from in outgoing:
            if program_from.outgoing_program not in user_programs:
                user_programs[program_from.outgoing_program] = i
                i += 1
                custom_d3["nodes"].append({"name": program_from.outgoing.program_name,
                                           "group": program_from.outgoing.type_id,
                                           "img": program_from.outgoing.vendor.img})

            for program_to in receiving:
                ratio = Ratio.query.filter((Ratio.outgoing_program == program_from.outgoing_program) & (Ratio.receiving_program == program_to.receiving_program)).first()
                if ratio:
                    custom_d3["links"].append({"source": user_programs[ratio.outgoing_program],
                                               "target": user_programs[ratio.receiving_program],
                                               "value": 1})
        return jsonify(custom_d3)

    flash("Please sign in first")
    return redirect("/login")


### Balance-related ###


@app.route("/update-balance", methods=["POST"])
def update_balance():
    """Update user balance."""

    if "user" in session:
        user_id = session["user"]

        program = request.form.get("program")
        balance = request.form.get("balance")

        existing_balance = Balance.query.filter((Balance.program_id == program) & (Balance.user_id == user_id)).first()
        update_id = Action.query.filter(Action.action_type == 'Update').one().action_id

        if existing_balance:
            existing_balance.current_balance = balance
            existing_balance.action_id = update_id

        else:
            balance = Balance(user_id=user_id, program_id=program, current_balance=balance, action_id=update_id)
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


@app.route("/transfer-balance", methods=["POST"])
def transfer_balance():
    """transfer user balance from one program to another."""

    if "user" in session:
        user_id = session["user"]

        outgoing = int(request.form.get("outgoing"))
        receiving = int(request.form.get("receiving"))
        amount = int(request.form.get("amount"))

        existing_balance_from = Balance.query.filter((Balance.program_id == outgoing) & (Balance.user_id == user_id)).first()

        # Constraint for positive balance
        if existing_balance_from.current_balance < amount:
            return "Not enough outstanding points for this transfer"

        existing_balance_to = Balance.query.filter((Balance.program_id == receiving) & (Balance.user_id == user_id)).first()

        outgoing_ratio = Ratio.query.filter((Ratio.outgoing_program == outgoing) & (Ratio.receiving_program == receiving)).one()

        numerator = outgoing_ratio.numerator
        denominator = outgoing_ratio.denominator

        if amount % denominator != 0:
            return "Please enter a transferable amount. See ratio above"

        transfer = Transfer(user_id=user_id, outgoing_program=outgoing, receiving_program=receiving, outgoing_amount=amount)
        db.session.add(transfer)

        # Update to receiving program in balances table (must be before outgoing)
        existing_balance_to.current_balance = existing_balance_to.current_balance + amount * (numerator / denominator)
        existing_balance_to.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

        # Update to outgoing program in balances table
        existing_balance_from.current_balance = existing_balance_from.current_balance - amount
        existing_balance_from.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

        # Commit all changes to the database
        db.session.commit()

        # to update DOM through jQuery
        # return json of outgoing program name, receiving program name, and respective balances

        transferred = {}

        transferred["outgoing"] = {"program_id": outgoing,
                                   "program_name": outgoing_ratio.outgoing.program_name,
                                   "current_balance": existing_balance_from.current_balance,
                                   "updated_at": existing_balance_from.updated_at,
                                   }

        transferred["receiving"] = {"program_id": receiving,
                                    "program_name": outgoing_ratio.receiving.program_name,
                                    "current_balance": existing_balance_to.current_balance,
                                    "updated_at": existing_balance_to.updated_at,
                                    }

        return jsonify(transferred)

    flash("Please sign in first")
    return redirect("/login")


@app.route("/ratio-info")
def return_ratio():
    """Return ratio."""

    if "user" in session:
        user_id = session["user"]
        outgoing = request.args.get("outgoing")
        receiving = request.args.get("receiving")

        if receiving:
            ratio = Ratio.query.filter((Ratio.outgoing_program == outgoing) & (Ratio.receiving_program == receiving)).first()
            ratio = str(ratio.numerator / ratio.denominator)

            return jsonify(ratio)

        else:
            receiving = Ratio.query.filter(Ratio.outgoing_program == outgoing)\
                                   .distinct(Ratio.receiving_program)\
                                   .join(Balance, Balance.program_id == Ratio.receiving_program)\
                                   .filter(Balance.user_id == user_id).all()

            program_id = [program.receiving_program for program in receiving]

            program_name = [program.receiving.program_name for program in receiving]

            receiving = {}

            receiving["program_id"] = program_id
            receiving["program_name"] = program_name

            return jsonify(receiving)

    flash("Please sign in first")
    return redirect("/login")


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    app.run(port=5000, host='0.0.0.0')
