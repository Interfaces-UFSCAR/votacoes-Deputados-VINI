from utils import *

import networkx as nx
from networkx.algorithms.community import louvain_communities

def att_nodes(graph: nx.Graph, communities: list[set]):
    
    nodes = graph.nodes(data= True)

    for idx, community in enumerate(communities):
        nodes_community = {node: {'comunidade': idx} for node in community}
        nx.set_node_attributes(graph, nodes_community)

def communities(file_name: str):
    graph = load_graph(f'{file_name}_net')
    
    communities = louvain_communities(graph, 'concordancia', seed= 10)

    att_nodes(graph, communities)

    save_graph(f'{file_name}_net', graph)



    