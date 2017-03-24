from models import add_balance
from models import add_transfer
from models import db
from models import Program
from models import ratio_instance
from models import User

import graph

from paths import make_path
from rewards_calc import calc_balance_ceiling
from rewards_calc import calc_first_transfer_amount
from rewards_calc import is_route_possible


def optimize(user_id, source, goal_amount, commit=False):
    """ Optimizes points transfer """
    # pdb.set_trace()

    user = User.query.get(user_id)
    goal = user.get_balance_first(source)
    original_goal = goal_amount

    # counter for paths returned to DOM
    i = 1
    suggestion = {
        "path": {},
        "message": ""
    }

    if goal:
        if goal_amount <= goal.current_balance:
            suggestion["message"] = "You've already achieved your goal."
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
        suggestion["message"] = "There are currently no known relationship between your goal program and those in your profile."
        return suggestion

    for flow in min_cost[:-1]:
        current = flow[0]  # current is an integer for program id

        # example path: None -- 212 -- 16 -- None
        path = make_path(current, source, predecessor)

        current_node = path.tail  # current_node is a node instance

        while current_node != path.head:
            # If enough funds at this route
            if is_route_possible(user, goal_amount, path.tail):
                inner_node = path.head

                while inner_node != path.tail:
                    outgoing_id = inner_node.data  # Outgoing program
                    outgoing_program = user.get_balance(outgoing_id)

                    receiving_id = inner_node.next.data  # Receiving program
                    receiving_program = user.get_balance(receiving_id)

                    # Start by transferring from last source
                    if inner_node == path.head:
                        transfer_amount = calc_first_transfer_amount(user, goal_amount, path, source)

                    else:
                        edge_ratio = ratio_instance(outgoing_id, receiving_id).ratio_to()
                        transfer_amount = calc_balance_ceiling(user.get_balance(outgoing_id).current_balance, edge_ratio)

                    # Update to outgoing & receiving program in balances table
                    transfer_ratio = ratio_instance(outgoing_id, receiving_id).ratio_to()
                    add_transfer(user_id, outgoing_id, receiving_id, transfer_amount)

                    # Update to outgoing & receiving program in balances table
                    outgoing_program.transferred_from(transfer_amount)
                    receiving_program.transferred_to(transfer_amount, transfer_ratio)

                    # Update transfer info (outgoing, receiving, transfer_amount, numerator, denominator)
                    key = "Step " + str(i) + ": "

                    suggestion["path"][key] = create_path_dictionary(outgoing_id, receiving_id, transfer_amount)

                    i += 1

                    if commit:
                        db.session.commit()
                        suggestion["confirmation"] = "Your transfers have been committed. Please go to 'Activity' Page to see the transactions."

                    if receiving_id == source:
                        suggestion["message"] = "You've achieved your goal balance! Would you like to commit this transfer?"
                        return suggestion

                    inner_node = inner_node.next

            # If not enough funds at this route, try next
            else:
                current_node = current_node.prev
                continue

    current = min_cost[-1][0]  # Best, worst-case

    # example path: None -- 212 -- 16 -- None
    path = make_path(current, source, predecessor)
    current_node = path.tail  # current_node is a node instance

    while current_node != path.head:

        inner_node = path.head

        while inner_node != path.tail:
            outgoing_id = inner_node.data  # Outgoing program
            outgoing_program = user.get_balance(outgoing_id)

            receiving_id = inner_node.next.data  # Receiving program
            receiving_program = user.get_balance(receiving_id)

            # Start by transferring from last source
            if inner_node == path.head:
                transfer_amount = calc_first_transfer_amount(user, goal_amount, path, source)

            else:
                edge_ratio = ratio_instance(outgoing_id, receiving_id).ratio_to()
                transfer_amount = calc_balance_ceiling(user.get_balance(outgoing_id).current_balance, edge_ratio)

            if transfer_amount > 0:
                # Update to outgoing & receiving program in balances table
                transfer_ratio = ratio_instance(outgoing_id, receiving_id).ratio_to()
                add_transfer(user_id, outgoing_id, receiving_id, transfer_amount)

                # Update to outgoing & receiving program in balances table
                outgoing_program.transferred_from(transfer_amount)
                receiving_program.transferred_to(transfer_amount, transfer_ratio)

                # Update transfer info (outgoing, receiving, transfer_amount, numerator, denominator)
                key = "Step " + str(i) + ": "

                suggestion["path"][key] = create_path_dictionary(outgoing_id, receiving_id, transfer_amount)

                i += 1

                if commit:
                    db.session.commit()
                    suggestion["confirmation"] = "Your transfers have been committed. Please go to 'Activity' Page to see the transactions."

            if receiving_id == source:
                shortage = original_goal - user.get_balance(source).current_balance
                if shortage == goal_amount:
                    suggestion["message"] = "You currently do not have enough outstanding points for a transfer."
                elif shortage > 0:
                    suggestion["message"] = "You do not have enough points to achieve your goal. The maximum you can reach is {} point(s), which is {} point(s) short of your goal.\
                                             Would you like to commit this transfer?".format("{:,}".format(int(user.get_balance(source).current_balance)), "{:,}".format(int(shortage)))
                else:
                    suggestion["message"] = "You've achieved your goal balance! Would you like to commit this transfer?"
                return suggestion

            inner_node = inner_node.next

    return suggestion


#####################################

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
