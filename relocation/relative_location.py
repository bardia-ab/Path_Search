from resources.cut import CUT
from relocation.tile import Tile
import networkx as nx
import re
class RLOC:
    def __init__(self, cut: CUT, idx):
        self.G          = self.get_RLOC_G(cut)
        self.index      = idx
        self.origins    = set()

    def get_RLOC_G(self, cut):
        nodes_dict = {}
        main_path = cut.main_path.str_nodes()
        main_path_edges = set(zip(main_path, main_path[1:]))
        G = nx.DiGraph()
        for node in cut.G:
            if node.startswith('INT'):
                tile = f'INT_{self.get_RLOC_coord(self.get_tile(node), cut.origin)}'
                port = self.get_port(node)
            else:
                tile = f'CLB_{Tile(self.get_tile(node)).direction}_{self.get_RLOC_coord(self.get_tile(node), cut.origin)}'
                port = self.get_port(node).split('SITE_0_')[1]

            RLOC_node = f'{tile}/{port}'
            nodes_dict[node] = RLOC_node

        for edge in cut.G.edges():
            if edge in main_path_edges:
                label = 'main_path'
            else:
                label = 'not'

            G.add_edge(nodes_dict[edge[0]], nodes_dict[edge[1]], path_type=label)

        return G

    def get_DLOC_G(self, device, D_coord):
        nodes_dict = {}
        G = nx.DiGraph()

        for node in self.G:
            coordinate = self.get_DLOC_coord(self.get_tile(node), D_coord)
            if coordinate not in device.tiles_map:
                return None

            if node.startswith('INT'):
                '''if not device.get_tiles(coordinate=coordinate):
                    return None'''

                tile = f'INT_{coordinate}'
                port = self.get_port(node)
            else:
                direction = self.get_direction(node)
                #tile = device.get_tiles(coordinate=coordinate, direction=direction)
                tile = device.tiles_map[coordinate][f'CLB_{direction}']
                if not tile:
                    return None
                #else:
                    #tile = tile.pop().name

                port = f'CLE_CLE_{self.get_slice_type(tile)}_SITE_0_{self.get_port(node)}'

            DLOC_node = f'{tile}/{port}'
            nodes_dict[node] = DLOC_node

        for edge in self.G.edges():
            DLOC_edge = (nodes_dict[edge[0]], nodes_dict[edge[1]])
            if self.is_wire(DLOC_edge):
                if DLOC_edge not in device.wires_dict[self.get_tile(DLOC_edge[0])]:
                    return None


            label = self.G.get_edge_data(*edge)['path_type']
            G.add_edge(nodes_dict[edge[0]], nodes_dict[edge[1]], path_type=label)

        return G

    def is_pip(self, edge):
        if self.get_tile(edge[0]) == self.get_tile(edge[1]):
            return True
        else:
            return False

    def is_wire(self, edge):
        if self.get_tile(edge[0]) != self.get_tile(edge[1]):
            return True
        else:
            return False

    def get_RLOC_coord(self, tile, origin):
        rx = self.get_x_coord(tile) - self.get_x_coord(origin)
        ry = self.get_y_coord(tile) - self.get_y_coord(origin)
        RLOC_coord = f'X{rx}Y{ry}'

        return RLOC_coord

    def get_DLOC_coord(self, tile, D_coord):
        dx = self.get_x_coord(tile) + self.get_x_coord(D_coord)
        dy = self.get_y_coord(tile) + self.get_y_coord(D_coord)
        DLOC_coord = f'X{dx}Y{dy}'

        return DLOC_coord

    @staticmethod
    def get_direction(node):
        return RLOC.get_tile(node).split('_')[1]

    @staticmethod
    def get_slice_type(tile):
        if tile.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @staticmethod
    def get_coordinate(node):
        return re.findall('X-*\d+Y-*\d+', node)[0]

    @staticmethod
    def get_x_coord(tile):
        return int(re.findall('-*\d+', tile)[0])

    @staticmethod
    def get_y_coord(tile):
        return int(re.findall('-*\d+', tile)[1])

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]

    @staticmethod
    def get_port(wire, delimiter='/'):
        return wire.split(delimiter)[1]


