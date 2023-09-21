import re
from resources.node import Node
from itertools import product
from abc import ABC, abstractmethod

class Primitive(ABC):
    @abstractmethod
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @property
    def tile(self, delimiter='/'):
        return self.name.split(delimiter)[0]

    @property
    def bel(self, delimiter='/'):
        return self.name.split(delimiter)[1]

    @property
    def letter(self):
        return self.bel[0]

    @property
    def bel_group(self):
        if self.name.startswith('CLEL_R'):
            group = 'E_'
        else:
            group = 'W_'

        if self.letter in ['A', 'B', 'C', 'D']:
            group = group + 'B'
        else:
            group = group + 'T'

        return group

    @property
    def direction(self):
        if self.name.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir

    @property
    def coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.name)[0]

    @property
    def get_x_coord(self):
        return int(re.findall('-*\d+', self.tile)[0])

    @property
    def get_y_coord(self):
        return int(re.findall('-*\d+', self.tile)[1])

    @property
    def site_type(self):
        if self.name.startswith('CLEM'):
            return 'M'
        else:
            return 'L'


class FF(Primitive):
    __slots__ = ('name', '_node')
    def __init__(self, name):
        self.name   = name
        self.node   = None

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name and self.node == other.node

    def __hash__(self):
        return hash((self.name, self.node))

    @property
    def node(self):
        return self._node

    @node.setter
    def node(self, node_obj: str|Node):
        if node_obj is not None:
            node_obj = node_obj if type(node_obj) == Node else Node(node_obj)

        self._node = node_obj

    @property
    def index(self):
        if self.name.endswith('2'):
            return 2
        else:
            return 1

class SubLUT_ABC(Primitive):
    __slots__ = ('name', 'usage', '_inputs', '_output', '_func')
    def __init__(self, name):
        self.name   = name
        self.usage  = 'free'
        self.inputs = None
        self.output = None
        self.func   = None

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name and self.usage == other.usage and self.inputs == other.inputs and self.output == other.output and self.func == other.func

    def __hash__(self):
        return hash((self.name, self.usage, self._inputs, self._output, self._func))

    @property
    @abstractmethod
    def num_inputs(self):
        pass

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, function):
        self._func = function
        #self.cal_init()

    @property
    def inputs(self) -> {Node}:
        return self._inputs

    @inputs.setter
    def inputs(self, input: Node|str):
        if input is not None:
            input = input if type(input) == Node else Node(input)
            if not (0 <= input.index <= self.num_inputs):
                raise Exception(f'{input} is invalid for {self.name}!!!')

            self._inputs.add(input)
        else:
            self._inputs = set()

    @property
    def output(self) -> Node:
        return self._output

    @output.setter
    @abstractmethod
    def output(self, outp:Node):
        pass

    @property
    @abstractmethod
    def capacity(self):
        pass

    def clear(self):
        self.inputs     = None
        self.output     = None
        self.func       = None
        self.usage      = 'free'
        #self.cal_init()

    def cal_init(self):
        entries = self.get_truth_table()
        if self.func == 'buffer':
            idx = list(self.inputs)[0].index - 1
            init_list = (str(entry[idx]) for entry in entries)
        elif self.func == 'not':
            idx = list(self.inputs)[0].index - 1
            init_list = (str(int(not(entry[idx]))) for entry in entries)
        else:
            init_list = (str(0) for _ in entries)

        init_list = reversed(list(init_list))
        init_binary = ''.join(init_list)

        return format(int(init_binary, base=2), f'0{2**self.num_inputs // 4}X')

    def get_truth_table(self):
        truth_table = product((0, 1), repeat=self.num_inputs)
        for entry in truth_table:
            yield entry[::-1]


class SubLUT_5(SubLUT_ABC):

    @property
    def num_inputs(self):
        return 5

    @SubLUT_ABC.output.setter
    def output(self, outp:Node|str):
        if outp is not None:
            raise Exception(f'{self.name} cannot connect to {outp}')

        self._output = outp

    @property
    def capacity(self):
        return 1


class SubLUT_6(SubLUT_ABC):

    @property
    def num_inputs(self):
        return 6

    @SubLUT_ABC.output.setter
    def output(self, outp: Node | str):
        if outp is not None:
            outp = outp if type(outp) == Node else Node(outp)
            if outp.clb_node_type not in  {'CLB_muxed', 'CLB_out'}:
                raise Exception(f'{self.name} cannot connect to {outp}')

        self._output = outp

    @property
    def capacity(self):
        return 2


class LUT(Primitive):
    __slots__ = ('name', '_capacity', '_subLUT')

    def __init__(self, name):
        self.name = name
        self._capacity = 2
        self._subLUT = []

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __hash__(self):
        return hash((self.name, ))
    @property
    def capacity(self):
        return self._capacity

    @capacity.setter
    def capacity(self, val):
        if not (0 <= val <= 2):
            raise Exception(f'{val} is not a valid capacity!')

        self._capacity = val

    @property
    def subLUT(self):
        return self._subLUT

    @subLUT.setter
    def subLUT(self, sublut: SubLUT_5 | SubLUT_6):

        if sublut.capacity > self.capacity:
            raise Exception(f'{sublut} cannot fit into {self}!')
        else:
            self._subLUT.append(sublut)
            self.capacity -= sublut.capacity


if __name__ == '__main__':
    lut1 = SubLUT_6('CLEM_X46Y90/A6LUT')
    lut1.inputs = 'CLEM_X46Y90/CLE_CLE_M_SITE_0_A1'
    lut1.func = 'buffer'
    lut1.output = 'CLEM_X46Y90/CLE_CLE_M_SITE_0_A_O'
    lut2 = SubLUT_5('CLEM_X46Y90/A5LUT')
    lut2.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A2')
    lut2.func = 'not'
    # lut2.cal_init()

    a = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_AMUX')
    #lut2.output = a

    lut3 = SubLUT_6('CLEM_X46Y90/A6LUT')
    lut3.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A1')
    lut3.func = 'not'
    lut4 = SubLUT_5('CLEM_X46Y90/A5LUT')
    lut4.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A2')
    lut4.func = 'buffer'
    lut4.output = 'CLEM_X46Y90/CLE_CLE_M_SITE_0_AMUX'

    lut = LUT('CLEM_X46Y90/ALUT')
    lut.subLUT = lut4
    print('hi')