import re
from Functions import get_graph
import networkx as nx
from resources.node import Node
def get_regex(node:Node) -> str:

    regexp = re.sub(r'(?<!EE|NN|SS|WW)(?<!\d)\d+', '#', node.name)
    regexp = re.sub('_[EW]_', '_[EW]_', regexp)
    regexp = re.sub('_[EW]#', '_[EW]#', regexp)
    regexp = re.sub('_(BLN|BLS)_', '_(BLN|BLS)_', regexp)
    regexp = regexp.replace('#', '\d+')

    return regexp

def build_graph(root, x: int, y: int) -> nx.DiGraph:
    G1 = get_graph(root, default_weight=0, xlim_down=x, xlim_up=x, ylim_down=y, ylim_up=y)

    G = nx.DiGraph()
    for edge in G1.edges:
        G.add_edge(Node(edge[0]), Node(edge[1]))

    return G

def get_pips(G: nx.DiGraph, node: str|Node, dir=None) -> set:
    if type(node) == str:
        node = Node(node)

    edges = set(G.in_edges(node)).union(set(G.out_edges(node)))
    if dir == 'uphill':
        pips = {edge for edge in edges if node == edge[1] and edge[0].tile == edge[1].tile}
    elif dir == 'downhill':
        pips = {edge for edge in edges if node == edge[0] and edge[0].tile == edge[1].tile}
    else:
        pips = {edge for edge in edges if edge[0].tile == edge[1].tile}

    return pips

def get_wires(G: nx.DiGraph, node: str|Node) -> set:
    if type(node) == str:
        node = Node(node)

    wires = {neigh for neigh in G.neighbors(node) if neigh.tile != node.tile}
    wires.update(pred for pred in G.predecessors(node) if pred.tile != node.tile)

    return wires

def get_wire_dir(G: nx.DiGraph, node:str|Node) -> str|None:
    if type(node) == str:
        node =Node(node)

    wire = get_wires(G, node)
    if wire:
        wire = wire.pop()
    else:
        return None

    if wire in G.neighbors(node):
        return 'out'
    else:
        return 'in'

def get_wire_dist(G: nx.DiGraph, node:str|Node) -> {tuple}:
    if type(node) == str:
        node =Node(node)

    dir = get_wire_dir(G, node)
    dists = set()
    for wire in get_wires(G, node):
        '''if dir == 'in':
            dists.add((node.get_x_coord - wire.get_x_coord, node.get_y_coord - wire.get_y_coord))
        elif dir == 'out':
            dists.add((wire.get_x_coord - node.get_x_coord, wire.get_y_coord - node.get_y_coord))
        else:
            return None'''
        dists.add((wire.get_x_coord - node.get_x_coord, wire.get_y_coord - node.get_y_coord))

    return dists

