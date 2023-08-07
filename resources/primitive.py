import re
from resources.node import Node
from itertools import product
from Functions import extend_dict

class Primitive:

    def __init__(self, type, name):
        self.type   = type
        self.name   = name
        self.usage  = 'free'

    def __repr__(self):
        return self.name

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
    def coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.name)[0]

    @property
    def site_type(self):
        if self.name.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @property
    def direction(self):
        if self.name.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir


class FF(Primitive):

    def __init__(self, name):
        super().__init__('FF', name)

    @property
    def index(self):
        if self.name.endswith('2'):
            return 2
        else:
            return 1


class LUT(Primitive):

    def __init__(self, name):
        super().__init__('LUT', name)
        self.init   = ''
        self.inputs = None
        self.func   = None

    @property
    def LUT_type(self):
        return self.bel[1:]     # 5LUT|6LUT

    @property
    def func(self):
        return self._func

    @func.setter
    def func(self, function):
        self._func = function
        self.cal_init()

    @property
    def inputs(self):
        return self._inputs

    @inputs.setter
    def inputs(self, input):
        if input is not None:
            self._inputs.add(input)
            self.cal_init()
        else:
            self._inputs = set()

    def clear(self):
        self.inputs     = None
        self.func       = None
        self.usage      = 'free'
        self.cal_init()

    def cal_init(self):
        entries = LUT.get_truth_table(int(self.bel[1]))
        if self.func == 'buffer':
            idx = int(list(self.inputs)[0][-1]) - 1
            if self.LUT_type == '5LUT' and idx == 5:
                return

            init_list = [str(entry[idx]) for entry in entries]
        elif self.func == 'not':
            idx = int(list(self.inputs)[0][-1]) - 1
            if self.LUT_type == '5LUT' and idx == 5:
                return

            init_list = [str(int(not(entry[idx]))) for entry in entries]

        else:
            init_list = [str(0) for _ in entries]

        init_list.reverse()
        init_binary = ''.join(init_list)
        self.init = format(int(init_binary, base=2), f'016X')

    @staticmethod
    def get_truth_table(n_entry):
        truth_table = list(product((0, 1), repeat=n_entry))
        return [entry[::-1] for entry in truth_table]

    @staticmethod
    def integrate(*LUT_primitives):
        dct = {}
        for LUT_primitive in LUT_primitives:
            key = f'{LUT_primitive.tile}/{LUT_primitive.letter}LUT'
            extend_dict(dct, key, LUT_primitive)

        LUT6_2_primitives = set()
        for key in dct:
            LUT6_2_primitives.add(LUT6_2(key, *dct[key]))

        return LUT6_2_primitives

class LUT6_2:

    def __init__(self, name, *primitives):
        self.name   = name
        self.LUTs   = primitives
        self.init = self.cal_int2()

    def __repr__(self):
        return self.name

    def set_LUT(self, LUT_in, function):
        subLUT = [lut for lut in self.LUTs if lut.usage == 'free']
        subLUT.sort(key=lambda x: x.name, reverse=True)
        N = 2 if LUT_in.is_i6 else 1
        for i in range(N):
            subLUT[i].inputs   = LUT_in
            subLUT[i].function = function
            subLUT[i].usage    = 'used'

    def cal_int(self):
        LUT6 = [prim for prim in self.LUTs if prim.LUT_type=='6LUT'].pop()
        LUT5 = [prim for prim in self.LUTs if prim.LUT_type == '5LUT']

        if LUT5 and not Node(LUT5[0].inputs[0]).is_i6: # when LUT_in.is_i6 => 5LUT is used but init isn't calculated
            LUT5 = LUT5.pop()
            init = "64'h" + LUT6.init[:8] + LUT5.init[-8:]
        else:
            init = "64'h" + LUT6.init

        return init

    def cal_int2(self):
        LUT6 = [prim for prim in self.LUTs if prim.LUT_type=='6LUT'].pop()
        LUT5 = [prim for prim in self.LUTs if prim.LUT_type == '5LUT'].pop()

        if LUT5.usage == 'used' and not LUT5.inputs.is_i6: # when LUT_in.is_i6 => 5LUT is used but init isn't calculated
            LUT5 = LUT5.pop()
            init = "64'h" + LUT6.init[:8] + LUT5.init[-8:]
        else:
            init = "64'h" + LUT6.init

        return init

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
    def coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.name)[0]

    @property
    def site_type(self):
        if self.name.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @property
    def direction(self):
        if self.name.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir
