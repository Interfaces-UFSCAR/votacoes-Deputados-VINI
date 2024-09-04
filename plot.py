from forceatlas2 import forceatlas2
import networkx as nx
import ipysigma as sigma
import pickle

from utils import *


def _apply_force_atlas(graph: nx.Graph):
    I = forceatlas2(G=nx.to_numpy_array(graph,  weight= 'concordancia'))

    positions_dict = {node:{'x':I[i][0], 'y':I[i][1]} for i, node in enumerate(graph.nodes)}

    nx.set_node_attributes(graph, positions_dict)

def plot_nework(network_name: str, 
                plot_name: str,
                node_color: str):
    
    graph = load_graph(network_name)
        
    _apply_force_atlas(graph)

    sigma.Sigma.set_defaults(800, max_categorical_colors= 50, node_size_range= 5)
    sigma.Sigma(graph, node_color= node_color, node_label= 'nome').to_html(f'./data/plots/{plot_name}.html')