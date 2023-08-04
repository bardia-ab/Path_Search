import heapq

import Global_Module
from resources.tile import *
from resources.primitive import *
from Functions import extend_dict, weight_function
class Arch:
    def __init__(self, G):
        self.G          = G
        self.tiles      = set()
        self.wires_dict = {}
        self.init_tiles()
        self.reform_cost()
        self.weight = weight_function(G, 'weight')

    def init_tiles(self):
        all_edges = {Edge(edge) for edge in self.G.edges()}
        tiles_set = {Arch.get_tile(node) for node in self.G}
        for tile in tiles_set:
            tile1 = Tile(tile, self.G)
            tile1.edges = set(filter(lambda x: re.search(tile1.name, f'{x.u} {x.v}'), all_edges))
            self.tiles.add(tile1)

    def gen_FFs(self):
        FFs = set()
        for clb in self.get_tiles(type='CLB'):
            for i in range(65, 73):
                FFs.add(FF(f'{clb.name}/{chr(i)}FF'))
                FFs.add(FF(f'{clb.name}/{chr(i)}FF2'))

        return FFs

    def gen_LUTs(self):
        LUTs = set()
        for clb in self.get_tiles(type='CLB'):
            for i in range(65, 73):
                LUTs.add(LUT(f'{clb.name}/{chr(i)}5LUT'))
                LUTs.add(LUT(f'{clb.name}/{chr(i)}6LUT'))

        return LUTs

    def get_tiles(self, **attributes):
        tiles = set()
        for tile in self.tiles:
            for attr in attributes:
                if getattr(tile, attr) != attributes[attr]:
                    break
            else:
                tiles.add(tile)


        return tiles

    def get_nodes(self, **attributes):
        all_nodes = {node for tile in self.tiles for node in tile.nodes}
        nodes = set()
        for node in all_nodes:
            for attr in attributes:
                if getattr(node, attr) != attributes[attr]:
                    break
            else:
                nodes.add(node)

        return nodes

    def get_edges(self, **attributes):
        all_edges = {edge for tile in self.tiles for edge in tile.edges}
        edges = set()
        for edge in all_edges:
            for attr in attributes:
                if getattr(edge, attr) != attributes[attr]:
                    break
            else:
                edges.add(edge)

        return edges

    def set_wires_dict(self, coord):
        tile = 'INT_' + coord
        for edge in self.G.edges():
            if len(list(filter(lambda x: re.search(tile, x), edge))) != 2:
                for node in edge:
                    if re.search(tile, node):
                        key = node

                    if not re.search(tile, node):
                        value = node

                extend_dict(self.wires_dict, key, value)
                extend_dict(self.wires_dict, value, key)

    def get_wire(self, node):
        if node in self.wires_dict:
            return self.wires_dict[node]
        else:
            return None

    def set_level(self, G, coord):
        mid_back = set()
        node_level = {}
        int_tile = self.get_tiles(type='INT', coordinate=coord).pop()
        queue = list(self.get_nodes(tile_type='INT', mode='in', coordinate=coord))
        next_queue = set()
        level = 0
        while len(node_level) != len(int_tile.nodes):
            level += 1
            neighs = set()
            for node in queue:
                neighs.update(G.neighbors(node.name))
                node_level[node.name] = level

            for neigh in neighs:
                neigh1 = self.get_nodes(name=neigh).pop()
                if neigh1.tile != int_tile.name:
                    continue
                elif neigh1.name not in node_level:
                    next_queue.add(neigh1)
                else:
                    mid_back.add(neigh1)

            queue = list(next_queue).copy()
            next_queue = set()

        for node in int_tile.nodes:
            node.level = node_level[node.name]

        return mid_back

    def get_clb_nodes(self, type):
        all_nodes = {node for tile in self.tiles for node in tile.nodes}
        if type == 'LUT_in':
            return set(filter(lambda x: re.match(GM.LUT_in_pattern, x.name), all_nodes))
        elif type == 'FF_in':
            return set(filter(lambda x: re.match(GM.FF_in_pattern, x.name), all_nodes))
        elif type == 'FF_out':
            return set(filter(lambda x: re.match(GM.FF_out_pattern, x.name), all_nodes))
        elif type == 'CLB_out':
            return set(filter(lambda x: re.match(GM.CLB_out_pattern, x.name), all_nodes))
        elif type == 'CLB_muxed':
            return set(filter(lambda x: re.match(GM.MUXED_CLB_out_pattern, x.name), all_nodes))

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
                path_in = nx.shortest_path(self.G, 's', pip[0], weight='weight')[1:]
                path_out = nx.shortest_path(self.G, pip[1], 't', weight='weight')[:-1]
                GM.pips_length_dict[(pip.u, pip.v)] = len(path_in + path_out)
            except:
                continue

        self.G.remove_nodes_from(['s', 't'])

    @staticmethod
    def get_tile(wire, delimiter='/'):
        return wire.split(delimiter)[0]

    @staticmethod
    def get_port(wire, delimiter='/'):
        return wire.split(delimiter)[1]


    def reform_cost(self):
        for edge in self.G.edges():
            if self.get_tile(edge[0]) == self.get_tile(edge[1]):
                if self.get_tile(edge[0]).startswith('CLE'):
                    if re.match(Global_Module.LUT_in6_pattern, edge[0]):
                        weight = 50
                    else:
                        weight = 25  # CLB_Route_Thru
                else:
                    continue
            else:
                continue

            self.G.get_edge_data(*edge)['weight'] = weight

    def blocking_nodes(self, tile):
        #these are out mode nodes that have pips back to the INT tile
        return {node.name for node in self.get_nodes(tile=tile, mode='out') if self.G.out_degree(node.name)>1}