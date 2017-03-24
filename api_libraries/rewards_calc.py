from math import floor
import numpy as np
from models import ratio_instance


def calc_transfer_amount(user, goal_amount=None, path=None, source=None, outgoing_id=None, receiving_id=None, is_first=False):

    if is_first:
        transfer_amount = calc_first_transfer_amount(user, goal_amount, path, source)
    else:
        edge_ratio = ratio_instance(outgoing_id, receiving_id).ratio_to()
        transfer_amount = calc_balance_ceiling(user.get_balance(outgoing_id).current_balance, edge_ratio)

    return transfer_amount


def calc_first_transfer_amount(user, goal_amount, path, source):
    """ The first transfer, from the "outest program", is the only one that is not the full balance capacity. """

    # Start by transferring from last source
    product_ratio_balance = []
    ratios = []

    # We only want to take into account how much could have been transferred thus far
    node = path.head.next

    while node.next:
        # node.data = outgoing_program id
        # node.next.data = receiving_program id

        edge_ratio = ratio_instance(node.data, node.next.data).ratio_to()
        node_balance = calc_balance_ceiling(user.get_balance(node.data).current_balance, edge_ratio)
        product_ratio_balance.append(edge_ratio * node_balance)

        node = node.next

    # We calculate the transfer amount as follows:
    # Step 1) goal_amount minus what has been transferred thus far, which is the product of edge ratio and balance between two prgograms
    # Step 2) result of step 1 divide by the cumulative ratios, np.prod((ratios)), yields the amount needed from the last outgoing program
    # Step 3) result of step 2 divide by the ratio between the last program the one preceding one to get the amount outgoing required

    ratio = ratio_instance(path.head.data, path.head.next.data).ratio_to()

    # Minimum, transfer either goal amount or upto balance ceiling
    transfer_amount = min(((goal_amount - sum(product_ratio_balance)) / np.prod(ratios)) / ratio,
                          calc_balance_ceiling(user.get_balance(path.head.data).current_balance, ratio))

    return transfer_amount


def calc_balance_ceiling(balance, ratio):
    """ Return balance ceiling (maximum divisible by ratio) given balance and ratio """

    if ratio == 0:
        balance_ceiling = balance

    else:
        balance_ceiling = floor(balance * ratio) / ratio

    return balance_ceiling


def balance_capacity(user, current):

    if current.prev is None:
            return 0

    ratio = ratio_instance(current.prev.data, current.data).ratio_to()
    balance = user.get_balance(current.prev.data).current_balance

    current = current.prev

    return floor((ratio * balance) + balance_capacity(user, current))


def is_route_possible(user, goal_amount, node):
    """ Return True or False if path is viable """

    return goal_amount <= balance_capacity(user, node)
