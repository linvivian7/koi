""" Helper function """

from functools import reduce
from math import floor
from math import ceil
from model import ratio_instance
import numpy as np


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

    balance_ceiling = floor(balance * ratio) / ratio

    return balance_ceiling


######################################

def is_route_possible(ratio_list, goal_amount, balance_capacity):
    """ Given the ratio_list, calculate cumulative amount needed, return True or False if path is viable """

    ratio = calc_cumulative_ratio(ratio_list)
    req_amount = calc_required_amount(goal_amount, ratio)

    return req_amount <= balance_capacity


def calc_required_amount(goal_amount, ratio):
    """ """

    return int(ceil(goal_amount / ratio))


def calc_cumulative_ratio(ratio_list):
    """ """

    return np.prod(ratio_list)






















