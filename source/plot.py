from fa2 import ForceAtlas2
import networkx as nx
import ipysigma as sigma
import pickle

from .utils import *

CORES_PARTIDOS = {
    "AVANTE": "#d27901",
    "CIDADANIA": "#ff008d",
    "DC": "#000081",
    "DEM": "#1481c5",
    "MDB": "#00933f",
    "NOVO": "#ff6501",
    "PAN": "#006632",
    "PATRI": "#00552a",
    "PATRIOTA": "#00552a",
    "PCB**": "#c30000",
    "PCdoB": "#900",
    "PDC": "#000081",
    "PDC*": "#000081",
    "PDS": "#20308c",
    "PDT": "#243d7d",
    "PEN": "#00552a",
    "PFL": "#1481c5",
    "PHS": "#020203",
    "PJ": "#2171cc",
    "PL": "#0051a0",
    "PL*": "#0051a0",
    "PMB": "#8e2a4e",
    "PMDB": "#00933f",
    "PMN": "#430545",
    "PMR": "#009c39",
    "PODE": "#2db64a",
    "PP": "#68c1ec",
    "PP**": "#68c1ec",
    "PP***": "#68c1ec",
    "PPB": "#68c1ec",
    "PPL": "#004f00",
    "PPR": "#002ac3",
    "PPS": "#ff008d",
    "PR": "#0051a0",
    "PRB": "#009c39",
    "PRN": "#2171cc",
    "PRONA": "#024d3d",
    "PROS": "#f2701a",
    "PRP": "#006db8",
    "PRS": "#ec0301",
    "PRTB": "#4caf2e",
    "PSB": "#ffcc00",
    "PSC": "#2db64a",
    "PSD": "#71c944",
    "PSD*": "#71c944",
    "PSDB": "#0627c6",
    "PSDC": "#000081",
    "PSL": "#193167",
    "PSOL": "#ea454e",
    "PST": "#007500",
    "PSTU": "#ffff00",
    "PT": "#FF0000",
    "PTB": "#005e1a",
    "PTC": "#2171cc",
    "PTdoB": "#d27901",
    "PTN": "#2db64a",
    "PTR": "#68c1ec",
    "PV": "#006428",
    "REDE": "#2ab6c3",
    "REPUBLICANOS": "#009c39",
    "S.PART.": "#808080",
    "SD": "#f2701a",
    "SDD": "#f2701a",
    "SOLIDARIEDADE": "#f2701a",
    "UNIÃO": "#1481c5"
}

FA2 = ForceAtlas2(
                        # Behavior alternatives
                        outboundAttractionDistribution=True,  # Dissuade hubs
                        linLogMode=False,  # NOT IMPLEMENTED
                        adjustSizes=False,  # Prevent overlap (NOT IMPLEMENTED)
                        edgeWeightInfluence=1.0,

                        # Performance
                        jitterTolerance=1.0,  # Tolerance
                        barnesHutOptimize=True,
                        barnesHutTheta=1.2,
                        multiThreaded=False,  # NOT IMPLEMENTED

                        # Tuning
                        scalingRatio=2.0,
                        strongGravityMode=False,
                        gravity=1.0,

                        # Log
                        verbose=True)

def _apply_force_atlas(graph: nx.Graph):
    positions = FA2.forceatlas2(nx.to_numpy_array(graph,  weight= 'concordancia'), iterations=2000)

    positions_dict = {node:{'x':positions[i][0], 'y':positions[i][1]} for i, node in enumerate(graph.nodes)}

    nx.set_node_attributes(graph, positions_dict)

def plot_nework(network_name: str, 
                plot_name: str,
                node_color: str):
    
    graph = load_graph(network_name)
        
    _apply_force_atlas(graph)

    sigma.Sigma.set_defaults(800, max_categorical_colors= 50, node_size_range= 5)
    
    parameters = dict(
            graph= graph, 
            node_color= node_color, 
            node_label= 'nome', 
    )

    if node_color == 'partido':
        parameters |= dict(node_color_palette= CORES_PARTIDOS)
    
    sigma.Sigma(**parameters).to_html(f'./data/plots/{plot_name}.html')


