import pickle
import json
from datetime import datetime

import networkx as nx

def save_graph(file_name: str, graph: nx.Graph):
    with open(f'./data/networks/{file_name}.pkl', 'wb') as pickle_file:
        pickle.dump(graph, pickle_file)

def load_graph(file_name: str) -> nx.Graph:
    with open(f'./data/networks/{file_name}.pkl', 'rb') as pickle_file:
        graph = pickle.load(pickle_file)

    return graph

def save_json(file_name: str, json_obj: dict | list | tuple):
    with open(f'./data/jsons/{file_name}.json', 'w') as json_file:
        json.dump(json_obj, json_file)

def load_json(file_name: str) -> dict | list | tuple:
    with open(f'./data/jsons/{file_name}.json', 'r') as json_file:
        json_obj = json.load(json_file)

    return json_obj

def print_log(message: str, flush= True):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}", flush= flush)


