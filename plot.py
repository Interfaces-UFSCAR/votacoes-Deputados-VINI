from forceatlas2 import forceatlas2
import networkx as nx
import ipysigma as sigma
import pickle


def _apply_force_atlas(graph: nx.Graph):
    I = forceatlas2(G=nx.to_numpy_array(graph,  weight= 'concordancia'))

    positions_dict = {node:{'x':I[i][0], 'y':I[i][1]} for i, node in enumerate(graph.nodes)}

    nx.set_node_attributes(graph, positions_dict)

def plot_nework(network_name: str):
    with open(f'data/networks/{network_name}.pkl', 'rb') as file:
        graph = pickle.load(file)
        
    _apply_force_atlas(graph)
    sigma.Sigma(graph, node_color= "partido", node_label= 'nome').to_html(f'./data/plots/{network_name}.html')