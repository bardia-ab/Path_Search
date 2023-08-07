from Functions import load_data
from relocation.tile import Tile
import Global_Module as GM
import re
class Arch:

    def __init__(self, name):
        self.name       = name
        self.wires_dict = load_data(GM.load_path, 'wires_dict2.data')
        self.tiles_map  = self.get_tiles_coord_dict()
        self.INTs       = self.get_INTs()
        self.CLBs       = self.get_CLBs()

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

    def sort_INTs(self, tile):
        x_coord = self.get_x_coord(tile)
        origin_tile = self.get_tiles(name=tile).pop()
        self.INTs.sort(key=lambda x: self.get_x_coord(x.name))
        self.INTs = sorted(self.INTs, key= lambda x: abs(x_coord - self.get_x_coord(x.name)))
        self.INTs.remove(origin_tile)
        self.INTs.insert(0, origin_tile)

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
        for tile in self.INTs + self.CLBs:
            [x, y] = re.findall('\d+', tile.name)
            x = int(x)
            y = int(y)
            if (x_min <= x <= x_max) and (y_min <= y <= y_max):
                limited_tiles.append(tile)

        self.INTs = limited_tiles.copy()

    @staticmethod
    def get_x_coord(tile):
        return int(re.findall('-*\d+', tile)[0])

    @staticmethod
    def get_y_coord(tile):
        return int(re.findall('-*\d+', tile)[1])