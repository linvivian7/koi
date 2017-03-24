from models import add_balance
from models import db
from models import Program
from models import ratio_instance
from models import User

import graph

from paths import make_path
from rewards_calc import calc_transfer_amount
from rewards_calc import is_route_possible


def optimize(user_id, source, goal_amount, commit=False):
    """ Optimizes points transfer """

    user = User.query.get(user_id)
    goal = user.get_balance_first(source)
    original_goal = goal_amount

    # counter for paths returned to DOM
    suggestion = {
        "path": {},
        "message": ""
    }

    if goal:
        if goal_amount <= goal.current_balance:
            suggestion["message"] = add_message(status="fulfilled")
            return suggestion
        else:
            goal_amount = goal_amount - goal.current_balance
    else:
        add_balance(user_id, source, 0)

    if commit:
        db.session.commit()

    min_cost, predecessor = graph.bellman_ford_outputs(user_id, source)

    # If no other programs are connected to goal program
    if len(min_cost) == 1:
        suggestion["message"] = add_message(status="no relation")
        return suggestion

    for flow in min_cost[:-1]:
        current = flow[0]  # current is an integer for program id

        # example path: None -- 212 -- 16 -- None
        path = make_path(current, source, predecessor)

        current_node = path.tail  # current_node is a node instance

        while current_node != path.head:
            # If enough funds at this route
            if is_route_possible(user, goal_amount, path.tail):
                suggestion["path"], suggestion["message"] = process(path, user, goal_amount, source, original_goal, commit)
                return suggestion

            # If not enough funds at this route, try next
            else:
                current_node = current_node.prev
                continue

    current = min_cost[-1][0]  # Best, worst-case

    # example path: None -- 212 -- 16 -- None
    path = make_path(current, source, predecessor)
    current_node = path.tail  # current_node is a node instance

    suggestion["path"], suggestion["message"] = process(path, user, goal_amount, source, original_goal, commit)

    return suggestion


#####################################

def process(path, user, goal_amount, source, original_goal, commit):
    inner_node = path.head

    i = 1
    suggestion = {
        "path": {},
        "message": ""
    }

    while inner_node != path.tail:
        outgoing_id = inner_node.data  # Outgoing program
        receiving_id = inner_node.next.data  # Receiving program

        # Start by transferring from last source
        if inner_node == path.head:
            transfer_amount = calc_transfer_amount(user=user, goal_amount=goal_amount, path=path, source=source, is_first=True)

        else:
            transfer_amount = calc_transfer_amount(user=user, outgoing_id=outgoing_id, receiving_id=receiving_id, is_first=False)

        if transfer_amount > 0:
            # Update to transaction in transfers table
            user.add_transfer(outgoing_id, receiving_id, transfer_amount)

            # Update transfer info (outgoing, receiving, transfer_amount, numerator, denominator)
            key = "Step " + str(i) + ": "

            suggestion["path"][key] = create_path_dictionary(outgoing_id, receiving_id, transfer_amount)

            i += 1

            if commit:
                db.session.commit()
                suggestion["confirmation"] = add_message(status="commit")

        if receiving_id == source:
            shortage = original_goal - user.get_balance(source).current_balance
            if shortage == goal_amount:
                suggestion["message"] = add_message(status="insufficient funds")
            elif shortage > 0:
                suggestion["message"] = add_message(status="partial funds", user=user, source=source, shortage=shortage)
            else:
                suggestion["message"] = add_message(status="achieved goal")
            return suggestion["path"], suggestion["message"]

        inner_node = inner_node.next

    return suggestion["path"], suggestion["message"]


def add_message(status, user=None, source=None, shortage=None):
    if status == "fulfilled":
        return "You've already achieved your goal."
    elif status == "no relation":
        return "There is currently no known relationship between your goal program and those in your profile."
    elif status == "insufficient funds":
        return "You currently do not have enough outstanding points for a transfer."
    elif status == "partial funds":
        return "You do not have enough points to achieve your goal. The maximum you can reach is {} point(s), which is {} point(s) short of your goal.\
                Would you like to commit this transfer?".format("{:,}".format(int(user.get_balance(source).current_balance)), "{:,}".format(int(shortage)))
    elif status == "achieved goal":
        return "You've achieved your goal balance! Would you like to commit this transfer?"
    elif status == "commit":
        return "Your transfers have been committed. Please go to 'Activity' Page to see the transactions."


def create_path_dictionary(outgoing_id, receiving_id, amount):
    path = {}
    transfer = ratio_instance(outgoing_id, receiving_id)

    path["outgoing"] = Program.query.get(outgoing_id).program_name
    path["outgoing_url"] = Program.query.get(outgoing_id).vendor.url
    path["receiving"] = Program.query.get(receiving_id).program_name
    path["receiving_url"] = Program.query.get(receiving_id).vendor.url
    path["amount"] = amount
    path["numerator"] = transfer.numerator
    path["denominator"] = transfer.denominator

    return path
