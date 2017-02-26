""" Helper function """

from math import floor
from math import log

from model import add_balance
from model import add_transfer
from model import db
from model import Program
from model import ratio_instance
from model import User


#####################################
def optimize(user_id, source, goal_amount, commit=False):
    """ Optimizes points transfer """

    user = User.query.get(user_id)
    goal = user.get_balance(source)

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
    cost, predecessor = bellman_ford(graph, source)
    min_cost = sorted(cost.items(), key=lambda (node, cost): cost)

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

            if current_node.data == source:
                continue

            path[current].append(predecessor[current_node.data])

            if current_node.next:
                while current_node.next.data != source:
                    ancestor = predecessor[current_node.next.data]
                    path[current].append(ancestor)
                    current_node = current_node.next

            path[current].reverse()

            current_node = path[current].head

            while current_node != path[current].tail:

                # If enough funds at this route
                if is_route_possible(user, goal_amount, path[current].head):
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
                                if node == source:
                                    edge_ratio = 0  # Goal amount already deducted up-front, no need to count current balance at goal program again

                                else:
                                    if node.prev:
                                        edge_ratio = ratio_instance(node.data, node.prev.data).ratio_to()
                                        node_balance = calc_balance_ceiling(user.get_balance(node.data).current_balance, edge_ratio)
                                        product_ratio_balance.append(edge_ratio * node_balance)

                                node = node.prev

                            transfer_amount = (goal_amount - sum(product_ratio_balance)) / ratio_instance(out_node_id, in_node_id).ratio_to()

                        else:
                            edge_ratio = ratio_instance(out_node_id, in_node_id).ratio_to()
                            transfer_amount = calc_balance_ceiling(user.get_balance(out_node_id).current_balance, edge_ratio)

                        transfer = ratio_instance(out_node_id, in_node_id)
                        transfer_ratio = transfer.ratio_to()
                        add_transfer(user_id, out_node_id, in_node_id, transfer_amount)

                        # Update to outgoing & receiving program in balances table
                        out_node.transferred_from(transfer_amount)
                        in_node.transferred_to(transfer_amount, transfer_ratio)

                        # Update transfer info (outgoing, receiving, transfer_amount, numerator, denominator)
                        key = "Step " + str(i) + ": "

                        suggestion["path"][key] = {}

                        suggestion["path"][key]["outgoing"] = Program.query.get(out_node_id).program_name
                        suggestion["path"][key]["receiving"] = Program.query.get(in_node_id).program_name
                        suggestion["path"][key]["amount"] = transfer_amount
                        suggestion["path"][key]["numerator"] = transfer.numerator
                        suggestion["path"][key]["denominator"] = transfer.denominator

                        i += 1

                        if commit:
                            db.session.commit()
                            suggestion["confirmation"] = "Your transfers have been committed. Please go to 'Activity' Page to see the transactions."

                        if in_node_id == source:
                            suggestion["message"] = "You've achieved your goal balance!"
                            return suggestion

                        inner_node = inner_node.prev

                # If not enough funds at this route, try next
                else:
                    current_node = current_node.next
                    continue

    suggestion["message"] = "You do not have enough points to achieve your goal."
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


def calc_balance_ceiling(balance, ratio):
    """ Return balance ceiling (maximum divisible by ratio) given balance and ratio """

    if ratio == 0:
        balance_ceiling = balance

    else:
        balance_ceiling = floor(balance * ratio) / ratio

    return balance_ceiling


def balance_capacity(user, current):

    if current.next is None:
            return 0

    ratio = ratio_instance(current.next.data, current.data).ratio_to()
    balance = user.get_balance(current.next.data).current_balance

    current = current.next

    return floor((ratio * balance) + balance_capacity(user, current))


def is_route_possible(user, goal_amount, node):
    """ Return True or False if path is viable """

    return goal_amount <= balance_capacity(user, node)


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

    def remove(self, value):
        """ Remove node with given value """

        current = self.head

        while current:
            if current.data == value:
                if current.prev:
                    current.prev.next = current.next
                    current.next.prev = current.prev
                else:
                    self.head = current.next
                    current.next.prev = None

            current = current.next

    def reverse(self):
        """ Reversing a DLL in place """

        temp = self.tail
        current = self.tail

        while current.prev:
            self.append(current.prev.data)
            current = current.prev

        self.head = temp
        self.head.prev = None

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

    print len(graph)
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
