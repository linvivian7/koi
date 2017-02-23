# import pdb
import os
import re

# For calculation
from math import log
from helper import bellman_ford
from helper import calc_balance_ceiling
from helper import DoublyLinkedList
from helper import is_route_possible

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
from model import connect_to_db
from model import db
from model import Feedback
from model import Program
from model import ratio_instance
from model import Ratio
from model import TransactionHistory
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

    user_id = session["user"]
    user = User.query.options(db.joinedload('balances')).get(user_id)

    # For update-balance form
    programs = Program.query.all()

    # For program-balance table
    balances = user.balances

    # For transfer-balance form
    outgoing = user.user_outgoing()

    return render_template("dashboard.html", balances=balances, programs=programs, outgoing=outgoing)


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

    dynamic_d3 = {
        "nodes": [],
        "links": []
    }

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
    if "user" not in session:
        flash("Please sign in first")
        return redirect("/login")

    user_id = session["user"]
    user = User.query.get(user_id)

    # User-specific data
    outgoing = user.user_outgoing()
    receiving = user.user_receiving()

    user_programs = {}
    custom_d3 = {
        "nodes": [],
        "links": []
    }

    # Refactor with eager-load

    i = 0
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
            ratio = ratio_instance(program_from.outgoing_program, program_to.receiving_program)
            if ratio:
                custom_d3["links"].append({"source": user_programs[ratio.outgoing_program],
                                           "target": user_programs[ratio.receiving_program],
                                           "value": 1})
    return jsonify(custom_d3)


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
    new_balance = request.form.get("balance")

    balance = user.get_balance(program)
    update_id = Action.query.filter(Action.action_type == 'Update').one().action_id

    if balance:
        balance.current_balance = new_balance
        balance.action_id = update_id

    else:
        add_balance(user_id, program, new_balance, update_id)

    db.session.commit()

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
        user_id = session["user"]
        user = User.query.get(user_id)
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
    user = User.query.get(user_id)

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

    user_id = session["user"]
    user = User.query.get(user_id)
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
    user = User.query.get(user_id)

    goal_program = int(request.form.get("goal_program"))
    goal_amount = int(request.form.get("goal_amount"))

    goal = user.get_balance(goal_program)

    if goal:
        if goal_amount <= goal.current_balance:
            return "You already have enough points"
        else:
            goal_amount = goal_amount - goal.current_balance
    else:
        action_id = Action.query.filter(Action.action_type == 'New').one().action_id
        add_balance(user_id, goal_program, 0, action_id)
        db.session.commit()

    # Start Bellman-Ford-Moore
    optimization = {}

    receiving = user.user_receiving()

    for program in receiving:
        optimization[program.receiving_program] = {}

        outgoing_ratio = user.user_outgoing_for(program.receiving_program)

        for ratio in outgoing_ratio:
            if not optimization.get(ratio.outgoing_program):
                optimization[ratio.outgoing_program] = {}
            optimization[program.receiving_program][ratio.outgoing_program] = -log(ratio.ratio_to())

    cost, predecessor = bellman_ford(optimization, goal_program)

    min_cost = sorted(cost.items(), key=lambda (node, cost): cost)

    suggestion = {
        "start": [],
        "end": [],
        "amount": [],
        "message": []
    }

    for flow in min_cost:
        # Assigned for clarity
        cost = flow[1]

        if cost != float('inf'):
            # current is an integer for program id
            current = flow[0]

            # Create path for each possible flow
            path = {}
            path[current] = DoublyLinkedList()
            path[current].append(current)

            # current node is a Node instance
            current_node = path[current].head

            if current_node.data == goal_program:
                continue

            path[current].append(predecessor[current_node.data])

            if current_node.next:
                while current_node.next.data != goal_program:
                    ancestor = predecessor[current_node.next.data]
                    path[current].append(ancestor)
                    current_node = current_node.next

            path[current].print_list()
            path[current].reverse()
            path[current].print_list()

            ratio = {
                current: []
            }

            current_node = path[current].head

            while current_node != path[current].tail:
                outgoing_node = current_node.next.data
                receiving_node = current_node.data

                flow_ratio = ratio_instance(outgoing_node, receiving_node).ratio_to()
                ratio[current].append(flow_ratio)
                balance_capacity = user.get_balance(outgoing_node).current_balance

                # If enough funds at this route
                if is_route_possible(ratio[current], goal_amount, balance_capacity):
                    inner_node = path[current].tail

                    while inner_node != path[current].head:
                        out_node_id = inner_node.data  # Outgoing program
                        out_node = user.get_balance(out_node_id)

                        in_node_id = inner_node.prev.data  # Receiving program
                        in_node = user.get_balance(in_node_id)

                        # Start by transferring from last source
                        if inner_node == path[current].tail:
                            product_ratio_balance = []

                            node = inner_node.prev

                            while node:
                                if node == goal_program:
                                    edge_ratio = 0  # Goal amount already deducted up-front, no need to count current balance at goal program again

                                else:
                                    if node.prev:
                                        edge_ratio = ratio_instance(node.data, node.prev.data).ratio_to()
                                        node_balance = calc_balance_ceiling(user.get_balance(node.data).current_balance, edge_ratio)
                                        product_ratio_balance.append(edge_ratio * node_balance)

                                node = node.prev

                            sum(product_ratio_balance)
                            transfer_amount = (goal_amount - sum(product_ratio_balance)) / ratio_instance(out_node_id, in_node_id).ratio_to()

                        else:
                            edge_ratio = ratio_instance(out_node_id, in_node_id).ratio_to()
                            transfer_amount = calc_balance_ceiling(user.get_balance(out_node_id).current_balance, edge_ratio)

                        transfer_ratio = ratio_instance(out_node_id, in_node_id).ratio_to()
                        add_transfer(user_id, out_node_id, in_node_id, transfer_amount)

                        # Update to outgoing & receiving program in balances table
                        out_node.transferred_from(transfer_amount)
                        in_node.transferred_to(transfer_amount, transfer_ratio)
                        db.session.commit()

                        if in_node_id == goal_program:
                            suggestion["message"].append("You've achieved your goal balance")
                            return jsonify(suggestion)

                        inner_node = inner_node.prev

                # If not enough funds at this route, try next
                else:
                    current_node = current_node.next
                    continue

    return jsonify(suggestion)


@app.route('/optimize')
def optimization_dashboard():
    """Display optimization page as well as available outgoing sources"""

    if "user" not in session:
        flash("Please log in first")
        return redirect('/')

    user_id = session["user"]
    user = User.query.get(user_id)
    goal_program = request.args.get("goal_program")

    if not goal_program:
        programs = Program.query.all()
        return render_template('optimize.html', programs=programs)

    balance = user.get_balance(goal_program)

    optimize = {
        "display_program": {},
        "outgoing": {}
    }

    if balance:
        optimize["display_program"]["balance"] = balance.current_balance
        optimize["display_program"]["program_name"] = balance.program.program_name
    else:
        optimize["display_program"]["balance"] = 0
        optimize["display_program"]["program_name"] = Program.query.get(goal_program).program_name

    avail_sources = user.user_outgoing()

    if avail_sources:
        for program in avail_sources:
            optimize["outgoing"][program.outgoing_program] = {
                "program_name": program.outgoing.program_name,
                "balance": user.get_balance(program.outgoing_program).current_balance
            }

    return jsonify(optimize)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)
    app.run(port=5000, host='0.0.0.0')
