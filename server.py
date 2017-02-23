# from __future__ import print_function
# from ortools.graph import pywrapgraph
from helper import bellman_ford
from math import log, floor, ceil
import numpy as np
import pdb

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


@app.route('/register', methods=['GET', 'POST'])
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
                match_obj = re.search(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)

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
            flash("Please log out prior to registration")
            return redirect('/dashboard')

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

        # For update-balance form
        programs = Program.query.all()

        # For program-balance table
        balances = user.balances

        # FOr transfer-balance form
        outgoing = db.session.query(Ratio)\
                     .distinct(Ratio.outgoing_program)\
                     .join(Balance, Balance.program_id == Ratio.outgoing_program)\
                     .filter(Balance.user_id == user_id).all()

        return render_template("dashboard.html", balances=balances, programs=programs, outgoing=outgoing)
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
@app.route('/dynamic-d3.json')
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


@app.route('/custom-d3.json')
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


@app.route('/update-balance', methods=['POST'])
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


@app.route('/remove-balance', methods=['POST'])
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


@app.route('/transfer-balance', methods=['POST'])
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

        # Update to receiving program in balances table
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


@app.route('/ratio-info')
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


### Optimization ###

@app.route('/optimize', methods=['GET', 'POST'])
def optimize_transfer():
    """ Process optimization of points transfer to achieve user goal. """

    if "user" in session:
        user_id = session["user"]

        if request.method == 'POST':
            goal_program = int(request.form.get("goal_program"))
            goal_amount = int(request.form.get("goal_amount"))

            goal = Balance.query.filter((Balance.user_id == user_id) & (Balance.program_id == goal_program)).first()

            if goal:
                if goal_amount <= goal.current_balance:
                    return "You already have enough points"
                else:
                    goal_amount = goal_amount - goal.current_balance
            else:
                action_id = Action.query.filter(Action.action_type == 'New').one().action_id
                goal = Balance(user_id=user_id, program_id=goal_program, current_balance=0, action_id=action_id)
                db.session.add(goal)

            # Start Bellman-Ford-Moore
            optimization = {}

            receiving = db.session.query(Ratio)\
                                  .distinct(Ratio.receiving_program)\
                                  .join(Balance, Balance.program_id == Ratio.receiving_program)\
                                  .filter(Balance.user_id == user_id).all()

            for program in receiving:
                optimization[program.receiving_program] = {}

                outgoing_ratio = db.session.query(Ratio)\
                                           .join(Balance, Balance.program_id == Ratio.receiving_program)\
                                           .filter((Balance.user_id == user_id) & (Ratio.receiving_program == program.receiving_program))\
                                           .all()

                for ratio in outgoing_ratio:
                    if not optimization.get(ratio.outgoing_program):
                        optimization[ratio.outgoing_program] = {}
                    optimization[program.receiving_program][ratio.outgoing_program] = -log(float(ratio.numerator)/float(ratio.denominator))

            cost, predecessor = bellman_ford(optimization, goal_program)

            min_cost = sorted(cost.items(), key=lambda (node, cost): cost)

            # print "*" * 50
            # print min_cost, predecessor
            # print "*" * 50

            suggestion = {}
            suggestion["start"] = []
            suggestion["end"] = []
            suggestion["amount"] = []
            suggestion["message"] = []

            for flow in min_cost:
                # Assigned for clarity
                cost = flow[1]

                if cost != float('inf'):

                    # Assigned for clarity
                    current_id = flow[0]

                    if current_id == goal_program:
                        continue

                    # create path for each possible flow
                    path = {}
                    ratio = {}
                    prior_node = predecessor[current_id]

                    path[current_id] = []
                    path[current_id].append(current_id)
                    path[current_id].append(prior_node)

                    while prior_node != goal_program:
                        ancestor = predecessor[prior_node]
                        path[current_id].append(ancestor)
                        prior_node = ancestor

                    path[current_id].reverse()
                    ratio[current_id] = []
                    path_traveled = {}
                    i = 0

                    while i < len(path[current_id]) - 1:
                        # pdb.set_trace()

                        path_traveled[current_id] = path[current_id]

                        receiving_node = path[current_id][i]
                        outgoing_node = path[current_id][i+1]

                        ratio_object = Ratio.query.filter((Ratio.outgoing_program == outgoing_node) & (Ratio.receiving_program == receiving_node)).one()
                        flow_ratio = float(ratio_object.numerator) / float(ratio_object.denominator)

                        ratio[current_id].append(flow_ratio)
                        cumulative_ratio = np.prod(ratio[current_id])

                        req_amount = int(ceil(goal_amount / cumulative_ratio))
                        outgoing_node_balance = Balance.query.filter((Balance.user_id == user_id) & (Balance.program_id == outgoing_node)).first()

                        # possible for route to go through
                        if req_amount <= outgoing_node_balance.current_balance:
                            j = 0

                            while j < len(path_traveled[current_id]) - 1:
                                in_node = path_traveled[current_id][j]
                                in_node_obj = Balance.query.filter((Balance.user_id == user_id) & (Balance.program_id == in_node)).first()

                                out_node = path_traveled[current_id][j+1]
                                out_node_obj = Balance.query.filter((Balance.user_id == user_id) & (Balance.program_id == out_node)).first()

                                node_ratio = Ratio.query.filter((Ratio.outgoing_program == out_node) & (Ratio.receiving_program == in_node)).one()
                                flow_cost = float(node_ratio.numerator) / float(node_ratio.denominator)

                                balance_ceiling = floor(out_node_obj.current_balance * flow_cost) / flow_cost

                                transfer_amount = min(goal_amount / flow_cost, int(balance_ceiling / flow_cost))

                                transfer = Transfer(user_id=user_id, outgoing_program=out_node, receiving_program=in_node, outgoing_amount=transfer_amount)
                                db.session.add(transfer)

                                out_node_obj.current_balance = out_node_obj.current_balance - transfer_amount
                                out_node_obj.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

                                in_node_obj.current_balance = in_node_obj.current_balance + transfer_amount * flow_cost
                                in_node_obj.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

                                db.session.commit()

                                if in_node != goal_program:
                                    node_ratio = Ratio.query.filter((Ratio.outgoing_program == in_node) & (Ratio.receiving_program == predecessor[in_node])).one()
                                    pred_obj = Balance.query.filter((Balance.user_id == user_id) & (Balance.program_id == predecessor[in_node])).first()

                                    flow_cost = float(node_ratio.numerator) / float(node_ratio.denominator)

                                    balance_ceiling = floor(in_node_obj.current_balance * flow_cost) / flow_cost

                                    transfer_amount = int(balance_ceiling / flow_cost)

                                    transfer = Transfer(user_id=user_id, outgoing_program=in_node, receiving_program=predecessor[in_node], outgoing_amount=transfer_amount)
                                    db.session.add(transfer)

                                    in_node_obj.current_balance = in_node_obj.current_balance - transfer_amount
                                    out_node_obj.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

                                    pred_obj.current_balance = pred_obj.current_balance + transfer_amount * flow_cost
                                    pred_obj.action_id = Action.query.filter(Action.action_type == 'Transfer').one().action_id

                                    db.session.commit()

                                print "*" * 50
                                print in_node, out_node
                                print balance_ceiling
                                print transfer_amount
                                print "*" * 50

                                goal_amount = goal_amount - transfer_amount
                                j += 1

                            break

                        # continue, try next route
                        else:
                            i += 1
                            continue

            if goal_amount > 0:
                suggestion["message"].append("You don't have enough to achieve your goal balance")

            else:
                suggestion["message"].append("You've achieved your goal!!'")

            return jsonify(suggestion)

        else:
            if request.args.get("goal_program"):
                goal_program = request.args.get("goal_program")
                balance = Balance.query.filter((Balance.program_id == goal_program) & (Balance.user_id == user_id)).first()

                optimize = {}
                optimize["display_program"] = {}
                optimize["outgoing"] = {}

                if balance:
                    optimize["display_program"]["balance"] = balance.current_balance
                    optimize["display_program"]["program_name"] = balance.program.program_name
                else:
                    optimize["display_program"]["balance"] = 0
                    optimize["display_program"]["program_name"] = Program.query.get(goal_program).program_name

                avail_sources = db.session.query(Ratio)\
                                          .distinct(Ratio.outgoing_program)\
                                          .join(Balance, Balance.program_id == Ratio.outgoing_program)\
                                          .filter(Balance.user_id == user_id).all()

                if avail_sources:
                    # Refactor later please
                    for program in avail_sources:
                        identifier = "program" + str(program.outgoing_program)
                        optimize["outgoing"][identifier] = {}
                        optimize["outgoing"][identifier]["program_id"] = program.outgoing_program
                        optimize["outgoing"][identifier]["program_name"] = program.outgoing.program_name
                        optimize["outgoing"][identifier]["numerator"] = program.numerator
                        optimize["outgoing"][identifier]["denominator"] = program.denominator
                        optimize["outgoing"][identifier]["balance"] = Balance.query.filter((Balance.program_id == program.outgoing_program) & (Balance.user_id == user_id)).first().current_balance

                else:
                    optimize["outgoing"] = None

                return jsonify(optimize)

            else:
                programs = Program.query.all()

                return render_template('optimize.html', programs=programs)

    else:
        flash("Please log in first")
        return redirect('/')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    app.run(port=5000, host='0.0.0.0')
