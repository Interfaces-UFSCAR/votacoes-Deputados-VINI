import pickle
import json
from datetime import datetime
from collections.abc import Iterable, Callable
from multiprocessing import Process

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

def save_pdf(file_name: str, pdf_data: bytes):
    with open(f'{file_name}.pdf', 'wb') as pdf:
        pdf.write(pdf_data)

def run_assync(func: Callable, args: Iterable = []):
    process = Process(target= func, args= args)
    process.start()

    return process

def print_log(message: str, flush= True):
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}", flush= flush)

def att_context(context: dict, file_name: str):
    with open(f"./data/context.json", mode= 'r') as context_file:
        full_context = json.load(context_file)
        
    full_context[file_name] |= context
    
    with open(f"./data/context.json", mode= 'w') as context_file:
        json.dump(full_context, context_file)

def get_context(file_name: str) -> dict:
    with open(f"./data/context.json", mode= 'r') as context_file:
        return json.load(context_file)[file_name]
    
def clean_mode(mode: str, context: dict) -> str:
    if context['votacoes'] and context['deputados'] and context['discursos']:
        mode.replace('s', '')

    if context['network']:
        mode.replace('n', '')

    if context['backbone']:
        mode.replace('b', '')

    if context['communities']:
        mode.replace('c', '')

    return mode

    



