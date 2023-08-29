import re, os, shutil
from Functions import load_data, store_data
import Global_Module as GM
from relocation.relative_location import RLOC, DLOC
class Configuration:

    covered_pips_dict = {}
    def __init__(self):
        self.used_nodes_dict    = {}
        self.CUTs               = []
        #self.LUTs               = device.LUTs.copy()
        self.LUTs               = {}
        self.blocked_LUTs       = set()
        self.invalid_source_FFs = set()
        self.FFs                = {}
        self.CD                 = {}

    def add_DLOC_CUT(self, DLOC_G):
        for node in DLOC_G:
            tile = self.get_tile(node)
            port = self.get_port(node)
            self.extend_dict(self.used_nodes_dict, tile, port, value_type='set')

        for edge in DLOC_G.edges():
            if self.is_pip(edge):
                if edge[0].startswith('INT'):
                    key = self.get_tile(edge[0])
                    value = (self.get_port(edge[0]), self.get_port(edge[1]))
                else:
                    key = self.get_tile(edge[0])
                    value = (self.get_port(edge[0]), self.get_port(edge[1]))

                self.extend_dict(Configuration.covered_pips_dict, key, value, value_type='set')

    def add_D_CUT(self, D_CUT):
        DLOC_nodes = []
        for node in D_CUT.G:
            tile = self.get_tile(node)
            port = self.get_port(node)

            if tile in self.used_nodes_dict:
                if port in self.used_nodes_dict[tile]:
                    return False      # Collision
                else:
                    DLOC_nodes.append((tile, port))
            else:
                DLOC_nodes.append((tile, port))

        for element in DLOC_nodes:
            self.extend_dict(self.used_nodes_dict, element[0], element[1], value_type='set')

        for edge in D_CUT.G.edges():
            if self.is_pip(edge):
                if edge[0].startswith('INT'):
                    key = self.get_tile(edge[0])
                    value = (self.get_port(edge[0]), self.get_port(edge[1]))
                else:
                    key = self.get_tile(edge[0])
                    value = (self.get_port(edge[0]), self.get_port(edge[1]))
                    #key = f'CLB_{self.get_direction(edge[0])}_{self.get_coordinate(edge[0])}'
                    #value = (self.get_port(edge[0]).split('_SITE_0_')[-1], self.get_port(edge[1]).split('_SITE_0_')[-1])

                self.extend_dict(Configuration.covered_pips_dict, key, value, value_type='set')

        return True

    def get_LUTs(self, **attributes):
        LUTs = set()
        for LUT in self.LUTs:
            for attr in attributes:
                if getattr(LUT, attr) != attributes[attr]:
                    break
            else:
                LUTs.add(LUT)

        return LUTs

    def set_LUTs(self, LUTs_func_dict):
        usage = 'used'
        for node in LUTs_func_dict:
            LUT_primitives = self.get_subLUT(usage, node)
            if not LUT_primitives:
                continue

            for LUT_primitive in LUT_primitives:
                LUT_primitive.inputs = node.name
                LUT_primitive.func   = LUTs_func_dict[node]
                LUT_primitive.usage  = usage

    def get_subLUT(self, usage, node, next_iter_initalization=False):
        LUT_primitives = []
        if usage == 'free':
            LUT_primitives.extend(self.get_LUTs(tile=node.tile, letter=node.bel, type=node.primitive, usage='used'))
            LUT_primitives.sort(key=lambda x: x.name, reverse=False)  #[5LUT, 6LUT]
        elif usage == 'used':
            LUT_primitives.extend(self.get_LUTs(tile=node.tile, letter=node.bel, type=node.primitive, usage='free'))
            LUT_primitives.sort(key=lambda x: x.name, reverse=True)   #[6LUT, 5LUT]
            if not LUT_primitives:
                breakpoint()
        else:
            status = 'free' if next_iter_initalization else 'used'
            LUT_primitives.extend(self.get_LUTs(tile=node.tile, letter=node.bel, type=node.primitive, usage=status))
            LUT_primitives.sort(key=lambda x: x.name, reverse=True)   #[6LUT, 5LUT]

        if node.is_i6:
            return LUT_primitives
        elif LUT_primitives:
            return LUT_primitives[:1]
        else:
            return []

    def set_blocked_invalid_primitives(self):
        for lut in self.LUTs:
            #self.LUTs[lut] = set(self.LUTs[lut] )
            self.LUTs[lut] = sorted(self.LUTs[lut], key=lambda x: 0 if x[2] == 'O' else 1)
            for i, subLUT in enumerate(self.LUTs[lut]):
                idx = 6 - i
                tile = self.get_tile(lut)
                bel = self.get_port(lut)[0]
                self.blocked_LUTs.add(f'{tile}/{bel}{idx}LUT')
                if subLUT[0][-1] == '6':
                    self.blocked_LUTs.add(f'{tile}/{bel}5LUT')

                if i == 1:
                    FF1 = subLUT[0][:-1] + 'Q'
                    FF2 = subLUT[0][:-1] + 'Q2'
                    self.invalid_source_FFs.update({FF1, FF2})

    @classmethod
    def sort_covered_pips(self, x_min, x_max, y_min, y_max):
        keys = []
        for key in self.covered_pips_dict:
            if key.startswith('CLE'):
                continue
            [x, y] = re.findall('\d+', key)
            x = int(x)
            y = int(y)
            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                keys.append(key)

        keys = sorted(keys, key=lambda x: len(self.covered_pips_dict[x]))
        self.covered_pips_dict = {k: self.covered_pips_dict[k] for k in keys}

    @staticmethod
    def is_pip(edge):
        if Configuration.get_tile(edge[0]) == Configuration.get_tile(edge[1]):
            return True
        else:
            return False

    @staticmethod
    def get_direction(clb_node):
        if clb_node.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir

    @staticmethod
    def get_coordinate(node):
        return re.findall('X-*\d+Y-*\d+', node)[0]

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]

    @staticmethod
    def get_port(wire, delimiter='/'):
        return wire.split(delimiter)[1]

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
