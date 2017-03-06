""" Helper function """

from math import floor
from math import log
import numpy as np
import random

from model import add_balance
from model import add_transfer
from model import db
from model import Program
from model import ratio_instance
from model import User


#####################################

def generate_random_color(ntimes, base=(255, 255, 255)):
    """ Generate random pastel blue-greenish and red-orange colors for charts """

    colors = set()

    i = 1

    while len(colors) < ntimes + 1:

            if i % 2 == 0:
                red = random.randint(0, 50)
                green = random.randint(150, 170)
                blue = random.randint(155, 219)

            if i % 2 != 0:
                red = random.randint(240, 250)
                green = random.randint(104, 168)
                blue = random.randint(0, 114)

            if base:
                red = (red + base[0]) / 2
                green = (green + base[1]) / 2
                blue = (blue + base[2]) / 2

            color = (red, green, blue)
            colors.add(color)
            i += 1

    return colors


#####################################

def optimize(user_id, source, goal_amount, commit=False):
    """ Optimizes points transfer """

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

    graph = get_graph_nodes(user_id)

    # example_min_cost: [(16, 0), (212, 0.0), (164, 1.0986122886681098), (6, inf), (170, inf), (187, inf)]
    # example predecessor: {164: 212, 6: None, 170: None, 16: None, 212: 16, 187: None}

    cost, predecessor = bellman_ford(graph, source)
    min_cost = [flow for flow in sorted(cost.items(), key=lambda (node, cost): cost) if flow[1] != float('inf')]

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
                    outgoing_program_id = inner_node.data  # Outgoing program
                    outgoing_program = user.get_balance(outgoing_program_id)

                    receiving_program_id = inner_node.next.data  # Receiving program
                    receiving_program = user.get_balance(receiving_program_id)

                    # Start by transferring from last source
                    if inner_node == path.head:
                        transfer_amount = calc_first_transfer_amount(user, goal_amount, path, source)

                    else:
                        edge_ratio = ratio_instance(outgoing_program_id, receiving_program_id).ratio_to()
                        transfer_amount = calc_balance_ceiling(user.get_balance(outgoing_program_id).current_balance, edge_ratio)

                    # Update to outgoing & receiving program in balances table
                    transfer = ratio_instance(outgoing_program_id, receiving_program_id)
                    transfer_ratio = ratio_instance(outgoing_program_id, receiving_program_id).ratio_to()
                    add_transfer(user_id, outgoing_program_id, receiving_program_id, transfer_amount)

                    # Update to outgoing & receiving program in balances table
                    outgoing_program.transferred_from(transfer_amount)
                    receiving_program.transferred_to(transfer_amount, transfer_ratio)

                    # Update transfer info (outgoing, receiving, transfer_amount, numerator, denominator)
                    key = "Step " + str(i) + ": "

                    suggestion["path"][key] = {}

                    suggestion["path"][key]["outgoing"] = Program.query.get(outgoing_program_id).program_name
                    suggestion["path"][key]["outgoing_url"] = Program.query.get(outgoing_program_id).vendor.url
                    suggestion["path"][key]["receiving"] = Program.query.get(receiving_program_id).program_name
                    suggestion["path"][key]["receiving_url"] = Program.query.get(receiving_program_id).vendor.url
                    suggestion["path"][key]["amount"] = transfer_amount
                    suggestion["path"][key]["numerator"] = transfer.numerator
                    suggestion["path"][key]["denominator"] = transfer.denominator

                    i += 1

                    if commit:
                        db.session.commit()
                        suggestion["confirmation"] = "Your transfers have been committed. Please go to 'Activity' Page to see the transactions."

                    if receiving_program_id == source:
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
            outgoing_program_id = inner_node.data  # Outgoing program
            outgoing_program = user.get_balance(outgoing_program_id)

            receiving_program_id = inner_node.next.data  # Receiving program
            receiving_program = user.get_balance(receiving_program_id)

            # Start by transferring from last source
            if inner_node == path.head:
                transfer_amount = calc_first_transfer_amount(user, goal_amount, path, source)

            else:
                edge_ratio = ratio_instance(outgoing_program_id, receiving_program_id).ratio_to()
                transfer_amount = calc_balance_ceiling(user.get_balance(outgoing_program_id).current_balance, edge_ratio)

            if transfer_amount > 0:
                # Update to outgoing & receiving program in balances table
                transfer = ratio_instance(outgoing_program_id, receiving_program_id)
                transfer_ratio = ratio_instance(outgoing_program_id, receiving_program_id).ratio_to()
                add_transfer(user_id, outgoing_program_id, receiving_program_id, transfer_amount)

                # Update to outgoing & receiving program in balances table
                outgoing_program.transferred_from(transfer_amount)
                receiving_program.transferred_to(transfer_amount, transfer_ratio)

                # Update transfer info (outgoing, receiving, transfer_amount, numerator, denominator)
                key = "Step " + str(i) + ": "

                suggestion["path"][key] = {}

                suggestion["path"][key]["outgoing"] = Program.query.get(outgoing_program_id).program_name
                suggestion["path"][key]["outgoing_url"] = Program.query.get(outgoing_program_id).vendor.url
                suggestion["path"][key]["receiving"] = Program.query.get(receiving_program_id).program_name
                suggestion["path"][key]["receiving_url"] = Program.query.get(receiving_program_id).vendor.url
                suggestion["path"][key]["amount"] = transfer_amount
                suggestion["path"][key]["numerator"] = transfer.numerator
                suggestion["path"][key]["denominator"] = transfer.denominator

                i += 1

                if commit:
                    db.session.commit()
                    suggestion["confirmation"] = "Your transfers have been committed. Please go to 'Activity' Page to see the transactions."

            if receiving_program_id == source:
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

def get_graph_nodes(user_id):
    """ """

    user = User.query.get(user_id)
    receiving = user.user_receiving()

    optimization = {}

    for program in receiving:
        optimization[program.receiving_program] = {}

        outgoing_ratio = user.user_outgoing_for(program.receiving_program)

        for ratio in outgoing_ratio:
            if not optimization.get(ratio.outgoing_program):
                optimization[ratio.outgoing_program] = {}
            optimization[program.receiving_program][ratio.outgoing_program] = -log(ratio.ratio_to())

    return optimization


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


def make_path(current, source, predecessor):

    # Create path for flow
    path = DoublyLinkedList()
    path.append(current)

    # current node is a Node instance
    current_node = path.head

    if current_node.data == source:
        return path

    path.append(predecessor[current_node.data])

    if current_node.next:
        while current_node.next.data != source:
            ancestor = predecessor[current_node.next.data]
            path.append(ancestor)
            current_node = current_node.next

    return path


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
def is_route_possible(user, goal_amount, node):
    """ Return True or False if path is viable """

    return goal_amount <= balance_capacity(user, node)
    return floor((ratio * balance) + balance_capacity(user, current))





### For creating paths in optimization algorithm ###

class Node(object):

    def __init__(self, data, prev, next):
        self.data = data
        self.prev = prev
        self.next = next

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<node:{}>".format(self.data)


class DoublyLinkedList(object):

    head = None
    tail = None

    def append(self, data):
        new_node = Node(data, None, None)
        if self.head is None:
            self.head = self.tail = new_node
        else:
            new_node.prev = self.tail
            new_node.next = None
            self.tail.next = new_node
            self.tail = new_node

    def print_list(self):
        print "Doubly linked list:"
        current = self.head
        while current:
            if current == self.head:
                print current.prev
            print current.data
            if current == self.tail:
                print current.next

            current = current.next


###############################################
"""
The Bellman-Ford algorithm

Graph API:

    iter(graph) gives all nodes
    iter(graph[u]) gives neighbours of u
    graph[u][v] gives weight of edge (u, v)

credit: https://gist.github.com/joninvski/701720
"""


# Step 1: For each node prepare the destination and predecessor
def initialize(graph, source):
    d = {}  # Stands for destination
    p = {}  # Stands for predecessor
    for node in graph:
        d[node] = float('Inf')  # We start admiting that the rest of nodes are very very far
        p[node] = None
    d[source] = 0  # For the source we know how to reach
    return d, p


def relax(node, neighbour, graph, d, p):
    # If the distance between the node and the neighbour is lower than the one I have now
    if d[neighbour] > d[node] + graph[node][neighbour]:
        # Record this lower distance
        d[neighbour] = d[node] + graph[node][neighbour]
        p[neighbour] = node


def bellman_ford(graph, source):
    d, p = initialize(graph, source)

    for i in range(len(graph)-1):  # run this until is converges
        for u in graph:
            for v in graph[u]:  # For each neighbour of u
                relax(u, v, graph, d, p)  # Lets relax it

    # Step 3: check for negative-weight cycles
    for u in graph:
        for v in graph[u]:
            assert d[v] <= d[u] + graph[u][v]

    return d, p
##########################################
