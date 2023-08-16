import re
from resources.node import *
from resources.arch_graph import *
from Functions import get_tile, get_port

class Path:

    def __init__(self, device=None, TC=None, nodes=None, path_type=None):
        # as used_nodes are extracted from device, extra used_nodes like s and t are removed
        self.path_type  = path_type
        if device:
            self.nodes      = self.add_nodes(device, nodes)
            self.edges      = self.add_edges(device, nodes)

        if TC and device:
            self.prev_CD    = TC.CD.copy()
            if not self.verify_path(device, TC):
                raise ValueError

    def __repr__(self):
        nodes = [node.name for node in self.nodes]
        return ' -> '.join(nodes)

    def __getitem__(self, item):
        return self.nodes[item]

    def __setitem__(self, key, value: Node):
        self.nodes[key] = value

    def __len__(self):
        return len(self.nodes)

    def __add__(self, obj2):
        path = Path()
        path.nodes = self.nodes + obj2.used_nodes
        path.edges = self.edges.union(obj2.edges)
        path.path_type = self.path_type

        return path

    def str_nodes(self):
        return [node.name for node in self.nodes]

    def add_nodes(self, device: Arch, nodes):
        vertices = []
        for node in nodes:
            vertices.extend(device.get_nodes(name=node))

        return vertices

    def add_edges(self, device, nodes):
        edges = set()
        for edge in zip(nodes, nodes[1:]):
            edges.update(device.get_edges(u=edge[0], v=edge[1]))

        return edges

    def get_LUT_in_type(self, LUT_in):
        if LUT_in == self[-1]:
            type = 'end_node'
        else:
            idx = self.nodes.index(LUT_in)
            if re.match(GM.Unregistered_CLB_out_pattern, self[idx + 1].name):
                type = 'mid_node'
            else:
                type = 'end_node'

        return type

    def get_LUT_func(self, LUT_in_type):
        if LUT_in_type == 'mid_node':
            LUT_func = 'buffer'
        else:
            if self.path_type in ['path_out', 'main_path']:
                LUT_func = 'buffer'
            elif self.path_type == 'not':
                LUT_func = 'not'
            elif self.path_type == 'capture_launch':
                LUT_func = 'partial'
            elif self.path_type == 'capture_sample':
                LUT_func = 'xor'
            else:
                raise ValueError('Wrong Path_type!!!')

        return LUT_func

    def FFs(self):
        FFs_set = {node for node in self.nodes if node.primitive == 'FF'}

        '''if GM.block_mode == 'local':
            for node in filter(lambda x: x.primitive=='FF', self.used_nodes):
                FFs_set.update(device.get_nodes(name=node.name))
        else:
            for node in filter(lambda x: x.primitive=='FF', self.used_nodes):
                FFs_set.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))'''

        return FFs_set

    def LUTs_dict(self):
        dct = {}
        for node in filter(lambda x: x.primitive=='LUT', self.nodes):
            LUT_in_type = self.get_LUT_in_type(node)
            LUT_func = self.get_LUT_func(LUT_in_type)
            dct[node] = LUT_func

        return dct

    def verify_path(self, device, TC):
        result = True
        usage_dct = {}
        if GM.block_mode == 'global':
           LUTs_func_dict = TC.get_global_LUTs(device, self.LUTs_dict())
        else:
            LUTs_func_dict = self.LUTs_dict()

        for LUT_in in LUTs_func_dict:
            required_subLUTs = 2 if (LUT_in.is_i6 or not GM.LUT_Dual) else 1
            key = (LUT_in.tile, LUT_in.bel)
            if key not in usage_dct:
                usage_dct[key] = required_subLUTs
            else:
                usage_dct[key] += required_subLUTs

        for key in usage_dct:
            free_subLUTs = TC.get_LUTs(tile=key[0], letter=key[1], usage='free')
            if usage_dct[key] > len(free_subLUTs):
                result = False
                break

        return result


    @property
    def pips(self):
        return set(filter(lambda x: x.type == 'pip', self.edges))

    @property
    def wires(self):
        return set(filter(lambda x: x.type == 'wire', self.edges))

    @staticmethod
    def get_pips(path):
        pips = set()
        for edge in zip(path, path[1:]):
            if get_tile(edge[0]) == get_tile(edge[1]):
                pips.add(edge)

        return pips