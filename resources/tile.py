import re
import Global_Module as GM
import networkx as nx
from resources.node import *
from resources.edge import *

class Tile:
    def __init__(self, name, G):
        self.name   = name
        self.nodes  = self.add_nodes(G)
        self.edges  = set()
        # self.edges is initialized in arch_graph >> init_tiles()
        #self.edges  = self.add_edges(G)

    def __repr__(self):
        return self.name

    @property
    def exact_type(self):
        end_idx = re.search('_X-*\d+Y-*\d+', self.name).regs[0][0]
        return self.name[:end_idx]

    @property
    def type(self):
        if self.name.startswith('INT'):
            return 'INT'
        else:
            return 'CLB'

    @property
    def coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.name)[0]

    @property
    def site_type(self):
        if self.name.startswith('INT'):
            return None
        elif self.name.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @property
    def direction(self):
        if self.name.startswith('INT'):
            dir = 'Center'
        elif self.name.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir

    def add_nodes(self, G: nx.DiGraph):
        nodes = set()
        for node in G:
            if Node(node).tile != self.name:
                continue

            Node1 = Node(node)
            Node1.mode = Node1.set_INT_node_mode(G)
            nodes.add(Node1)

        return nodes

    def add_edges(self, G: nx.DiGraph):
        edges = set()
        for edge in G.edges():
            if list(filter(lambda x: re.search(self.name, x), edge)):
                edges.add(Edge(edge))

        return edges

    def get_nodes(self, mode):
        return set(filter(lambda node: node.mode == mode, self.nodes))

    @property
    def pips(self):
        return {edge for edge in self.edges if edge.type == 'pip'}

    @property
    def wires(self):
        return {edge for edge in self.edges if edge.type == 'wire'}

    def get_clb_nodes(self, type):
        if type == 'LUT_in':
            return set(filter(lambda x: re.match(GM.LUT_in_pattern, x.name), self.nodes))
        elif type == 'FF_in':
            return set(filter(lambda x: re.match(GM.FF_in_pattern, x.name), self.nodes))
        elif type == 'FF_out':
            return set(filter(lambda x: re.match(GM.FF_out_pattern, x.name), self.nodes))
        elif type == 'CLB_out':
            return set(filter(lambda x: re.match(GM.CLB_out_pattern, x.name), self.nodes))
        elif type == 'CLB_muxed':
            return set(filter(lambda x: re.match(GM.MUXED_CLB_out_pattern, x.name), self.nodes))