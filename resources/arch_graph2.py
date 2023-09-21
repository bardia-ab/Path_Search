import os
from resources.edge import Edge
from resources.primitive import *
from Functions import extend_dict, load_data
from router import weight_function
import networkx as nx

class Arch:
    def __init__(self, G):
        self.G                  = G
        self.pips_length_dict   = {}
        #self.Init_tile_node_dicts()
        self.reform_cost()
        self.weight = weight_function(G, 'weight')


    def Init_tile_node_dicts(self):
        self.tile_dirc_dict = {}
        self.gnode_dict = {}
        for tile in self.tiles:
            if tile.type == 'CLB':
                self.tile_dirc_dict[tile.name] = tile.direction

            for node in tile.nodes:
                if node.tile_type == 'INT':
                    key = node.port
                    value = node.tile
                    extend_dict(self.gnode_dict, key, value, value_type='set')
                else:
                    key1 = node.port_suffix
                    key2 = node.bel_group[0]
                    value = node.tile
                    if key1 not in self.gnode_dict:
                        self.gnode_dict[key1] = {key2: {value}}
                    else:
                        extend_dict(self.gnode_dict[key1], key2, value, value_type='set')

    def get_gnodes(self, node):
        gnodes = set()
        if node.startswith('INT'):
            port = self.get_port(node)
            for tile in self.gnode_dict[port]:
                gnodes.add(f'{tile}/{port}')
        else:
            dirc = self.tile_dirc_dict[self.get_tile(node)]
            port_suffix = self.port_suffix(node)
            slice_type = self.get_slice_type(node)
            for tile in self.gnode_dict[port_suffix][dirc]:
                gnodes.add(f'{tile}/CLE_CLE_{slice_type}_SITE_0_{port_suffix}')

        return gnodes

    def gen_FFs(self, TC_total=None):
        blocked_FFs = TC_total.FFs if TC_total else set()
        FFs = set()
        tiles = (node.tile for node in self.get_nodes() if node.tile_type == 'CLB')
        for clb in tiles:
            for i in range(ord('A'), ord('H') + 1):
                FFs.add(f'{clb.name}/{chr(i)}FF')
                FFs.add(f'{clb.name}/{chr(i)}FF2')

        FFs = {FF(ff) for ff in FFs if ff not in blocked_FFs}

        return FFs

    def gen_LUTs(self, TC, TC_total=None):
        blocked_LUTs = TC_total.blocked_LUTs if TC_total else set()
        LUTs = set()
        tiles = (node.tile for node in self.get_nodes() if node.tile_type == 'CLB')
        for clb in tiles:
            for i in range(ord('A'), ord('H') + 1):
                LUTs.add(f'{clb.name}/{chr(i)}5LUT')
                LUTs.add(f'{clb.name}/{chr(i)}6LUT')

        LUTs = {LUT(lut) for lut in LUTs if lut not in blocked_LUTs}
        full_LUTs = set(filter(lambda x: re.match('CL.*5LUT', x), blocked_LUTs))
        partial_LUTs = set(filter(lambda x: re.match('CL.*6LUT', x), blocked_LUTs))

        full_LUTs_ins = {f'{self.get_tile(key)}/CLE_CLE_{self.get_slice_type(key)}_SITE_0_{self.get_port(key)[0]}{i}' for key in full_LUTs for i in range(1, 7)}
        partial_LUTs_i6 = {f'{self.get_tile(key)}/CLE_CLE_{self.get_slice_type(key)}_SITE_0_{self.get_port(key)[0]}6'
                         for key in partial_LUTs}
        partial_LUTs_mux = {f'{self.get_tile(key)}/CLE_CLE_{self.get_slice_type(key)}_SITE_0_{self.get_port(key)[0]}MUX' for key in partial_LUTs}
        in_graph_blocked_nodes = set(self.G) & full_LUTs_ins.union(partial_LUTs_i6).union(partial_LUTs_mux)
        TC.block_nodes = in_graph_blocked_nodes
        TC.reconst_block_nodes.update(in_graph_blocked_nodes)
        TC.G.remove_nodes_from(in_graph_blocked_nodes)

        return LUTs

    def get_nodes(self, **attributes):
        all_nodes = (Node(node) for node in self.G)
        for k, v in attributes.items():
            nodes = set()
            for node in all_nodes:
                if getattr(node, k) == v:
                    nodes.add(node)

            all_nodes = nodes.copy()

        return all_nodes

    def get_edges(self, **attributes):
        all_edges = (Edge(edge) for edge in self.G.edges)
        edges = set()
        for edge in all_edges:
            for attr in attributes:
                if getattr(edge, attr) != attributes[attr]:
                    break
            else:
                edges.add(edge)

        return edges

    def get_pips_length(self, coordinate):
        tile = f'INT_{coordinate}'
        pips = self.get_edges(u_tile=tile, v_tile=tile)
        sources = {node.name for node in self.get_nodes(clb_node_type='FF_out')}
        sinks = {node.name for node in self.get_nodes(clb_node_type='FF_in')}

        for src in sources:
            self.G.add_edge('s', src, weight=0)

        for sink in sinks:
            self.G.add_edge(sink, 't', weight=0)

        for pip in pips:
            try:
                path_in = nx.shortest_path(self.G, 's', pip.u, weight='weight')[1:]
                path_out = nx.shortest_path(self.G, pip.v, 't', weight='weight')[:-1]
                self.pips_length_dict[(pip.u, pip.v)] = len(path_in + path_out)
            except:
                continue

        self.G.remove_nodes_from(['s', 't'])

    def get_queue(self, coordinate, load_path=None):
        self.get_pips_length(coordinate)
        queue = list(self.pips_length_dict)
        if load_path is not None:
            pips_dict = load_data(load_path, 'covered_pips_dict.data')
            tile = f'INT_{coordinate}'
            pips = pips_dict[tile]
            pips = {(f'{tile}/{pip[0]}', f'{tile}/{pip[1]}') for pip in pips}
            queue = list(set(queue) - pips)

        return queue

    def reform_cost(self):
        for edge in self.get_edges():
            if edge.type == 'pip':
                if edge[0].tile_type == 'CLB':
                    if any(map(lambda x: x.clb_node_type == 'CLB_muxed', edge)):
                        weight = 100
                    elif edge[0].is_i6:
                        weight = 100
                    else:
                        weight = 25  # CLB_Route_Thru
                else:
                    continue
            else:
                continue

            self.G.get_edge_data(*edge)['weight'] = weight

    def blocking_nodes(self, CD, tile):
        #these are out mode nodes that have pips back to the INT tile
        out_mode_nodes = (node for node in self.get_nodes() if node.get_INT_node_mode(self.G) == 'out')
        blocking_nodes = {node.name for node in out_mode_nodes if self.G.out_degree(node.name)>1}
        valid_blocking_nodes = set()
        for node in blocking_nodes:
            if any(map(lambda x: Node(x).clb_node_type == 'FF_in' and CD[Node(x).bel_group] != 'launch', self.G.neighbors(node))):
                valid_blocking_nodes.add(node)

        return valid_blocking_nodes

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]

    @staticmethod
    def get_port(wire, delimiter='/'):
        return wire.split(delimiter)[1]


    @staticmethod
    def get_slice_type(tile):
        if tile.startswith('CLEM'):
            return 'M'
        else:
            return 'L'

    @staticmethod
    def port_suffix(node):
        return node.split('_SITE_0_')[-1]