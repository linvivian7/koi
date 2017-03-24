### For creating graph of reward programs in optimization algorithm ###
from models import User
from math import log


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


def bellman_ford_outputs(user_id, source):
    graph = get_graph_nodes(user_id)

    # example_min_cost: [(16, 0), (212, 0.0), (164, 1.0986122886681098), (6, inf), (170, inf), (187, inf)]
    # example predecessor: {164: 212, 6: None, 170: None, 16: None, 212: 16, 187: None}

    cost, predecessor = bellman_ford(graph, source)
    min_cost = [flow for flow in sorted(cost.items(), key=lambda (node, cost): cost) if flow[1] != float('inf') and flow[0] != source]
    min_cost.insert(0, (source, 0))

    return min_cost, predecessor

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
