import re
from resources.node import Node
from itertools import product

class LUT():
    __slots__ = ('name', 'usage', '_inputs', '_output', '_func')
    def __init__(self, name):
        self.name   = name
        self.usage  = 'free'
        self.inputs = None
        self.output = None
        self.func   = None

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name and self.usage == other.usage and self.inputs == other.inputs and self.output == other.output and self.func == other.func

    def __hash__(self):
        return hash((self.name, self.usage, self._inputs, self._output, self._func))

    @property
    def tile(self, delimiter='/'):
        return self.name.split(delimiter)[0]

    @property
    def bel(self, delimiter='/'):
        return self.name.split(delimiter)[1]

    @property
    def LUT_type(self):
        return self.bel[1:]     # 5LUT|6LUT

    @property
    def num_inputs(self):
        return int(self.LUT_type[0])

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

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, function):
        self._func = function
        #self.cal_init()

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, input):
        if input is not None:
            if self.num_inputs < input.index:
                raise Exception(f'{input} is invalid for {self.name}!!!')

            self._inputs.add(input)
            #self.cal_init()
        else:
            self._inputs = set()

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, outp:Node):
        if outp is not None:
            if self.LUT_type == '5LUT' and outp.clb_node_type == 'CLB_muxed':
                raise Exception(f'{self.name} cannot connect to {outp}')

        self._output = outp

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
