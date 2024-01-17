import re
from itertools import product
from Functions import *

class CR:

    def __init__(self, name, HCS_Y_coord, *tiles):
        self.name               = name
        self.HCS_Y_coord        = HCS_Y_coord
        self.tiles              = tiles
        self.set_boarders_coord()

    def __repr__(self):
        return self.name

    '''def get_INT_tiles(self, half=None):
        if self.HCS_Y_coord:
            if half == 'T':
                x_max = self.get_x_coord(self.bottom_right_tile)
                x_min, y_max = self.get_x_coord(self.top_left_tile), self.get_y_coord(self.top_left_tile)
                coords = set(product(range(x_min, x_max + 1), range(self.HCS_Y_coord + 1, y_max + 1)))
            elif half == 'B':
                x_max, y_min = self.get_x_coord(self.bottom_right_tile), self.get_y_coord(self.bottom_right_tile)
                x_min = self.get_x_coord(self.top_left_tile)
                coords = set(product(range(x_min, x_max + 1), range(y_min, self.HCS_Y_coord + 1)))
            else:
                x_max, y_min = self.get_x_coord(self.bottom_right_tile), self.get_y_coord(self.bottom_right_tile)
                x_min, y_max = self.get_x_coord(self.top_left_tile), self.get_y_coord(self.top_left_tile)
                coords = set(product(range(x_min, x_max + 1), range(y_min, y_max + 1)))

            INTs = [f'INT_X{coord[0]}Y{coord[1]}' for coord in coords]
        else:
            INTs = []

        return INTs'''

    def set_boarders_coord(self):
        self.x_min, self.y_min = 1000, 1000
        self.x_max, self.y_max = -1, -1
        for tile in self.tiles:
            x, y = self.get_x_coord(tile), self.get_y_coord(tile)
            if (x <= self.x_min and y <= self.y_min):
                self.x_min, self.y_min = x, y

            if (x >= self.x_max and y >= self.y_max):
                self.x_max, self.y_max = x, y

    @staticmethod
    def get_x_coord(tile):
        return int(re.findall('-*\d+', tile)[0])

    @staticmethod
    def get_y_coord(tile):
        return int(re.findall('-*\d+', tile)[1])
    @staticmethod
    def init_CRs(HCS_file):
        CRs = []
        HCS_dict = {}
        with open(HCS_file) as lines:
            for line in lines:
                line = line.rstrip('\n').split('\t')
                HCS_dict[line[0]] = int(line[1])

        CR_tile_dict = load_data(GM.load_path, 'CR_tile_dict.data')
        for cr, tiles in CR_tile_dict.items():
            HCS_Y_coord = HCS_dict[cr]
            CRs.append(CR(cr, HCS_Y_coord, *tiles))

        return CRs

    @staticmethod
    def get_CR_tile_dict(file):
        with open(file) as lines:
            entries = list(filter(lambda x: re.match('.*Name=INT_X.*ClockRegion=.*', x), lines))

        CR_tile_dict = {}
        for line in entries:
            line = line.rstrip('\n').split(',')
            clock_region = line[-1].split('=')[1]
            tile = line[2].split('=')[1]
            extend_dict(CR_tile_dict, clock_region, tile)

        return CR_tile_dict

    def get_coordinates(self):
        return {re.findall('X-*\d+Y-*\d+', tile)[0] for tile in self.tiles}
