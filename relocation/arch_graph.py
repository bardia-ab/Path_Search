import networkx as nx

from Functions import load_data, get_tile, get_port, extend_dict
from relocation.tile import Tile
from resources.primitive import LUT, LUT6_2
from relocation.clock_region import CR
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
        self.CRs        = CR.init_CRs(os.path.join(GM.load_path, 'HCS.txt'))
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
        G = self.block_graph(G)
        return G

    def block_graph(self, G):
        used_pips = set()
        used_nodes = set()
        #clk_path_pips= set(nx.dfs_edges(G, clk_pin))
        G_tiles = {get_tile(node) for node in G}
        for tile in G_tiles:
            if tile not in self.used_nodes_dict:
                continue

            used_nodes.update({f'{tile}/{node}' for node in self.used_nodes_dict[tile]})
            used_pips.update({(f'{tile}/{pip[0]}', f'{tile}/{pip[1]}') for pip in self.used_pips_dict[tile]})


        in_edges = set()
        for node in used_nodes:
            in_edges.update(G.in_edges(node))

        #in_edges = in_edges - clk_path_pips
        in_edges = in_edges - used_pips
        G.remove_edges_from(in_edges)

        return G

    @staticmethod
    def get_occupied_pips(pips_file):
        used_pips_dict  = {}
        with open(pips_file) as lines:
            for line in lines:
                if '<<->>' in line:
                    line = line.rstrip('\n').split('<<->>')
                    bidir = True
                elif '->>' in line:
                    line = line.rstrip('\n').split('->>')
                    bidir = False
                else:
                    line = line.rstrip('\n').split('->')
                    bidir = False

                tile = get_tile(line[0])
                start_port = get_port(line[0]).split('.')[1]
                end_port = line[1]
                extend_dict(used_pips_dict , tile, (start_port, end_port), value_type='set')
                if bidir:
                    extend_dict(used_pips_dict , tile, (end_port, start_port), value_type='set')

        return used_pips_dict

    def set_used_pips_nodes_dict(self, pips_file):
        self.used_pips_dict = self.get_occupied_pips(pips_file)
        self.used_nodes_dict = {}
        for key in self.used_pips_dict:
            self.used_nodes_dict[key] = {node for pip in self.used_pips_dict[key] for node in pip}
    def set_clk_dicts(self, file, clk_name):
        clk_pips_dict = self.get_occupied_pips(file)
        clk_nodes_dict = {}
        for tile in clk_pips_dict:
            clk_nodes_dict[tile] = {node for pip in clk_pips_dict[tile] for node in pip}

        clk_pins_dict = {}
        for tile, nodes in clk_nodes_dict.items():
            clk_pins = set(filter(lambda x: re.match('.*GCLK.*', x), nodes))
            if clk_pins:
                clk_pins_dict[tile] = next(iter(clk_pins))

        CR_clk_pins_dict = {}
        for tile, pin in clk_pins_dict.items():
            cr, half = self.get_tile_half(tile)
            x = self.get_x_coord(tile)
            extend_dict(CR_clk_pins_dict, (cr.name, half, x), pin, value_type='set')
            '''if cr not in CR_clk_pins_dict:
                CR_clk_pins_dict[cr] = {half: set(pin)}
            else:
                if half not in CR_clk_pins_dict[cr]:
                    CR_clk_pins_dict[cr].update({half: set(pin)})
                else:
                    CR_clk_pins_dict[cr][half].update(pin)'''

        if clk_name == 'launch':
            self.CR_l_clk_pins_dict = CR_clk_pins_dict.copy()

        if clk_name == 'sample':
            self.CR_s_clk_pins_dict = CR_clk_pins_dict.copy()

    def get_CRs(self, **attributes):
        CRs = set()
        for tile in self.CRs:
            for attr in attributes:
                if getattr(tile, attr) != attributes[attr]:
                    break
            else:
                CRs.add(tile)


        return CRs

    def get_tile_half(self, tile):
        x, y = self.get_x_coord(tile), self.get_y_coord(tile)
        for cr in {cr for cr in self.CRs if cr.HCS_Y_coord}:
            if (cr.x_min <= x <= cr.x_max) and (cr.y_min <= y <= cr.y_max):
                half = 'T' if y > cr.HCS_Y_coord else 'B'
                return cr, half

    @staticmethod
    def get_x_coord(tile):
        return int(re.findall('-*\d+', tile)[0])

    @staticmethod
    def get_y_coord(tile):
        return int(re.findall('-*\d+', tile)[1])