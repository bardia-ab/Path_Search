import heapq, os, copy

import Global_Module
from resources.tile import *
from resources.primitive import *
from Functions import extend_dict, weight_function, load_data

class Arch:
    def __init__(self, G):
        self.G          = G
        self.Init_tile_port_dict()
        self.tiles      = set()
        self.wires_dict = {}
        self.init_tiles()
        self.Init_tile_node_dicts()
        self.reform_cost()
        self.weight = weight_function(G, 'weight')

    def init_tiles(self):
        all_edges = {Edge(edge) for edge in self.G.edges()}
        for tile, tile_nodes in self.tile_port_dict.items():
            tile1 = Tile(tile, self.G, tile_nodes)
            tile1.edges = set(filter(lambda x: re.search(tile1.name, f'{x.u} {x.v}'), all_edges))
            self.tiles.add(tile1)

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

    def Init_tile_port_dict(self):
        self.tile_port_dict = {}
        for node in self.G:
            extend_dict(self.tile_port_dict, self.get_tile(node), self.get_port(node), value_type='set')

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
        for clb in self.get_tiles(type='CLB'):
            for i in range(65, 73):
                FFs.add(f'{clb.name}/{chr(i)}FF')
                FFs.add(f'{clb.name}/{chr(i)}FF2')

        FFs = {FF(ff) for ff in FFs if ff not in blocked_FFs}

        return FFs

    def gen_LUTs(self, TC, TC_total=None):
        blocked_LUTs = TC_total.blocked_LUTs if TC_total else set()
        LUTs = set()
        for clb in self.get_tiles(type='CLB'):
            for i in range(65, 73):
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
        for k, v in attributes.items():
            nodes = set()
            for node in all_nodes:
                if getattr(node, k) == v:
                    nodes.add(node)

            all_nodes = nodes.copy()

        return all_nodes


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
    def port_suffix(node):
        return node.split('_SITE_0_')[-1]


    def reconstruct_device(self, l, coord):
        queue = list(GM.pips_length_dict)
        if l > 1:
            files = sorted(os.listdir(os.path.join(GM.store_path, f'iter{l - 1}')),
                           key=lambda x: int(re.findall('\d+', x).pop()), reverse=False)
            TC_last = load_data(os.path.join(GM.store_path, f'iter{l - 1}'), files[-1])
            for edge in TC_last.G_dev.edges():
                if edge in self.G.edges():
                    if edge not in TC_last.G:
                        continue  # route_thrus

                    self.G.get_edge_data(*edge)['weight'] = TC_last.G.get_edge_data(*edge)['weight']

            pips_dict = load_data(GM.Data_path, 'covered_pips_dict.data')
            tile = f'INT_{coord}'
            pips = pips_dict[tile]
            pips = {(f'{tile}/{pip[0]}', f'{tile}/{pip[1]}') for pip in pips}
            queue = list(set(queue) - pips)


        return queue

    def reform_cost(self):
        for edge in self.G.edges():
            if self.get_tile(edge[0]) == self.get_tile(edge[1]):
                if self.get_tile(edge[0]).startswith('CLE'):
                    if re.match(Global_Module.MUXED_CLB_out_pattern, edge[0]) or re.match(Global_Module.MUXED_CLB_out_pattern, edge[1]):
                        weight = 100
                    elif re.match(Global_Module.LUT_in6_pattern, edge[0]):
                        weight = 50
                    else:
                        weight = 25  # CLB_Route_Thru
                else:
                    continue
            else:
                continue

            self.G.get_edge_data(*edge)['weight'] = weight

    def blocking_nodes(self, CD, tile):
        #these are out mode nodes that have pips back to the INT tile
        blocking_nodes = {node.name for node in self.get_nodes(tile=tile, mode='out') if self.G.out_degree(node.name)>1}
        valid_blocking_nodes = set()
        for node in blocking_nodes:
            clb_neighs = list(
                filter(lambda x: Node(x).clb_node_type == 'FF_in' and CD[Node(x).bel_group] != 'launch',
                       self.G.neighbors(node)))
            if clb_neighs:
                valid_blocking_nodes.add(node)

        return valid_blocking_nodes

    @staticmethod
    def get_other_half_group(group):
        half_dict = {'T': 'B', 'B': 'T'}
        direc_dict = {'E': 'W', 'W': 'E'}

        return f'{group[0]}_{half_dict[group[-1]]}'

    def get_local_pips(self, coordinate):
        desired_tile = 'INT_' + coordinate
        G = copy.deepcopy(self.G)
        invalid_nodes = [node for node in G if Node(node).coordinate != coordinate]
        G.remove_nodes_from(invalid_nodes)
        G_copy = copy.deepcopy(G)

        pips = {edge for edge in G.edges if Arch.get_tile(edge[0]) == Arch.get_tile(edge[1]) == desired_tile}
        all_sources = list(filter(GM.Source_pattern.match, G))
        all_sinks = list(filter(GM.Sink_pattern.match, G))
        groups = ['W_T', 'W_B', 'E_T', 'E_B']
        covered_pips = set()

        for group in groups:
            other_group = Arch.get_other_half_group(group)
            sources = {node for node in all_sources if Node(node).bel_group == group}
            sinks = {node for node in all_sinks if Node(node).bel_group == other_group}
            forbidden_nodes = {node for node in G if Node(node).bel_group if Node(node).bel_group[0] != group[0]}
            G.remove_nodes_from(forbidden_nodes)

            edges = set(product({'s'}, sources))
            for edge in edges:
                G.add_edge(*edge, weight=0)

            edges = set(product(sinks, {'t'}))
            for edge in edges:
                G.add_edge(*edge, weight=0)

            if not (sources and sinks):
                continue

            pip_u = {pip[0] for pip in pips}
            pip_v = {pip[1] for pip in pips}

            no_path_ports = set()
            for node in pip_u:
                if not nx.has_path(G, 's', node):
                    no_path_ports.add(node)

            for node in pip_v:
                if not nx.has_path(G, node, 't'):
                    no_path_ports.add(node)

            excess_edges = set()
            for node in no_path_ports:
                excess_edges.update(G.in_edges(node))
                excess_edges.update(G.out_edges(node))

            G.remove_edges_from(excess_edges)
            queue = pips - excess_edges

            for pip in pips:
                if nx.has_path(G, 's', pip[0]) and nx.has_path(G, pip[1], 't'):
                    covered_pips.add(pip)

            G = copy.deepcopy(G_copy)

        return covered_pips