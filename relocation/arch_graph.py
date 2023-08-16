import networkx as nx

from Functions import load_data
from relocation.tile import Tile
from resources.primitive import LUT, LUT6_2
import Global_Module as GM
import re, os
class Arch:

    def __init__(self, name):
        self.name       = name
        self.wires_dict = load_data(GM.load_path, 'wires_dict2.data')
        self.tiles_map  = self.get_tiles_coord_dict()
        self.INTs       = self.get_INTs()
        self.CLBs       = self.get_CLBs()
        self.pips       = load_data(GM.load_path, 'pips.data')
        #self.LUTs       = self.gen_LUTs()

    def get_INTs(self):
        INTs = set(filter(lambda x: x.startswith('INT'), self.wires_dict))

        return [Tile(INT) for INT in INTs]

    def get_CLBs(self):
        CLBs = set(filter(lambda x: x.startswith('CLE'), self.wires_dict))

        return [Tile(CLB) for CLB in CLBs]

    def get_tiles(self, **attributes):
        tiles = set()
        for tile in self.INTs + self.CLBs:
            for attr in attributes:
                if getattr(tile, attr) != attributes[attr]:
                    break
            else:
                tiles.add(tile)

        return tiles

    def gen_LUTs(self):
        LUTs = set()
        for clb in self.CLBs:
            for i in range(65, 73):
                subLUT1 = LUT(f'{clb.name}/{chr(i)}5LUT')
                subLUT2 = LUT(f'{clb.name}/{chr(i)}6LUT')
                LUTs.add(LUT6_2(f'{clb.name}/{chr(i)}LUT', subLUT1, subLUT2))

        return LUTs

    def sort_INTs(self, INTs, tile):
        x_coord = self.get_x_coord(tile)
        origin_tile = self.get_tiles(name=tile).pop()
        INTs.sort(key=lambda x: self.get_x_coord(x.name))
        INTs = sorted(INTs, key= lambda x: abs(x_coord - self.get_x_coord(x.name)))
        INTs.remove(origin_tile)
        INTs.insert(0, origin_tile)

        return INTs

    def get_tiles_coord_dict(self):
        tiles_coord_dict = {}
        for key in self.wires_dict:
            coordinate = re.findall('X\d+Y\d+', key)[0]
            if key.startswith('INT'):
                tile_type = 'INT'
            elif key.startswith('CLEL_R'):
                tile_type = 'CLB_E'
            else:
                tile_type = 'CLB_W'

            if coordinate not in tiles_coord_dict:
                tiles_coord_dict.update({coordinate: {'CLB_W': None, 'INT': None, 'CLB_E': None}})

            tiles_coord_dict[coordinate][tile_type] = key

        return tiles_coord_dict

    def limit(self, x_min, x_max, y_min, y_max):
        limited_tiles = []
        for tile in self.INTs:
            [x, y] = re.findall('\d+', tile.name)
            x = int(x)
            y = int(y)
            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                limited_tiles.append(tile)

        limited_INTs = []
        limited_CLBs = []
        x_min = x_min - 16
        y_min = y_min - 16
        x_max = x_max + 16
        y_max = y_max + 16

        for tile in self.INTs:
            [x, y] = re.findall('\d+', tile.name)
            x = int(x)
            y = int(y)
            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                limited_INTs.append(tile)

        for tile in self.CLBs:
            [x, y] = re.findall('\d+', tile.name)
            x = int(x)
            y = int(y)
            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                limited_CLBs.append(tile)

        self.INTs = limited_INTs.copy()
        self.CLBs = limited_CLBs.copy()

        return limited_tiles

    def remove_covered_INTs(self):
        remaining_pips_dict = self.get_remaining_pips_dict()
        return [INT for INT in self.INTs if INT.name in remaining_pips_dict]

    def get_remaining_pips_dict(self):
        covered_pips_dict = load_data(GM.Data_path, 'covered_pips_dict.data')
        remaining_pips = {}
        for INT in covered_pips_dict:
            coordinate = INT.split('_')[1]
            pattern = {k: 1 if v else 0 for k, v in self.tiles_map[coordinate].items()}
            N_pips = 3424 if all(pattern.values()) else 2480
            N_remaining = N_pips - len(covered_pips_dict[INT])
            if N_remaining:
                remaining_pips[INT] = N_remaining

        keys = sorted(remaining_pips, key=remaining_pips.get, reverse=True)
        remaining_pips = {k: remaining_pips[k] for k in keys}

        return remaining_pips

    def get_pips(self, INT):
        pips = set()
        for pip in self.pips:
            u, v = f'{INT}/{pip[0]}', f'{INT}/{pip[1]}'
            pips.add((u, v))

        return pips

    def get_tile_graph(self, tile):
        G = nx.DiGraph()
        G.add_edges_from(self.get_pips(tile))

        return G

    @staticmethod
    def get_x_coord(tile):
        return int(re.findall('-*\d+', tile)[0])

    @staticmethod
    def get_y_coord(tile):
        return int(re.findall('-*\d+', tile)[1])