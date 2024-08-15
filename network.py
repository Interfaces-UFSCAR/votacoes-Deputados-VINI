import pandas as pd
import json
import itertools
import networkx as nx
import pickle
import numpy as np

MAP_VOTOS = {
    "Sim": 1,
    "Não": -1,
    "Abstenção": 0,
    "Obstrução": 0
}

def estruturar_rede() -> nx.Graph:
    with open('data/deputados.json', 'r') as json_file:
        deputados = json.load(json_file)
    
    graph = nx.Graph()

    for id_dep1, id_dep2 in itertools.combinations(deputados.keys(), 2):
        votos_dep1 = pd.Series(deputados[id_dep1]['votos']).map(MAP_VOTOS)
        votos_dep2 = pd.Series(deputados[id_dep2]['votos']).map(MAP_VOTOS)

        intersec = votos_dep1.index.intersection(votos_dep2.index)
        print

        if len(intersec) > 0:
            concordancia = np.float128((votos_dep1[intersec] == votos_dep2[intersec]).sum()/len(intersec))

            if not id_dep1 in graph:
                graph.add_node(
                    id_dep1, 
                    nome= deputados[id_dep1]['ultimoStatus']['nomeEleitoral'],
                    partido=  deputados[id_dep1]['ultimoStatus']['siglaPartido'],
                    uf=  deputados[id_dep1]['ultimoStatus']['siglaUf'],
                    condicao=  deputados[id_dep1]['ultimoStatus']['condicaoEleitoral']
                    
                )

            if not id_dep2 in graph:
                graph.add_node(
                    id_dep2, 
                    nome= deputados[id_dep2]['ultimoStatus']['nomeEleitoral'],
                    partido=  deputados[id_dep2]['ultimoStatus']['siglaPartido'],
                    uf=  deputados[id_dep2]['ultimoStatus']['siglaUf'],
                    condicao=  deputados[id_dep2]['ultimoStatus']['condicaoEleitoral']
                )
            
            graph.add_edge(id_dep1, id_dep2, concordancia= concordancia)
            #
        #

    return graph


def network():
    print("ESTRUTURAÇÃO DA REDE", flush= True)
    graph = estruturar_rede()

    with open('data/raw.pkl', 'wb') as pickle_file:
        pickle.dump(graph, pickle_file)

    




