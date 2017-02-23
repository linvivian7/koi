""" Helper function """

from functools import reduce
from math import floor
from math import ceil
import numpy as np


class Node(object):
    """ Node in a doubly linked list """

    def __init__(self, data, prev, next):
        self.data = data
        self.prev = prev
        self.next = next


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


##########################################
def lcm(a, b):
    if a > b:
        greater = a
    else:
        greater = b

    while True:
        if greater % a == 0 and greater % b == 0:
            lcm = greater
            break
        greater += 1

    return lcm


def get_lcm_for(denom_list):
    return reduce(lambda x, y: lcm(x, y), denom_list)


##########################################
"""
The Bellman-Ford algorithm

Graph API:

    iter(graph) gives all nodes
    iter(graph[u]) gives neighbours of u
    graph[u][v] gives weight of edge (u, v)
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


#####################################

def calc_balance_ceiling(balance, ratio):
    """ Return balance ceiling (maximum divisible by ratio) given balance and ratio """

    if ratio == 0:
        balance_ceiling = balance

    else:
        balance_ceiling = floor(balance * ratio) / ratio

    return balance_ceiling


######################################

def is_route_possible(ratio_list, goal_amount, balance_capacity):
    """ Given the ratio_list, calculate cumulative amount needed, return True or False if path is viable """

    req_amount = calc_required_amount(goal_amount, ratio_list)

    return req_amount <= balance_capacity


def calc_required_amount(goal_amount, ratio_list):
    """ """
    ratio = np.prod(ratio_list)

    return int(ceil(goal_amount / ratio))
