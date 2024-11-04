from utils import *
from plot import plot_nework

from collections import Counter

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities

def att_nodes(graph: nx.Graph, communities: list[set]):
    
    for idx, community in enumerate(communities):
        nodes_community = {node: {'comunidade': idx} for node in community}
        nx.set_node_attributes(graph, nodes_community)

def communities(file_name: str):
    graph = load_graph(f'{file_name}_net')
    
    nodes = graph.nodes()

    communities = greedy_modularity_communities(graph, 'concordancia')

    att_nodes(graph, communities)

    save_graph(f'{file_name}_net', graph)
