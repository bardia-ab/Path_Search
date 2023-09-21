from resources.node import Node
#from resources.configuration2 import Configuration
from resources.path2 import Path, PlainPath
from itertools import product
import networkx as nx

class CUT:
    __slots__ = ('_pip', 'origin', 'paths', '_G', 'FFs', 'subLUTs')
    def __init__(self, origin, pip=None):
        self.pip            = pip
        self.origin         = origin
        self.paths          = []
        self._G             = nx.DiGraph()
        self.FFs            = set()
        self.subLUTs        = set()

    def add_path(self, path: Path, TC):
        self.paths.append(path)
        self.FFs.update(path.FFs())
        self.subLUTs.update(path.subLUTs(TC))

    def get_path(self, path_type) -> Path:
        return next(path for path in self.paths if path.path_type == path_type)

    @property
    def pip(self):
        return self._pip

    @pip.setter
    def pip(self, edge):
        if edge is not None and type(edge[0]) == str:
            edge = (Node(edge[0]), Node(edge[1]))

        self._pip = edge

    @property
    def source(self) -> Node:
        return next(node for node in self.G if self.G.in_degree(node) == 0)

    @property
    def sinks(self) -> {Node}:
        return {node for node in self.G if self.G.out_degree(node) == 0}

    @property
    def main_path(self) -> PlainPath:
        return PlainPath(self.get_path('path_in').nodes + self.get_path('path_out').nodes)

    @property
    def not_path(self) -> PlainPath:
        sink = self.get_path('not')[-1]
        return PlainPath(nx.shortest_path(self.G, self.source, sink))

    @property
    def nodes(self) -> {Node}:
        return {node for path in self.paths for node in path}

    @property
    def covered_pips(self) -> {(Node, Node)}:
        tile = f'INT_{self.origin}'
        return {pip for pip in self.main_path.pips if pip[0].tile == tile}

    @property
    def G(self):
        if self.pip:
            self._G.add_edge(*self.pip)

        for path in self.paths:
            self._G.add_edges_from(path.edges)

        return self._G

    @property
    def RRG(self):
        RRG = nx.DiGraph()
        RRG.add_edges_from(self.G.edges())
        wires_end = {edge[1] for edge in self.G.edges if edge[0].tile != edge[1].tile}
        for node in wires_end:
            new_edges = product(self.G.predecessors(node), self.G.neighbors(node))
            RRG.remove_node(node)
            RRG.add_edges_from(new_edges)

        return RRG

    @property
    def routing_constraint(self):
        branch_dct = {}
        self.get_branches(self.RRG, branch_dct)
        source = [node for node in self.RRG if self.RRG.in_degree(node) == 0][0]
        for key in branch_dct.keys().__reversed__():
            for b_idx, lst in enumerate(branch_dct[key]):
                for n_idx, node in enumerate(lst):
                    if node in branch_dct:
                        for nested_branch in branch_dct[node]:
                            branch_dct[key][b_idx][
                                n_idx] += f" {{{' '.join(node.port for node in nested_branch)}}}"

        if len(branch_dct[source]) > 1:
            constraint = f"{source.port}"
            for branch in branch_dct[source][1:]:
                constraint += f" {{{' '.join(node.port for node in branch)}}}"

            constraint += f" {' '.join(node.port for node in branch_dct[source][0])}"
        else:
            constraint = f"{source.port} {' '.join(node.port for node in branch_dct[source][0])}"

        return f'{{{constraint}}}'

    @staticmethod
    def get_branches(G_net, branch_dct={}):
        source = [node for node in G_net if G_net.in_degree(node) == 0][0]
        for neigh in G_net.neighbors(source):
            T = nx.dfs_tree(G_net, neigh)
            trunk = nx.dag_longest_path(T)
            T.remove_edges_from(set(zip(trunk, trunk[1:])))
            T.remove_nodes_from({node for node in T if nx.is_isolate(T, node)})
            # ports_only = [Node(node).port for node in trunk]
            ports_only = trunk.copy()
            CUT.extend_dict(branch_dct, source, ports_only)
            fanout_nodes = [node for node in trunk if G_net.out_degree(node) > 1]
            if not fanout_nodes:
                continue

            for node in fanout_nodes:
                G_net2 = nx.dfs_tree(T, node)
                CUT.get_branches(G_net2, branch_dct)

    @staticmethod
    def extend_dict(dict_name, key, value, extend=False, value_type='list'):
        if value_type == 'set':
            if key not in dict_name:
                if isinstance(value, str) or isinstance(value, tuple):
                    dict_name[key] = {value}
                else:
                    dict_name[key] = set(value)
            else:
                if isinstance(value, str) or isinstance(value, tuple):
                    dict_name[key].add(value)
                else:
                    dict_name[key].update(value)
        else:
            if extend:
                if key not in dict_name:
                    dict_name[key] = [value]
                else:
                    dict_name[key].extend(value)
            else:
                if key not in dict_name:
                    dict_name[key] = [value]
                else:
                    dict_name[key].append(value)

        return dict_name


if __name__ == '__main__':
    nodes = 'CLEM_X46Y90.CLE_CLE_M_SITE_0_AQ -> INT_X46Y90.LOGIC_OUTS_W14 -> INT_X46Y90.INT_NODE_IMUX_42_INT_OUT1 -> INT_X46Y90.BYPASS_W5 -> INT_X46Y90.INT_NODE_IMUX_48_INT_OUT0 -> INT_X46Y90.IMUX_W10 -> CLEM_X46Y90.CLE_CLE_M_SITE_0_A1'.replace(
        '.', '/').split(' -> ')
    p1 = Path(nodes=nodes)
    cut = CUT('X46Y90', ('INT_X46Y90.LOGIC_OUTS_W14', 'INT_X46Y90.INT_NODE_IMUX_42_INT_OUT1'))
    cut.add_path(p1, None)
    print('hi')