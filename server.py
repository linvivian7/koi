import os
import re

from jinja2 import StrictUndefined
from flask import Flask, render_template, request, session, flash, redirect, jsonify
from flask_bcrypt import Bcrypt
from flask_moment import Moment

from sqlalchemy.orm.exc import NoResultFound

from model import connect_to_db, db, User, Ratio, Balance, Program, TransactionHistory
from model import Transfer


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

    if "user" in session:
        user_id = session["user"]
        user = User.query.options(db.joinedload('balances')).get(user_id)

        # User-specific data
        balances = user.balances
        transactions = TransactionHistory.query.filter_by(user_id=user_id).all()

        # for datalist generation
        programs = Program.query.all()

        outgoing = db.session.query(Ratio)\
                             .distinct(Ratio.outgoing_program)\
                             .join(Balance, Balance.program_id == Ratio.outgoing_program)\
                             .filter(Balance.user_id == user_id).all()

        return render_template("homepage.html", programs=programs, balances=balances, user=user, activities=transactions, outgoing=outgoing)

    else:
        return render_template("homepage.html")


@app.route('/about')
def about_page():
    """Return about page."""

    return render_template("/about.html")


@app.route('/contact')
def contact_page():
    """Return contact page and feedback form."""

    return render_template("/contact.html")


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


@app.route("/custom-d3.json")
def d3_info():
    """ """

    custom_d3 = {}

    custom_d3["nodes"] = []

    custom_d3["links"] = []

    programs = Program.query.all()

    for program in programs:
        custom_d3["nodes"].append({"name": program.program_name,
                                   "group": program.type_id})

    ratios = db.session.query(Ratio.outgoing_program,
                              Ratio.receiving_program).join(Program, Program.program_id == Ratio.outgoing_program).all()

    # print "*" * 40
    # print ratios
    # print "*" * 40

    for outgoing, receiving in ratios:
        custom_d3["links"].append({"source": outgoing-1,
                                   "target": receiving-1,
                                   "value": 1})

    print custom_d3

    return jsonify(custom_d3)


@app.route("/ratio-info")
# @login_required
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

            print "*" * 40
            print outgoing
            print receiving
            print "*" * 40

            return jsonify(receiving)

    flash("Please sign in first")
    return redirect("/login")


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


@app.route("/transfer-balance", methods=["POST"])
# @login_required
def transfer_balance():
    """transfer user balance from one program to another."""

    if "user" in session:
        user_id = session["user"]

        outgoing = request.form.get("outgoing")
        receiving = request.form.get("receiving")
        amount = int(request.form.get("amount"))

        existing_balance_from = Balance.query.filter((Balance.program_id == outgoing) & (Balance.user_id == user_id)).first()

        # Constraint for positive balance
        if existing_balance_from.current_balance < amount:
            return "Not enough outstanding points for this transfer"

        existing_balance_to = Balance.query.filter((Balance.program_id == receiving) & (Balance.user_id == user_id)).first()

        try:
            outgoing_ratio = Ratio.query.filter((Ratio.outgoing_program == outgoing) & (Ratio.receiving_program == receiving)).one()
            print "*" * 40
            print outgoing_ratio
            print "*" * 40

            numerator = outgoing_ratio.numerator
            denominator = outgoing_ratio.denominator

            print "*" * 40
            print numerator, denominator
            print "*" * 40
        except:
            flash("There's no ratio for this yet! Please submit your input in the feedback form")
            redirect("/login")

        if amount % denominator != 0:
            flash("Please enter a transferable amount. See ratio on the dashboard view")
            redirect("/#home")

        existing_balance_to.current_balance = existing_balance_to.current_balance + amount * (numerator / denominator)
        existing_balance_from.current_balance = existing_balance_from.current_balance - amount

        db.session.add(existing_balance_from)
        db.session.add(existing_balance_to)

        db.session.commit()

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
        print "*" * 40
        print transferred
        print "*" * 40

        return jsonify(transferred)

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
