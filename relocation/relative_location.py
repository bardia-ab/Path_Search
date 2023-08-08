from resources.cut import CUT
from relocation.tile import Tile
import networkx as nx
import re, copy
from Functions import extend_dict
import Global_Module as GM
class RLOC:
    def __init__(self, cut: CUT, idx):
        self.LUTs_func_dict = {}
        self.FFs_set = set()
        self.G              = self.get_RLOC_G(cut)
        self.index          =   idx
        self.origins        = set()
        self.D_CUTs         = set()

    def __repr__(self):
        return f'CUT{self.index}'

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

        for LUT_in in cut.LUTs_func_dict:
            function = cut.LUTs_func_dict[LUT_in]
            R_LUT_in = copy.deepcopy(LUT_in)
            R_LUT_in.name = nodes_dict[LUT_in.name]
            self.LUTs_func_dict[R_LUT_in] = function

        for ff in cut.FFs_set:
            R_ff = copy.deepcopy(ff)
            R_ff.name = nodes_dict[ff.name]
            self.FFs_set.add(R_ff)

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

    @staticmethod
    def is_pip(edge):
        if RLOC.get_tile(edge[0]) == RLOC.get_tile(edge[1]):
            return True
        else:
            return False

    @staticmethod
    def is_wire(edge):
        if RLOC.get_tile(edge[0]) != RLOC.get_tile(edge[1]):
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
    def get_direction(clb_node):
        if clb_node.startswith('CLEL_R'):
            dir = 'E'
        else:
            dir = 'W'

        return dir

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



class DLOC():

    def __init__(self, device, TC, R_CUT, origin):
        #self.LUTs_func_dict = {}
        #self.FFs_set        = set()
        self.origin         = origin
        self.index          = R_CUT.index
        self.G              = self.get_DLOC_G(device, TC, R_CUT)

    def __repr__(self):
        return f'CUT{self.index}_{self.origin}'

    def get_DLOC_G(self, device, TC, R_CUT):
        nodes_dict = {}
        G = nx.DiGraph()

        for node in R_CUT.G:
            coordinate = self.get_DLOC_coord(self.get_tile(node), self.origin)
            if coordinate not in device.tiles_map:
                return None

            if node.startswith('INT'):
                tile = f'INT_{coordinate}'
                port = self.get_port(node)
            else:
                direction = self.get_direction(node)
                tile = device.tiles_map[coordinate][f'CLB_{direction}']
                if not tile:
                    return None

                port = f'CLE_CLE_{self.get_slice_type(tile)}_SITE_0_{self.get_port(node)}'

            DLOC_node = f'{tile}/{port}'
            nodes_dict[node] = DLOC_node

        for edge in R_CUT.G.edges():
            DLOC_edge = (nodes_dict[edge[0]], nodes_dict[edge[1]])
            if self.is_wire(DLOC_edge):
                if DLOC_edge not in device.wires_dict[self.get_tile(DLOC_edge[0])]:
                    return None

            label = R_CUT.G.get_edge_data(*edge)['path_type']
            G.add_edge(nodes_dict[edge[0]], nodes_dict[edge[1]], path_type=label)

        for LUT_in in R_CUT.LUTs_func_dict:
            function = R_CUT.LUTs_func_dict[LUT_in]
            D_LUT_in = copy.deepcopy(LUT_in)
            D_LUT_in.name = nodes_dict[LUT_in.name]
            if function == 'buffer':
                neigh = list(G.neighbors(D_LUT_in.name))[0]
                neigh_type = 'O' if re.match(GM.CLB_out_pattern, neigh) else 'MUX'
            else:
                neigh_type = None

            #self.LUTs_func_dict[D_LUT_in] = function
            extend_dict(TC.LUTs, D_LUT_in.bel_key, (D_LUT_in.name, function, neigh_type))
            #LUT_primitive = TC.get_LUTs(name=D_LUT_in.bel_key).pop()
            #LUT_primitive.set_LUT(D_LUT_in, function)

        for ff in R_CUT.FFs_set:
            D_ff = copy.deepcopy(ff)
            D_ff.name = nodes_dict[ff.name]
            extend_dict(TC.FFs, D_ff.bel_key, D_ff.name)
            #self.FFs_set.add(D_ff)

        return G

    def get_DLOC_coord(self, tile, D_coord):
        dx = self.get_x_coord(tile) + self.get_x_coord(D_coord)
        dy = self.get_y_coord(tile) + self.get_y_coord(D_coord)
        DLOC_coord = f'X{dx}Y{dy}'

        return DLOC_coord

    @staticmethod
    def is_pip(edge):
        if RLOC.get_tile(edge[0]) == RLOC.get_tile(edge[1]):
            return True
        else:
            return False

    @staticmethod
    def is_wire(edge):
        if RLOC.get_tile(edge[0]) != RLOC.get_tile(edge[1]):
            return True
        else:
            return False

    @staticmethod
    def get_direction(node):
        def get_direction(clb_node):
            if clb_node.startswith('CLEL_R'):
                dir = 'E'
            else:
                dir = 'W'

            return dir

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