import re
import Global_Module as GM

class Node:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    @property
    def exact_tile_type(self):
        end_idx = re.search('_X-*\d+Y-*\d+', self.tile).regs[0][0]
        return self.tile[:end_idx]

    @property
    def tile_type(self):
        if self.name.startswith('INT'):
            return 'INT'
        else:
            return 'CLB'

    @property
    def tile(self, delimiter='/'):
        return self.name.split(delimiter)[0]

    @property
    def port(self, delimiter='/'):
        return self.name.split(delimiter)[1]

    @property
    def bel(self):
        if self.tile_type == 'INT':
            return None
        else:
            return self.name.split('_SITE_0_')[-1][0]

    @property
    def port_suffix(self):
        if self.tile_type == 'INT':
            return None
        else:
            return self.name.split('_SITE_0_')[-1]

    @property
    def bel_key(self):
        if re.match(GM.LUT_in_pattern, self.name):
            key = self.tile + '/' + self.bel + 'LUT'

        elif re.match(GM.FF_in_pattern, self.name):
            suffix = ['', '2']
            key = self.tile + '/' + self.bel + 'FF' + suffix[int(self.index) - 1]

        elif re.match(GM.FF_out_pattern, self.name):
            suffix = ['', '2']
            key = self.tile + '/' + self.bel + 'FF' + suffix[int(self.index) - 1]

        else:
            key = None

        return key

    @property
    def index(self):
        if self.clb_node_type in ['FF_in', 'FF_out']:
            if self.name[-1] in ['I', '2']:
                return 2

            if self.name[-1] in ['X', 'Q']:
                return 1

        if self.clb_node_type == 'LUT_in':
            return self.name[-1]

    @property
    def is_i6(self):
        return bool(re.match(GM.LUT_in6_pattern, self.name))

    @property
    def bel_group(self):
        if self.tile_type == 'INT':
            return None

        if self.name.startswith('CLEL_R'):
            group = 'E_'
        else:
            group = 'W_'

        if self.bel in ['A', 'B', 'C', 'D']:
            group = group + 'B'
        else:
            group = group + 'T'

        return group

    @property
    def site_type(self):
        if self.tile_type == 'INT':
            return None
        elif self.tile.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @property
    def coordinate(self):
        return re.findall('X-*\d+Y-*\d+', self.tile)[0]

    @property
    def prefix(self):
        if self.tile_type == 'INT':
            return None
        else:
            return f'CLE_CLE_{self.site_type}_SITE_0'

    @property
    def clb_node_type(self):
        if re.match(GM.LUT_in_pattern, self.name):
            return 'LUT_in'
        elif re.match(GM.FF_in_pattern, self.name):
            return 'FF_in'
        elif re.match(GM.FF_out_pattern, self.name):
            return 'FF_out'
        elif re.match(GM.CLB_out_pattern, self.name):
            return 'CLB_out'
        elif re.match(GM.MUXED_CLB_out_pattern, self.name):
            return 'CLB_muxed'
        else:
            return None

    @property
    def primitive(self):
        if self.tile_type == 'INT':
            return None
        elif self.clb_node_type == 'LUT_in':
            return 'LUT'
        elif self.clb_node_type in {'FF_out', 'FF_in'}:
            return 'FF'
        else:
            return None

    def set_INT_node_mode(self, G):
        # Modes: 1- in 2- out 3- mid
        pred_tiles = {self.__class__(pred).tile for pred in G.predecessors(self.name)}
        neigh_tiles = {self.__class__(neigh).tile for neigh in G.neighbors(self.name)}

        if pred_tiles == neigh_tiles:
            mode = 'mid'

        elif self.tile not in pred_tiles and (neigh_tiles == {self.tile} or neigh_tiles == set()):
            mode = 'in'

        else:
            mode = 'out'

        return mode


    @staticmethod
    def get_x_coord(tile):
        return int(re.findall('-*\d+', tile)[0])

    @staticmethod
    def get_y_coord(tile):
        return int(re.findall('-*\d+', tile)[1])