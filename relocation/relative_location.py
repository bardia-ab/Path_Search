from resources.cut import CUT
from resources.node import Node
from relocation.tile import Tile
import networkx as nx
import re, copy, concurrent.futures
from itertools import product
from Functions import extend_dict
import Global_Module as GM
class RLOC:
    def __init__(self, cut: CUT, idx):
        self.LUTs_func_dict = {}
        self.FFs_set        = set()
        self.G              = self.get_RLOC_G(cut)
        self.index          =   idx
        self.origins        = set()
        self.D_CUTs         = set()

    def __repr__(self):
        return f'CUT{self.index}'

    def get_RLOC_node(self, node: Node, origin):
        if node.tile_type == 'INT':
            tile = f'INT_{self.get_RLOC_coord(node.tile, origin)}'
            port = node.port
        else:
            tile = f'CLB_{node.bel_group[0]}_{self.get_RLOC_coord(node.tile, origin)}'
            port = node.port_suffix

        #with concurrent.futures.ProcessPoolExecutor() as executor:
            #RLOC_nodes = executor.map(self.get_RLOC_node, cut.nodes, product({origin}, repeat=len(cut.nodes)))

        return f'{tile}/{port}'

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

        for function, LUT_ins in cut.LUTs_func_dict.items():
            for LUT_in in LUT_ins:
                R_LUT_in = copy.deepcopy(LUT_in)
                R_LUT_in.name = nodes_dict[LUT_in.name]
                extend_dict(self.LUTs_func_dict, function, R_LUT_in, value_type='set')

        for ff in cut.FFs_set:
            R_ff = copy.deepcopy(ff)
            R_ff.name = nodes_dict[ff.name]
            self.FFs_set.add(R_ff)

        return G

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
    def get_direction(clb_node):
        return clb_node.split('_')[1]

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
        #self.not_LUT        = None
        self.LUTs_func_dict = {}
        self.FFs_set        = set()
        self.origin         = origin
        self.index          = R_CUT.index
        self.G              = self.get_DLOC_G(device, TC, R_CUT)

    def __repr__(self):
        return f'CUT{self.index}_{self.origin}'

    #def __eq__(self, other):
        #return f'CUT{self.index}_{self.origin}' == f'CUT{other.index}_{other.origin}'

    def get_DLOC_G(self, device, TC, R_CUT):
        nodes_dict = {}
        G = nx.DiGraph()

        for node in R_CUT.G:
            DLOC_node = self.get_DLOC_node(device, node)
            if DLOC_node is None:
                self.reason = 'invalid DLOC_node'
                return None

            tile = self.get_tile(DLOC_node)
            port = self.get_port(DLOC_node)
            if tile in TC.used_nodes_dict:
                if port in TC.used_nodes_dict[tile]:
                    self.reason = 'Collision'
                    return None     #Collision

            if re.match(GM.LUT_in_pattern, DLOC_node):
                neigh = list(R_CUT.G.neighbors(node))
                if neigh:
                    neigh = neigh[0]
                    MUX_flag = neigh.endswith('MUX')
                else:
                    MUX_flag = False

                LUT_key = Node(DLOC_node).bel_key
                N = 2 if (DLOC_node[-1] == 6 or not GM.LUT_Dual or MUX_flag) else 1
                if TC.get_LUT_capacity(LUT_key) < N:
                    self.reason = 'LUT over utelization'
                    return None     #LUT over utelization

            nodes_dict[node] = DLOC_node

        for edge in R_CUT.G.edges():
            DLOC_edge = (nodes_dict[edge[0]], nodes_dict[edge[1]])
            if self.is_wire(DLOC_edge):
                if DLOC_edge not in device.wires_dict[self.get_tile(DLOC_edge[0])]:
                    self.reason = 'wire heterogeneity'
                    return None

            label = R_CUT.G.get_edge_data(*edge)['path_type']
            G.add_edge(nodes_dict[edge[0]], nodes_dict[edge[1]], path_type=label)

        for function, LUT_ins in R_CUT.LUTs_func_dict.items():
            for LUT_in in LUT_ins:
                D_LUT_in = copy.deepcopy(LUT_in)
                D_LUT_in.name = nodes_dict[LUT_in.name]
                if function == 'buffer':
                    neigh = list(G.neighbors(D_LUT_in.name))[0]
                    neigh_type = 'O' if re.match(GM.CLB_out_pattern, neigh) else 'MUX'
                else:
                    neigh_type = None
                    #self.not_LUT = (D_LUT_in.bel_key, D_LUT_in.name)

                extend_dict(TC.LUTs, D_LUT_in.bel_key, (D_LUT_in.name, function, neigh_type))
                extend_dict(self.LUTs_func_dict, function, D_LUT_in)

        for ff in R_CUT.FFs_set:
            D_ff = copy.deepcopy(ff)
            D_ff.name = nodes_dict[ff.name]
            extend_dict(TC.FFs, D_ff.bel_key, D_ff.name)
            self.FFs_set.add(D_ff.bel_key)

        return G

    def get_DLOC_coord(self, tile, D_coord):
        dx = self.get_x_coord(tile) + self.get_x_coord(D_coord)
        dy = self.get_y_coord(tile) + self.get_y_coord(D_coord)
        DLOC_coord = f'X{dx}Y{dy}'

        return DLOC_coord

    def get_DLOC_node(self, device, R_node):
        coordinate = self.get_DLOC_coord(self.get_tile(R_node), self.origin)
        if coordinate not in device.tiles_map:
            return None

        if R_node.startswith('INT'):
            tile = f'INT_{coordinate}'
            port = self.get_port(R_node)
        else:
            direction = self.get_direction(R_node)
            tile = device.tiles_map[coordinate][f'CLB_{direction}']
            if not tile:
                return None

            port = f'CLE_CLE_{self.get_slice_type(tile)}_SITE_0_{self.get_port(R_node)}'

        DLOC_node = f'{tile}/{port}'
        return DLOC_node

    def get_g_buffer(self):
        if list(filter(lambda x: re.match(GM.MUXED_CLB_out_pattern, x), self.G)):
            return "00"

        if 'buffer' in self.LUTs_func_dict:
            buffer_in = self.LUTs_func_dict['buffer'][0].name
            not_in = self.LUTs_func_dict['not'][0].name
            neigh = next(self.G.neighbors(buffer_in))
            src = [node for node in self.G if self.G.in_degree(node) == 0][0]
            sink = [node for node in self.G if self.G.out_degree(node) == 0 and re.match(GM.FF_in_pattern, node)][0]
            brnch_node = [node for node in self.G if self.G.out_degree(node) > 1]
            if brnch_node:
                brnch_node = brnch_node[0]
            elif self.LUTs_func_dict['not'][0].name == self.LUTs_func_dict['buffer'][0].name:
                brnch_node = self.LUTs_func_dict['not'][0].name
            else:
                breakpoint()

            src_sink_path = nx.shortest_path(self.G, src, sink)
            branch_sink_path = nx.shortest_path(self.G, brnch_node, sink)

            if buffer_in not in src_sink_path:
                g_buffer = "01"     #not_path belongs to Q_launch and route_thru is between brnc_node and not_in
            elif neigh in branch_sink_path:
                g_buffer = "10"     # not_path belongs to Q_launch
            else:
                g_buffer = "11"     #not_path belongs to route_thru
        else:
            g_buffer = "00"

        return g_buffer

    @property
    def RRG(self):
        RRG = nx.DiGraph()
        RRG.add_edges_from(self.G.edges())
        wires_end = {edge[1] for edge in self.G.edges if CUT.get_tile(edge[0]) != CUT.get_tile(edge[1])}
        for node in wires_end:
            new_edges = product(self.G.predecessors(node), self.G.neighbors(node))
            RRG.remove_node(node)
            RRG.add_edges_from(new_edges)

        return RRG

    def get_routing_constraint(self, NetName, RouteThruNetName=None):
        constraints = []
        g_buffer = self.get_g_buffer()
        if g_buffer == "00":
            constraints.append(f'set_property FIXED_ROUTE {self.routing_constraint} [get_nets {NetName}]\n')
        else:
            buffer_in = self.LUTs_func_dict['buffer'][0].name
            neigh = next(self.G.neighbors(buffer_in))
            not_in = self.LUTs_func_dict['not'][0].name
            sink = [node for node in self.G if self.G.out_degree(node) == 0 and re.match(GM.FF_in_pattern, node)][0]
            src = [node for node in self.G if self.G.in_degree(node) == 0][0]
            brnch_node = [node for node in self.G if self.G.out_degree(node) > 1]
            if brnch_node:
                brnch_node = brnch_node[0]
            elif self.LUTs_func_dict['not'][0].name == self.LUTs_func_dict['buffer'][0].name:
                brnch_node = self.LUTs_func_dict['not'][0].name
            else:
                breakpoint()

            self1 = copy.deepcopy(self)

            if g_buffer == "10":       #not_path belongs to Q_launch
                path1 = nx.shortest_path(self.G, src, buffer_in)
                path2 = nx.shortest_path(self.G, src, not_in)
                self1.G = nx.DiGraph()
                self1.G.add_edges_from(zip(path1, path1[1:]))
                self1.G.add_edges_from(zip(path2, path2[1:]))
                constraints.append(f'set_property FIXED_ROUTE {self1.routing_constraint} [get_nets {NetName}]\n')
                self1.G = nx.DiGraph()
                path3 = nx.shortest_path(self.G, neigh, sink)
                self1.G.add_edges_from(zip(path3, path3[1:]))
                constraints.append(
                    f'set_property FIXED_ROUTE {self1.routing_constraint} [get_nets {RouteThruNetName}]\n')
            elif g_buffer == "01":
                path1 = nx.shortest_path(self.G, src, sink)
                path2 = nx.shortest_path(self.G, src, buffer_in)
                self1.G = nx.DiGraph()
                self1.G.add_edges_from(zip(path1, path1[1:]))
                self1.G.add_edges_from(zip(path2, path2[1:]))
                constraints.append(f'set_property FIXED_ROUTE {self1.routing_constraint} [get_nets {NetName}]\n')
                self1.G = nx.DiGraph()
                path3 = nx.shortest_path(self.G, neigh, not_in)
                self1.G.add_edges_from(zip(path3, path3[1:]))
                constraints.append(
                    f'set_property FIXED_ROUTE {self1.routing_constraint} [get_nets {RouteThruNetName}]\n')
            else:                       #not_path belongs to route_thru
                path1 = nx.shortest_path(self.G, src, buffer_in)
                self1.G = nx.DiGraph()
                self1.G.add_edges_from(zip(path1, path1[1:]))
                constraints.append(f'set_property FIXED_ROUTE {self1.routing_constraint} [get_nets {NetName}]\n')
                self1.G = nx.DiGraph()
                path2 = nx.shortest_path(self.G, neigh, sink)
                path3 = nx.shortest_path(self.G, neigh, not_in)
                self1.G.add_edges_from(zip(path2, path2[1:]))
                self1.G.add_edges_from(zip(path3, path3[1:]))
                constraints.append(
                    f'set_property FIXED_ROUTE {self1.routing_constraint} [get_nets {RouteThruNetName}]\n')

        return constraints

    @property
    def routing_constraint(self):
        branch_dct = {}
        self.get_branches(self.RRG, branch_dct)
        source = [node for node in self.RRG if self.RRG.in_degree(node) == 0][0]
        for key in branch_dct.keys().__reversed__():
            for b_idx, lst in enumerate(branch_dct[key]):
                for n_idx, node in enumerate(lst):
                    if node in branch_dct:
                        for nested_branch in branch_dct[node]:
                            branch_dct[key][b_idx][n_idx] += f" {{{' '.join(Node(node).port for node in nested_branch)}}}"

        if len(branch_dct[source]) > 1:
            constraint = f"{Node(source).port}"
            for branch in branch_dct[source][1:]:
                constraint += f" {{{' '.join(Node(node).port for node in branch)}}}"

            constraint += f" {' '.join(Node(node).port for node in branch_dct[source][0])}"
        else:
            constraint = f"{Node(source).port} {' '.join(Node(node).port for node in branch_dct[source][0])}"

        return f'{{{constraint}}}'

    @staticmethod
    def get_branches(G_net, branch_dct={}):
        source = [node for node in G_net if G_net.in_degree(node) == 0][0]
        for neigh in G_net.neighbors(source):
            T = nx.dfs_tree(G_net, neigh)
            trunk = nx.dag_longest_path(T)
            T.remove_edges_from(set(zip(trunk, trunk[1:])))
            T.remove_nodes_from({node for node in T if nx.is_isolate(T, node)})
            #ports_only = [Node(node).port for node in trunk]
            ports_only = trunk.copy()
            CUT.extend_dict(branch_dct, source, ports_only)
            fanout_nodes = [node for node in trunk if G_net.out_degree(node) > 1]
            if not fanout_nodes:
                continue

            for node in fanout_nodes:
                G_net2 = nx.dfs_tree(T, node)
                DLOC.get_branches(G_net2, branch_dct)

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
    def get_direction(clb_node):
        return clb_node.split('_')[1]

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