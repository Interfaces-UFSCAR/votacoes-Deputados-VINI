import pandas as pd
import json
import itertools
import networkx as nx
import pickle
import scipy.integrate as integrate
import numpy as np

MAP = {
    'Não': -1,
    'Sim': 1,
    'Abstenção': 0
}


def estruturar_rede():
    with open('deputados.json', 'r') as json_file:
        deputados = json.load(json_file)
    
    graph = nx.Graph()

    for id_dep1, id_dep2 in itertools.combinations(deputados.keys(), 2):
        votos_dep1 = pd.Series(deputados[id_dep1]['votos'])
        votos_dep2 = pd.Series(deputados[id_dep2]['votos'])

        intersec = votos_dep1.index.intersection(votos_dep2.index)
        concordancia = (votos_dep1[intersec] == votos_dep2[intersec]).sum()/len(intersec)
        
        if concordancia > 100:
            print(f'({id_dep1})<={concordancia}=>({id_dep2})', flush= True)

            try:
                graph.add_edge(id_dep1, id_dep2, concordancia= concordancia)
            except KeyError:
                graph.add_nodes_from(
                    id_dep1, 
                    nome= deputados[id_dep1]['ultimoStatus']['nomeEleitoral'],
                    partido=  deputados[id_dep1]['ultimoStatus']['siglaPartido'],
                    uf=  deputados[id_dep1]['ultimoStatus']['siglaUf'],
                    condicao=  deputados[id_dep1]['ultimoStatus']['condicaoEleitoral']
                    
                )
                graph.add_nodes_from(
                    id_dep2, 
                    nome= deputados[id_dep2]['ultimoStatus']['nomeEleitoral'],
                    partido=  deputados[id_dep2]['ultimoStatus']['siglaPartido'],
                    uf=  deputados[id_dep2]['ultimoStatus']['siglaUf'],
                    condicao=  deputados[id_dep2]['ultimoStatus']['condicaoEleitoral']
                )
            #
        #

    return graph

def calculate_strength(graph: nx.Graph):
    
    nodes = graph.nodes(data=True)
    
    for node, edges in graph.adjacency():
        strength = 0

        for edge in edges.values:
            strength += edge['concordancia']
        
        node_info = nodes[node]
        node_info |= {'strength': strength}
        graph.add_node(node_info)



def backbone_extraction(graph: nx.Graph, threshold):
    
    calculate_strength(graph)

    nodes = graph.nodes(data=True)

    for edge in graph.edges():
        edge_data = graph.get_edge_data(*edge)
        
        weight = edge_data['concordancia'] / nodes[edge[1]]['strength']
        degree = graph.degree[edge[1]]

        probability = (degree - 1) * (1 - np.power(1 - weight), degree + 1) / (degree + 1)

        edge_data |= {'probability': probability}
        graph.add_edge(*edge, edge_data)


    n_size = len(graph)
    less_probably_edges = iter(sorted(graph.edges(data=True), key= lambda x: x[2]['probability']))

    continue_backbone = True
    while continue_backbone:
        edge = next(less_probably_edges)
        graph.remove_edge(*edge)

        components = nx.connected_components(graph)
        largest_component = max(components, key=len)
        
        if len(largest_component) / n_size <= 0.8:
            continue_backbone = False

graph = estruturar_rede()
backbone_extraction(graph)

nx.write_graphml(graph, 'teste.gml')


