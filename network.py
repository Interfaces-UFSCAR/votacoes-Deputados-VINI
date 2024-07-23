import pandas as pd
import json
import itertools
import networkx as nx
import pickle

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
        weight = (votos_dep1[intersec] == votos_dep2[intersec]).sum()
        
        if weight > 100:
            print(f'({id_dep1})<={weight}=>({id_dep2})', flush= True)

            try:
                graph.add_edge(id_dep1, id_dep2, weight= weight)
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

    nx.write_graphml(graph, 'teste.graphml')


estruturar_rede()