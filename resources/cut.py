from resources.path import *
import networkx as nx

class CUT:

    def __init__(self, origin, pip=None):
        self.pip            = pip
        self.origin         = origin
        self.FFs_set        = set()
        self.paths          = []
        self.LUTs_func_dict = {}

    def get_paths(self):
        paths = []
        source = [node for node in self.G if self.G.in_degree(node) == 0][0]
        sinks = [node for node in self.G if self.G.out_degree(node) == 0]

        for sink in sinks:
            paths.append(nx.shortest_path(self.G, source, sink, weight='weight'))

        return paths

    @property
    def main_path(self):
        path_in = {path for path in self.paths if path.path_type == 'path_in'}.pop()
        path_out = {path for path in self.paths if path.path_type == 'path_out'}.pop()
        main_path = path_in + path_out
        main_path.edges.add(self.pip)
        main_path.path_type = 'main_path'

        return main_path

    @property
    def not_path(self):
        src = {node for node in self.G if self.G.in_degree(node) == 0}.pop()
        path = nx.shortest_path(self.G, src, self.paths[-1][-1].name)
        #used_nodes = [node for node in self.used_nodes if node.name in path]
        #used_nodes.sort(key=lambda x: path.index(x.name))
        #not_path = Path(used_nodes=path, path_type='not')

        return path

    @property
    def nodes(self):
        nodes = set()
        for path in self.paths:
            nodes.update(path.used_nodes)

        return nodes

    @property
    def covered_pips(self):
        tile = f'INT_{self.origin}'
        covered_pips = {self.pip.name}
        paths = {path for path in self.paths if path.path_type in {'path_in', 'path_out'}}
        for path in paths:
            covered_pips.update({pip.name for pip in path.pips if pip.u_tile == tile})

        return covered_pips

    @property
    def G(self):
        if '_G' not in self.__dict__:
            self._G = nx.DiGraph()

        if self.pip:
            self._G.add_edge(*self.pip.name)

        for path in self.paths:
            self._G.add_edges_from(path.edges)

        return self._G

    @property
    def RRG(self):
        RRG = nx.DiGraph()
        RRG.add_edges_from(self.G.edges())
        wires_end = {edge[1] for edge in self.G.edges if CUT.get_tile(edge[0]) != CUT.get_tile(edge[1])}
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
                                n_idx] += f" {{{' '.join(Node(node).port for node in nested_branch)}}}"

        if len(branch_dct[source]) > 1:
            constraint = f"{Node(source).port}"
            for branch in branch_dct[source][1:]:
                constraint += f" {{{' '.join(Node(node).port for node in branch)}}}"

            constraint += f" {' '.join(Node(node).port for node in branch_dct[source][0])}"
        else:
            constraint = f"{Node(source).port} {' '.join(Node(node).port for node in branch_dct[source][0])}"

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

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]
