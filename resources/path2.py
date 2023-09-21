import re
from resources.node import Node
import Global_Module as GM
from abc import ABC, abstractmethod
from resources.primitive import FF

class Path_ABC(ABC):
    @abstractmethod
    def __init__(self):
        pass

    def __repr__(self):
        nodes = [node.name for node in self.nodes]
        return ' -> '.join(nodes)

    def __eq__(self, other):
        return type(self) == type(other) and self.nodes == other.nodes

    def __hash__(self):
        return hash((self.nodes, ))

    def __getitem__(self, item):
        return self.nodes[item]

    def __setitem__(self, key, value: Node):
        self.nodes[key] = value

    def __len__(self):
        return len(self.nodes)

    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx >= len(self):
            raise StopIteration
        else:
            self.idx += 1
            return self[self.idx - 1]

    @property
    def nodes(self):
        return self._nodes

    @nodes.setter
    def nodes(self, vertices: [str|Node]):
        self._nodes = []
        for vertex in vertices:
            if type(vertex) == str:
                if '/' not in vertex:
                    continue            #skip virtual nodes

                vertex = Node(vertex)

            self._nodes.append(vertex)

    @property
    def edges(self) -> {(Node, Node)}:
        return set(zip(self.nodes, self.nodes[1:]))

    @property
    def pips(self) -> {(Node, Node)}:
        return set(filter(lambda x: x[0].tile == x[1].tile, self.edges))

    @property
    def wires(self) -> {(Node, Node)}:
        return set(filter(lambda x: x[0].tile != x[1].tile, self.edges))

    def str_nodes(self):
        return [node.name for node in self.nodes]


class PlainPath(Path_ABC):
    __slots__ = ('_nodes', 'idx')
    def __init__(self, nodes):
        self.nodes = nodes


class Path(Path_ABC):
    __slots__ = ('path_type', '_nodes', 'prev_CD', 'idx')
    def __init__(self, TC=None, nodes=None, path_type=None):
        self.path_type  = path_type
        self.nodes      = nodes

        if TC:
            self.prev_CD    = TC.CD.copy()
            self.verify_path(TC)

    def __add__(self, obj2):
        path = Path()
        path.nodes = self.nodes + obj2.nodes
        path.path_type = self.path_type

        return path

    def get_LUT_in_type(self, LUT_in):
        type = 'end_node'
        if LUT_in != self[-1]:
            if re.match(GM.Unregistered_CLB_out_pattern, self[self.nodes.index(LUT_in) + 1].name):
                type = 'mid_node'

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
        return (FF(node.bel_key, node) for node in self.nodes if node.primitive == 'FF')
    def subLUTs(self, TC):
        for LUT_in in filter(lambda x: x.primitive=='LUT', self.nodes):
            LUT_in_type = self.get_LUT_in_type(LUT_in)
            LUT_output = None if LUT_in_type == 'end_node' else self[self.nodes.index(LUT_in) + 1]
            LUT_func = self.get_LUT_func(LUT_in_type)
            yield TC.get_subLUT(LUT_in, LUT_output, LUT_func)

    def verify_path(self, TC):
        result = True
        try:
            subLUTs = TC.get_global_subLUTs(self.subLUTs(TC)) if GM.block_mode == 'global' else self.subLUTs(TC)
        except:
            raise ValueError('Path Verification Failed!')

        return result


if __name__ == '__main__':
    nodes = 'CLEM_X46Y90.CLE_CLE_M_SITE_0_AQ -> INT_X46Y90.LOGIC_OUTS_W14 -> INT_X46Y90.INT_NODE_IMUX_42_INT_OUT1 -> INT_X46Y90.BYPASS_W5 -> INT_X46Y90.INT_NODE_IMUX_48_INT_OUT0 -> INT_X46Y90.IMUX_W10 -> CLEM_X46Y90.CLE_CLE_M_SITE_0_A1'.replace('.', '/').split(' -> ')
    p1 = Path(nodes=nodes)
    p2 = PlainPath(nodes)

    print('hi')