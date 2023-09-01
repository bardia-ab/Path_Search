import re

import networkx as nx

from resources.cut import CUT
from resources.node import Node
from resources.edge import Edge
from resources.path import Path
from resources.primitive import LUT
from Functions import *
from itertools import product
import Global_Module as GM
from tqdm import tqdm, trange
import copy, time

class Configuration():

    def __init__(self, device, TC_total=None):
        self.G                      = copy.deepcopy(device.G)
        self.G_TC                   = nx.DiGraph()
        self._block_nodes           = set()
        self.reconst_block_nodes    = set()
        self._block_edges           = set()
        self.FFs                    = device.gen_FFs(TC_total)
        self.LUTs                   = device.gen_LUTs(self, TC_total)
        self.CD                     = {'W_T': None, 'W_B': None, 'E_T': None, 'E_B': None}
        self.CUTs                   = []
        self.tried_pips             = set()
        self.route_thrus            = {}
        self.long_TC_process_time   = 120
        self.assign_source_sink()
        if TC_total:
            blocked_nodes = {f'{tile}/{port}' for tile, ports in TC_total.used_nodes_dict.items() for port in ports}
            #blocked_LUT_ins = set(filter(lambda x: re.match(GM.LUT_in_pattern, x), blocked_nodes))
            #blocked_i6 = {LUT_in[:-1] + '6' for LUT_in in blocked_LUT_ins}
            #blocked_nodes.update(blocked_i6)
            self.block_nodes = blocked_nodes
            self.reconst_block_nodes.update(blocked_nodes)
            self.G.remove_nodes_from(blocked_nodes)
            self.CD = TC_total.CD.copy()
            for group, function in self.CD.items():
                self.remove_source_sink(device, group, function)

            edges = set(product({'s'}, TC_total.invalid_source_FFs))
            self.G.remove_edges_from(edges)

        self.start_TC_time = time.time()

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

    @property
    def block_edges(self):
        return self._block_edges
    
    @block_edges.setter
    def block_edges(self, edges):
        if isinstance(edges, tuple):
            edges = list(edges)
        elif isinstance(edges, Edge):
            edges = list(edges.name)
            
        for edge in edges:
            if isinstance(edge, Edge):
                edge = edge.name

            if edge[0] == 'out_node':
                continue
                
            self._block_edges.add(edge)
            self.G.remove_edge(*edge)
    
    @property
    def block_nodes(self):
        return self._block_nodes

    @block_nodes.setter
    def block_nodes(self, nodes):
        if isinstance(nodes, str) or isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            if isinstance(node, Node):
                node = node.name

            #in_edges = list(self.G.in_edges(node))
            #self.block_edges = in_edges
            self._block_nodes.add(node)
                
    def unblock_nodes(self, device, nodes):
        if isinstance(nodes, str) or isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            if isinstance(node, Node):
                if Node.primitive == 'LUT':
                    blocked_subLUTs = self.get_LUTs(tile=node.tile, letter=node.bel, usage='blocked')
                    if len(blocked_subLUTs) == 2:
                        continue
                    elif len(blocked_subLUTs) == 1 and node.is_i6:
                        continue

                node = node.name

            try:
                self._block_nodes.remove(node)
            except:
                pass
                #breakpoint()

            in_edges = set(device.G.in_edges(node))
            self._block_edges = self._block_edges - in_edges
            self.add_edges(*in_edges, device=device)

    def add_edges(self, *edges, device=None, weight=None):
        for edge in edges:
            if {edge[0], edge[1]} & self.reconst_block_nodes:
                continue

            if edge[1] in self._block_nodes:
                continue

            if weight is None:
                weight = device.G.get_edge_data(*edge)['weight']

            self.G.add_edge(*edge, weight=weight)
    
    def block_nodes2(self, nodes):
        in_edges = set()

        if isinstance(nodes, str) or isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            if isinstance(node, Node):
                if node.primitive == 'LUT': #in_edge of LUT_ins is a wire and not removed
                    self._block_nodes.add(node.name)
                    node = list(self.G.predecessors(node.name))[0]
                else:
                    node = node.name

            if isinstance(node, str):
                if re.match(GM.LUT_in_pattern, node):
                    self._block_nodes.add(node)
                    node = list(self.G.predecessors(node))[0]

            self._block_nodes.add(node)
            in_edges.update(self.G.in_edges(node))

        in_edges = {edge for edge in in_edges if get_tile(edge[0]) == get_tile(edge[1])}
        self.G.remove_edges_from(in_edges)

    def unblock_nodes2(self, device, nodes):
        if isinstance(nodes, str) or isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            if isinstance(node, Node):
                if node.primitive == 'LUT': #in_edge of LUT_ins is a wire and not removed
                    try:
                        self._block_nodes.remove(node.name)
                    except:
                        breakpoint()

                    node = list(self.G.predecessors(node.name))[0]
                else:
                    node = node.name

                if isinstance(node, str):
                    if re.match(GM.LUT_in_pattern, node):
                        self._block_nodes.remove(node)
                        node = list(self.G.predecessors(node))[0]
            try:
                self._block_nodes.remove(node)
            except:
                #print(f'***{node}***')
                continue
                #breakpoint()

            for edge in device.G.in_edges(node):
                self.G.add_edge(*edge, weight=device.G.get_edge_data(*edge)['weight'])

    def block_path(self, device, path):
        #nodes = [node for node in path if node.primitive != 'LUT']
        self.block_nodes = path
        global_nodes = set()
        for node in path:
            '''if node.tile_type == 'INT':
                global_nodes.update(device.get_nodes(port=node.port))
            else:
                global_nodes.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))'''
            global_nodes = device.get_gnodes(node.name)

        global_nodes = global_nodes - set(path)
        if GM.block_mode == 'global':
            self.block_nodes = global_nodes
        else:
            self.penalize_nodes(global_nodes)

    def penalize_nodes(self, nodes):
        in_edges = set()

        if isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            #self._block_nodes.add(node)
            in_edges.update(self.G.in_edges(node.name))
            #in_edges.update(self.G.out_edges(node.name))

        for edge in in_edges:
            if self.G.get_edge_data(*edge)['weight'] >= 1e4:
                # as we extract the edges, some nodes count twice
                continue

            self.G.get_edge_data(*edge)['weight'] += 1e4

    def relax_nodes(self, nodes):
        in_edges = set()

        if isinstance(nodes, Node):
            nodes = [nodes]

        for node in nodes:
            #self._block_nodes.remove(node)
            in_edges.update(self.G.in_edges(node.name))

        for edge in in_edges:
            if self.G.get_edge_data(*edge)['weight'] <= 1e4:
                continue
                breakpoint()

            self.G.get_edge_data(*edge)['weight'] -= 1e4

    def get_FFs(self, **attributes):
        all_FFs = self.FFs.copy()
        for k, v in attributes.items():
            FFs = set()
            for node in all_FFs:
                if getattr(node, k) == v:
                    FFs.add(node)

            all_FFs = FFs.copy()

        return all_FFs


    def get_LUTs(self, **attributes):
        all_LUTs = self.LUTs.copy()
        for k, v in attributes.items():
            LUTs = set()
            for node in all_LUTs:
                if getattr(node, k) == v:
                    LUTs.add(node)

            all_LUTs = LUTs.copy()

        return all_LUTs

    def create_CUT(self, coord, pip):
        cut = CUT(coord, pip=pip)
        self.CUTs.append(cut)
        if pip is not None:
            self.block_nodes = pip

    def add_path(self, device, path):
        self.set_CDs(device, path)  #always before block_paths
        cut = self.CUTs[-1]
        cut.paths.append(path)
        #for edge in path.edges:
            #self.add_edge_CUT(device, edge)
        self.block_path(device, path)

        #extract FFs & LUTs in G
        FFs_set         = path.FFs().copy()
        LUTs_func_dict  = path.LUTs_dict().copy()
        cut.FFs_set.update(FFs_set)
        cut.update_LUTs(LUTs_func_dict)
        # set their usage
        if GM.block_mode == 'global':
           FFs_set = self.get_global_FFs(device, FFs_set)
           LUTs_func_dict = self.get_global_LUTs(device, LUTs_func_dict)

        self.update_FFs('used', FFs_set)
        self.set_LUTs(device, 'used', LUTs_func_dict)
        self.block_source_sink(device, path)

    def remove_CUT(self, device):
        cut = self.CUTs[-1]
        #self.unblock_nodes(device, cut.nodes)

#        global_nodes = set()
        for path in reversed(cut.paths):
            global_nodes = set()
            self.unblock_nodes(device, path.nodes)
            self.reset_CDs(device, path)
            for node in path:
                '''if node.tile_type == 'INT':
                    global_nodes.update(device.get_nodes(port=node.port))
                else:
                    global_nodes.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))'''
                global_nodes = device.get_gnodes(node.name)

            global_nodes = global_nodes - set(path)
            if GM.block_mode == 'global':
                self.unblock_nodes(device, global_nodes)
            else:
                self.relax_nodes(global_nodes)

            self.unblock_source_sink(device, path)  #always after unblock_nodes


        #reset primitive usage
        if GM.block_mode == 'global':
            FFs_set = self.get_global_FFs(device, cut.FFs_set)
            LUTs_func_dict = self.get_global_LUTs(device, cut.LUTs_func_dict)
        else:
            FFs_set = cut.FFs_set.copy()
            LUTs_func_dict = cut.LUTs_func_dict.copy()

        self.update_FFs('free', FFs_set)
        self.reset_LUTs(device, LUTs_func_dict)
        if not self.CUTs and self.block_nodes:
            breakpoint()

        self.CUTs.remove(cut)

    def finalize_CUT(self, device, int_tile):
        cut = self.CUTs[-1]
        self.G_TC = nx.compose(self.G_TC, cut.G)
        if not nx.is_forest(self.G_TC):
            breakpoint()

        if GM.block_mode == 'global':
           FFs_set = self.get_global_FFs(device, cut.FFs_set)
           LUTs_func_dict = self.get_global_LUTs(device, cut.LUTs_func_dict)
        else:
            FFs_set = cut.FFs_set.copy()
            LUTs_func_dict = cut.LUTs_func_dict.copy()

        self.update_FFs('blocked', FFs_set)
        self.set_LUTs(device, 'blocked', LUTs_func_dict)
        #increase cost
        main_path = self.CUTs[-1].main_path
        self.inc_cost(device, main_path, int_tile, 1/len(main_path), global_mode=True)
        self.remove_LUT_occupied_sources(device)
        out_node_neighs = {node.name for node in cut.nodes if 'out_node' in self.G.predecessors(node.name)}
        edges = set(product({'out_node'}, out_node_neighs))
        self.G.remove_edges_from(edges)

    def block_CUT(self, device):
        for cut in self.CUTs:
            nodes = {node.name for node in cut.nodes if node in device.G}
            Source = list(filter(lambda x: x.clb_node_type == 'FF_out', cut.nodes))[0]
            Sink = list(filter(lambda x: x.clb_node_type == 'FF_in', cut.nodes))[0]

            for source in device.get_nodes(bel_group=Source.bel_group, port_suffix=Source.port_suffix):
                self.G.remove_edge('s', source.name)

            for sink in device.get_nodes(bel_group=Sink.bel_group, port_suffix=Sink.port_suffix):
                self.G.remove_edge(sink.name, 't')

            self.block_nodes = nodes
            self.update_FFs('blocked', cut.FFs_set)
            self.set_LUTs(device, 'blocked', cut.LUTs_func_dict, next_iter_initalization=True)

    def update_FFs(self, usage, FFs):
        FF_primitives = set()
        for node in FFs:
            FF_primitives.update(self.get_FFs(name=node.bel_key))

        for FF_primitive in FF_primitives:
            if FF_primitive.usage == 'blocked':
                breakpoint()
            else:
                FF_primitive.usage = usage

    def set_LUTs(self, device, usage, LUTs_func_dict, next_iter_initalization=False):
        #usage: used|blocked
        #next_iter_initalization: True => next_iter
        for function, nodes in LUTs_func_dict.items():
            for node in nodes:
                LUT_primitives = self.get_subLUT(usage, node, next_iter_initalization)
                if not LUT_primitives:
                    continue

                for LUT_primitive in LUT_primitives:
                    LUT_primitive.inputs = node.name
                    LUT_primitive.func   = function
                    LUT_primitive.usage  = usage

                ### block i6
                i6_node = device.get_nodes(is_i6=True, bel=node.bel, tile=node.tile)
                self.block_nodes = i6_node

                ### block the other LUT's inputs
                if self.is_LUT_full(LUT_primitives[0]):
                    LUT_inputs = device.get_nodes(is_i6=False, bel=node.bel, tile=node.tile, primitive=node.primitive)
                    self.block_nodes = LUT_inputs

    def reset_LUTs(self, device, LUTs_func_dict):
        usage = 'free'
        for function, nodes in LUTs_func_dict.items():
            for node in nodes:
                LUT_primitives = self.get_subLUT(usage, node)
                if not LUT_primitives:
                    continue

                full_LUT = self.is_LUT_full(LUT_primitives[0])
                freed_LUT_ins = set()

                for LUT_primitive in LUT_primitives:
                    freed_LUT_ins.update(LUT_primitive.inputs)
                    LUT_primitive.clear()

                freed_LUT_ins = {node for LUT_in in freed_LUT_ins for node in device.get_nodes(name=LUT_in)}

                if self.is_LUT_free(LUT_primitives[0]):
                    ### unblock i6
                    i6_node = device.get_nodes(is_i6=True, bel=node.bel, tile=node.tile)
                    if i6_node != freed_LUT_ins:
                        self.unblock_nodes(device, i6_node)

                    ###unblock freed LUTs
                    #freed_LUT_ins = {node for LUT_in in freed_LUT_ins for node in device.get_nodes(name=LUT_in)}
                    #self.unblock_nodes(device, freed_LUT_ins)

                if full_LUT:
                    ### unblock the other LUT's inputs
                    used_LUT_in = {inp for prim in LUT_primitives if prim.inputs for inp in prim.inputs}
                    free_LUT_in = device.get_nodes(is_i6=False, bel=node.bel, tile=node.tile, primitive=node.primitive) - used_LUT_in
                    free_LUT_in = free_LUT_in - freed_LUT_ins
                    free_LUT_in = {node.name for node in free_LUT_in} - self.block_nodes
                    self.unblock_nodes(device, free_LUT_in)

    def get_subLUT(self, usage, node, next_iter_initalization=False):
        cut = self.CUTs[-1]
        muxed_node = list(filter(lambda x: re.match(GM.MUXED_CLB_out_pattern, x), cut.G))
        if muxed_node:
            muxed_node = muxed_node[0]
            pred = Node(next(cut.G.predecessors(muxed_node)))
            MUX_flag = pred.bel_group == node.bel_group and pred.bel == node.bel
        else:
            MUX_flag = False

        LUT_primitives = []
        if usage == 'free':
            LUT_primitives.extend(self.get_LUTs(tile=node.tile, letter=node.bel, type=node.primitive, usage='used'))
            LUT_primitives.sort(key=lambda x: x.name, reverse=False)  #[5LUT, 6LUT]
        elif usage == 'used':
            LUT_primitives.extend(self.get_LUTs(tile=node.tile, letter=node.bel, type=node.primitive, usage='free'))
            LUT_primitives.sort(key=lambda x: x.name, reverse=True)   #[6LUT, 5LUT]
            if not LUT_primitives:
                breakpoint()
        else:
            status = 'free' if next_iter_initalization else 'used'
            LUT_primitives.extend(self.get_LUTs(tile=node.tile, letter=node.bel, type=node.primitive, usage=status))
            LUT_primitives.sort(key=lambda x: x.name, reverse=True)   #[6LUT, 5LUT]

        if node.is_i6:
            return LUT_primitives
        elif MUX_flag:
            return LUT_primitives
        elif not GM.LUT_Dual:
            return LUT_primitives
        elif LUT_primitives:
            return LUT_primitives[:1]
        else:
            return []

    def is_LUT_full(self, lut):
        full = True
        if isinstance(lut, LUT):
            LUTs = self.get_LUTs(tile=lut.tile, letter=lut.letter)
        else:           #Node
            LUTs = self.get_LUTs(tile=lut.tile, bel=lut.bel)

        for Lut in LUTs:
            if Lut.usage == 'free':
                full = False
                break

        return full

    def is_LUT_free(self, lut):
        free = True
        if isinstance(lut, LUT):
            LUTs = self.get_LUTs(tile=lut.tile, letter=lut.letter)
        else:  # Node
            LUTs = self.get_LUTs(tile=lut.tile, bel=lut.bel)

        for Lut in LUTs:
            if Lut.usage != 'free':
                free = False
                break

        return free

    def get_global_FFs(self, device, FFs_set):
        global_FFs = set()
        TC_FF_keys = {ff.name for ff in self.FFs}
        for node in FFs_set:
            global_FFs.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))

        global_FFs = {node for node in global_FFs if node.bel_key in TC_FF_keys}
        return global_FFs

    def get_global_LUTs(self, device, LUTs_func_dict):
        global_LUTs_func_dict = {}
        TC_LUT_keys = {f'{lut.tile}/{lut.letter}LUT' for lut in self.LUTs}
        for function, nodes in LUTs_func_dict.items():
            global_LUTs = set()
            for node in nodes:
                global_LUTs.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))

            global_LUTs = {node for node in global_LUTs if node.bel_key in TC_LUT_keys}
            global_LUTs_func_dict[function] = global_LUTs.copy()

        return global_LUTs_func_dict

    def get_global_node_pattern(self, node):
        if node.startswith('INT'):
            pattern = f'^INT.*/{get_port(node)}$'
        else:
            direction = self.get_direction(node)

            pattern = f'^CLE.*/CLE_CLE_[LM]_SITE_0_{self.port_suffix(node)}$'

        return pattern

    def get_global_nodes(self, node):
        pattern = self.get_global_node_pattern(node)
        nodes = set(filter(lambda x: re.match(pattern, x), self.G))
        if node.startswith('CLE'):
            direction = self.get_direction(node)
            if direction == 'E':
                nodes = {node for node in nodes if node.startswith('CLEL_R')}
            else:
                nodes = {node for node in nodes if not node.startswith('CLEL_R')}

        return nodes

    def get_global_edges(self, edge):
        p1 = self.get_global_node_pattern(edge[0])
        p2 = self.get_global_node_pattern(edge[1])

        return set(filter(lambda x: re.match(p1, x[0]) and re.match(p2, x[1]), self.G.edges()))


    def inc_cost(self, device, path, tile, weight, global_mode=False):
        edges = set()
        for edge in path.edges:
            if global_mode:
                edges.update({Edge(e) for e in self.get_global_edges(edge)})
            else:
                edges.add(edge)

        for edge in edges:
            if edge.type == 'pip' and edge.u_tile==tile:
                device.G.get_edge_data(*edge)['weight'] += weight
            else:
                device.G.get_edge_data(*edge)['weight'] += 0.5

    def pick_PIP(self, device, queue):
        while (set(queue) - self.tried_pips):
            pip = queue[0]

            self.tried_pips.add(pip)
            # queue is updated, but only CUT edges are removed while not-path and capture paths edges are missing from G
            if pip not in self.G.edges():
                queue.append(queue.pop(0))
                continue
            # checks LUT_input6 condition
            if Node(pip[1]).is_i6:
                if not self.get_subLUT('used', Node(pip[1])):
                    queue.append(queue.pop(0))
                    continue

            self.decide_route_thrus(device, pip)

            break
        else:
            pip = None

        return pip

    def sort_pips2(self, pips):
        pips_dict = get_pips_dict(GM.nodes_dict, pips)

        return sorted(pips, key=pips_dict.get, reverse=True)

    def sort_pips(self, pips):
        return sorted(pips, key=lambda x: GM.pips_length_dict[x], reverse=True)

    def finish_TC(self, queue, pbar, free_cap=8):
        #capacity = free_cap - len(self.CUTs)
        l_covered_pips = 3424 - len(queue)
        cond2 = time.time() - self.start_TC_time > (self.long_TC_process_time + 15 * (l_covered_pips // 1000))
        cond3 = not queue
        try:
            cond4 = nx.has_path(self.G, 's', 't')
        except nx.exception.NodeNotFound:
            cond4 = False

        if cond2:
            #print('Long TC Process Time!!!')
            pbar.set_postfix_str('Long TC Process Time!!!')
            #print('-----------------------------------------------------')
            return True
        elif cond3:
            #print('Queue is empty!!!')
            pbar.set_postfix_str('Queue is empty!!!')
            #print('-----------------------------------------------------')
            return True
        elif not cond4:
            #print('No path between sourse and sink!!!')
            pbar.set_postfix_str('No path between sourse and sink!!!')
            #print('-----------------------------------------------------')
            return True
        else:
            return False

    def assign_source_sink(self):
        self.G.remove_nodes_from(['s', 't'])
        Sources = list(filter(GM.Source_pattern.match, self.G))
        Sinks = list(filter(GM.Sink_pattern.match, self.G))

        edges = set(product({'s'}, Sources))
        #self.G.add_edges_from(edges, weight=0)
        self.add_edges(*edges, weight=0)
        edges = set(product(Sinks, {'t'}))
        #self.G.add_edges_from(edges, weight=0)
        self.add_edges(*edges, weight=0)

    def block_source_sink(self, device, path):
        path_types = {
            'path_in'   : {'source'},
            'path_out'  : {'sink'},
            'main_path' : {'source', 'sink'}
        }
        if path.path_type not in path_types:
            return

        for node_type in path_types[path.path_type]:
            if node_type == 'source':
                source = [node for node in path if node.clb_node_type=='FF_out']
                if GM.block_mode == 'global':
                    sources = device.get_nodes(bel_group=source[0].bel_group, port_suffix=source[0].port_suffix)
                else:
                    sources = source

                sources = {node.name for node in sources}
                edges = set(product({'s'}, sources))
                self.G.remove_edges_from(edges)

            if node_type == 'sink':
                sink = [node for node in path if node.clb_node_type == 'FF_in']
                if GM.block_mode == 'global':
                    sinks = device.get_nodes(bel_group=sink[0].bel_group, port_suffix=sink[0].port_suffix)
                    #sinks.update(device.get_nodes(bel_group=sink[0].bel_group, bel=sink[0], clb_node_type='LUT_in'))
                else:
                    sinks = sink

                sinks = {node.name for node in sinks}
                edges = set(product(sinks, {'t'}))
                self.G.remove_edges_from(edges)

    def unblock_source_sink(self, device, path):
        path_types = {
            'path_in': {'source'},
            'path_out': {'sink'},
            'main_path': {'source', 'sink'}
        }
        if path.path_type not in path_types:
            return

        for node_type in path_types[path.path_type]:
            if node_type == 'source':
                source = [node for node in path if node.clb_node_type == 'FF_out']
                if GM.block_mode == 'global':
                    sources = device.get_nodes(bel_group=source[0].bel_group, port_suffix=source[0].port_suffix)
                else:
                    sources = source

                sources = {node.name for node in sources}
                edges = set(product({'s'}, sources))
                #self.G.add_edges_from(edges, weight=0)
                self.add_edges(*edges, weight=0)

            if node_type == 'sink':
                sink = [node for node in path if node.clb_node_type == 'FF_in']
                if GM.block_mode == 'global':
                    sinks = device.get_nodes(bel_group=sink[0].bel_group, port_suffix=sink[0].port_suffix)
                    # sinks.update(device.get_nodes(bel_group=sink[0].bel_group, bel=sink[0], clb_node_type='LUT_in'))
                else:
                    sinks = sink

                sinks = {node.name for node in sinks}
                edges = set(product(sinks, {'t'}))
                #self.G.add_edges_from(edges, weight=0)
                self.add_edges(*edges, weight=0)

    def set_CDs(self, device, path):
        clock_groups = {
            'path_in'       : ('launch' , None      ),
            'path_out'      : (None     , 'sample'  ),
            'main_path'     : ('launch' , 'sample'  ),
            'not'           : (None     , None      ),
            'capture_launch': (None     , None      ),
            'capture_sample': ('sample' , 'launch'  )
        }
        other_group_dict = {'W_T': 'W_B', 'W_B': 'W_T', 'E_T': 'E_B', 'E_B': 'E_T'}
        other_function_dict = {'launch': 'sample', 'sample': 'launch'}
        if clock_groups[path.path_type][0]:
            group = path[0].bel_group
            tile = path[0].tile
            other_group = other_group_dict[group]
            function = clock_groups[path.path_type][0]
            other_function = other_function_dict[function]
            if self.CD[group] is None:
                self.CD[group] = function
                self.CD[other_group] = other_function
                self.remove_source_sink(device, group, function, tile)
                self.remove_source_sink(device, other_group, other_function, tile)

            else:
                if self.CD[group] != clock_groups[path.path_type][0]:
                    breakpoint()
                    raise ValueError (f"Conflict in Clock Group {group}: {clock_groups[path.path_type][0]} group")

        if clock_groups[path.path_type][1]:
            group = path[-1].bel_group
            tile = path[-1].tile
            other_group = other_group_dict[group]
            function = clock_groups[path.path_type][1]
            other_function = other_function_dict[function]
            if not self.CD[group]:
                self.CD[group] = function
                self.CD[other_group] = other_function
                self.remove_source_sink(device, group, function, tile)
                self.remove_source_sink(device, other_group, other_function, tile)

            else:
                if self.CD[group] != clock_groups[path.path_type][1]:
                    breakpoint()
                    raise f"Conflict in Clock Group {group}: {clock_groups[path.path_type][1]} group"

    def remove_source_sink(self, device, group, function, tile=None):
        if function == 'launch':
            FFs_in = set()
            LUTs_in = set()
            FFs_in.update(device.get_nodes(bel_group=group, clb_node_type='FF_in'))
            #LUTs_in.update(device.get_nodes(bel_group=group, clb_node_type='LUT_in'))
            '''if GM.block_mode == 'global':
                FFs_in.update(device.get_nodes(bel_group=group, clb_node_type='FF_in'))
                LUTs_in.update(device.get_nodes(bel_group=group, clb_node_type='LUT_in'))
            else:
                FFs_in.update(device.get_nodes(tile=tile, bel_group=group, clb_node_type='FF_in'))
                LUTs_in.update(device.get_nodes(tile=tile, bel_group=group, clb_node_type='LUT_in'))'''

            FFs_in = {FF_in.name for FF_in in FFs_in}
            LUTs_in = {LUT_in.name for LUT_in in LUTs_in}

            removed_edges = set(product(FFs_in, {'t'}))
            removed_edges.update(set(product(LUTs_in, {'t'})))
            added_edges = set(product(FFs_in, {f't_{group}'}))
            added_edges.update(set(product(LUTs_in, {f't_{group}'})))
        elif function == 'sample':
            FFs_out = set()
            FFs_out.update(device.get_nodes(bel_group=group, clb_node_type='FF_out'))
            '''if GM.block_mode == 'global':
                FFs_out.update(device.get_nodes(bel_group=group, clb_node_type='FF_out'))
            else:
                FFs_out.update(device.get_nodes(tile=tile, bel_group=group, clb_node_type='FF_out'))'''

            FFs_out = {FF_out.name for FF_out in FFs_out}

            removed_edges = set(product({'s'}, FFs_out))
            added_edges = set(product({f's_{group}'}, FFs_out))
        else:
            removed_edges = []
            added_edges = []

        self.G.remove_edges_from(removed_edges)
        #self.G.add_edges_from(added_edges, weight=0)
        self.add_edges(*added_edges, weight=0)

    def remove_LUT_occupied_sources(self, device):
        launch_groups = {group for group in self.CD if self.CD[group] == 'launch'}
        occupied_LUTs = set()
        for group in launch_groups:
            occupied_LUTs.update((LUT_primitive.tile, LUT_primitive.letter) for LUT_primitive in self.get_LUTs(usage='blocked', bel_group=group) if self.is_LUT_full(LUT_primitive))

        FF_outs = set()
        for lut in occupied_LUTs:
            FF_outs.update(device.get_nodes(tile=lut[0], bel=lut[1], clb_node_type='FF_out'))

        FF_outs = {node.name for node in FF_outs}
        edges = set(product({'s'}, FF_outs))
        self.G.remove_edges_from(edges)

    def reset_CDs(self, device, path):
        if path.prev_CD != self.CD:
            restored_groups = [group for group in path.prev_CD if path.prev_CD[group] == None and path.prev_CD[group] != self.CD[group]]
            for group in restored_groups:
                function = self.CD[group]
                self.restore_source_sink(device, group, function)

            # Don't copy path.prev_CD in self.CD
            # Because path_in is reset first then two other paths and they set None values again
            #self.CD = path.prev_CD.copy()
            for key in self.CD:
                if self.CD[key]:
                    self.CD[key] = path.prev_CD[key]

    def restore_source_sink(self, device, group, function):
        if function == 'launch':
            FFs_in = set()
            LUTs_in = set()
            FFs_in.update(device.get_nodes(bel_group=group, clb_node_type='FF_in'))
            FFs_in = {FF_in.name for FF_in in FFs_in}
            LUTs_in.update(device.get_nodes(bel_group=group, clb_node_type='LUT_in'))
            LUTs_in = {LUT_in.name for LUT_in in LUTs_in}

            removed_edges = set(product(FFs_in, {f't_{group}'}))
            removed_edges.update(set(product(LUTs_in, {f't_{group}'})))
            added_edges = set(product(FFs_in, {'t'}))
        elif function == 'sample':
            FFs_out = set()
            FFs_out.update(device.get_nodes(bel_group=group, clb_node_type='FF_out'))
            FFs_out = {FF_out.name for FF_out in FFs_out}

            removed_edges = set(product({f's_{group}'}, FFs_out))
            added_edges = set(product({'s'}, FFs_out))

        else:
            removed_edges = []
            added_edges = []

        self.G.remove_edges_from(removed_edges)
        self.add_edges(*added_edges, weight=0)
        #self.G.add_edges_from(added_edges, weight=0)

    def remove_route_thrus(self, coord):
        LUT_ins = list(filter(lambda x: re.match(GM.LUT_in_pattern, x) and not re.search(coord, x), self.G))
        removed_edges = set()
        for LUT_in in LUT_ins:
            removed_edges.update(self.G.out_edges(LUT_in))


        self.G.remove_edges_from(removed_edges)

    '''def restore_route_thrus(self):
        for edge in self.route_thrus:
            if not set(edge) & self._block_nodes:
                #self.G.add_edge(*edge, weight=self.route_thrus[edge])
                for edge in self.route_thrus:
                    self.add_edges(edge, weight=self.route_thrus[edge])'''

    '''def decide_route_thru_path_out(self, device, pip_v):
        self.remove_route_thrus()
        if self.G.out_degree(pip_v) == 1:
            neigh_pip_v = list(self.G.neighbors(pip_v)).pop()
            if re.match(GM.LUT_in_pattern, neigh_pip_v):
                out_edges = list(device.G.out_edges(neigh_pip_v))
                self.add_edges(*out_edges, device=device)

    def decide_route_thru_path_in(self, device, pip_u):
        if self.G.in_degree(pip_u) == 1:
            pred_pip_u = list(self.G.predecessors(pip_u)).pop()
            if re.match(GM.Unregistered_CLB_out_pattern, pred_pip_u):
                in_edges = list(device.G.in_edges(pred_pip_u))
                self.add_edges(*in_edges, device=device)'''

    def decide_long_pips(self, device, pip):
        neigh_pip_v = list(device.G.neighbors(pip[1]))
        for neigh in neigh_pip_v:
            if re.search(get_port(pip[0]), neigh) and pip[0] != neigh:
                TC_nodes = {node for cut in self.CUTs for node in cut.G}
                if neigh not in TC_nodes:
                    self.unblock_nodes(device, neigh)

        pred_pip_u = list(device.G.predecessors(pip[0]))
        for pred in pred_pip_u:
            if re.search(get_port(pip[1]), pred) and pip[1] != pred:
                TC_nodes = {node for cut in self.CUTs for node in cut.G}
                if pred not in TC_nodes:
                    self.unblock_nodes(device, pred)

    def fill_1(self, dev, queue, coord, TC_idx):
        int_tile = f'INT_{coord}'
        while not self.finish_TC(queue, free_cap=16):
            pip = self.pick_PIP(dev, queue)
            if not pip:
                continue

            self.create_CUT(coord, pip)
            try:
                path_out = path_finder(self.G, pip[1], 't', weight="weight", dummy_nodes=['t'], blocked_nodes=self.block_nodes)
                path_out = Path(dev, self, path_out, 'path_out')
                self.add_path(dev, path_out)
            except:
                self.remove_CUT(dev)
                queue.append(queue.pop(0))
                continue

            self.unblock_nodes(dev, pip[0])
            try:
                path_in = path_finder(self.G, 's', pip[0], weight="weight", dummy_nodes=['s'], blocked_nodes=self.block_nodes)
                path_in = Path(dev, self, path_in, 'path_in')
                self.add_path(dev, path_in)
            except:
                self.block_nodes = pip[0]
                self.remove_CUT(dev)
                queue.append(queue.pop(0))
                continue

            main_path = self.CUTs[-1].main_path.str_nodes()
            if len(main_path) > (GM.pips_length_dict[pip] + 5):
                self.remove_CUT(dev)
                self.G.remove_nodes_from(['s2', 't2'])
                queue.append(queue.pop(0))
                continue

            not_LUT_ins = dev.get_nodes(is_i6=False, clb_node_type='LUT_in', bel=path_in[0].bel, tile=path_in[0].tile)
            for LUT_in in not_LUT_ins:
                #self.G.add_edge(LUT_in.name, 't2', weight=0)
                self.add_edges((LUT_in.name, 't2'), weight=0)

            for node in main_path:
                #self.G.add_edge('s2', node, weight=0)
                self.add_edges(('s2', node), weight=0)

            try:
                not_path = path_finder(self.G, 's2', 't2', weight=dev.weight, dummy_nodes=['s2', 't2'], blocked_nodes=self.block_nodes)
                not_path = Path(dev, self, not_path, 'not')
                self.add_path(dev, not_path)
            except:
                self.remove_CUT(dev)
                self.G.remove_nodes_from(['s2', 't2'])
                queue.append(queue.pop(0))
                continue

            self.G.remove_nodes_from(['s2', 't2'])
            #self.inc_cost(dev, not_path, 1)
            self.finalize_CUT(dev, int_tile)
            queue = [pip for pip in queue if pip not in self.CUTs[-1].covered_pips]

            print(f'TC{TC_idx}- Found Paths: {len(self.CUTs)}')
            print(f'Remaining PIPs: {len(queue)}')

        return queue

    def fill_2(self, dev, queue, coord, TC_idx, c):
        int_tile = f'INT_{coord}'
        out_nodes = {edge[1] for edge in queue}
        '''invalid_out_nodes = set()
        for node in out_nodes:
            in_edges = set(dev.G.in_edges(node))
            if not in_edges & set(queue):
                invalid_out_nodes.add(node)

        out_nodes = out_nodes - invalid_out_nodes'''
        for node in out_nodes:
            self.G.add_edge('out_node', node, weight=0)

        while not self.finish_TC(queue, free_cap=16):
            out_nodes = {edge[1] for edge in queue}
            excess_out_nodes = set(self.G.neighbors('out_node')) - out_nodes
            excess_out_node_edges = set(product({'out_node'}, excess_out_nodes))
            self.G.remove_edges_from(excess_out_node_edges)
            self.create_CUT(coord, None)
            path_out = self.get_path(dev, 'out_node', 't', 'weight', self.block_nodes, 'path_out')
            if not path_out:
                print('-----------------------------------------------------')
                break

            '''try:
                path_out = path_finder(self.G, 'out_node', 't', weight='weight', dummy_nodes=['t', 'out_node'], blocked_nodes=self.block_nodes)
                path_out = Path(dev, self, path_out, 'path_out')
                self.add_path(dev, path_out)
            except:
                self.remove_CUT(dev)
                print('No path_out')
                print('-----------------------------------------------------')
                break'''

            visited_preds = {pip[0] for pip in self.G.in_edges(path_out[0].name) if pip not in queue}
            block_nodes = self.block_nodes.union(visited_preds) - {path_out[0].name}
            temp_path_in = self.get_path(dev, 's', path_out[0].name, 'weight', block_nodes, 'temp_path_in')
            if not temp_path_in:
                self.G.remove_edge('out_node', path_out[0].name)
                continue

            '''try:
                nodes = {pip[0] for pip in self.G.in_edges(path_out[0].name) if pip not in queue}
                temp_path_in = path_finder(self.G, 's', path_out[0].name, weight='weight', dummy_nodes=['s'], blocked_nodes=self.block_nodes.union(nodes) - {path_out[0].name})
            except:
                self.G.remove_edge('out_node', path_out[0].name)
                self.remove_CUT(dev)
                print('No path_in1')
                continue'''

            pip_u = temp_path_in[-2].name
            pip = (pip_u, path_out[0].name)

            #self.decide_route_thrus(dev, pip)
            self.decide_long_pips(dev, pip)

            self.G.remove_edge('out_node', path_out[0].name)
            path_in = self.get_path(dev, 's', pip_u, 'weight', self.block_nodes, 'path_in')
            if not path_in:
                #self.block_nodes = path_out[0].name
                continue

            '''try:
                self.G.remove_edge('out_node', path_out[0].name)   #it is removed in block_nodes
                #self.unblock_nodes(dev, path_out[0].name)
                path_in = path_finder(self.G, 's', pip_u, weight='weight', dummy_nodes=['s'], blocked_nodes=self.block_nodes)
                #self.block_nodes = path_out[0].name
                path_in = Path(dev, self, path_in, 'path_in')
                self.add_path(dev, path_in)
                self.CUTs[-1].pip = dev.get_edges(u=pip[0], v=pip[1]).pop()
            except:
                self.block_nodes = path_out[0].name
                self.remove_CUT(dev)
                print('No path_in2', pip[0])
                continue'''

            self.CUTs[-1].pip = dev.get_edges(u=pip[0], v=pip[1]).pop()
            main_path = self.CUTs[-1].main_path
            if len(main_path) > (GM.pips_length_dict[pip] + 10):
                self.remove_CUT(dev)
                for edge in main_path.edges:
                    self.G.get_edge_data(*edge)['weight'] += 1 / len(main_path)
                self.add_edges(('out_node', path_out[0].name), weight=1)
                print(f'long path => {pip} : {len(main_path) - GM.pips_length_dict[pip]}')
                continue

            if not (set(queue) & self.CUTs[-1].covered_pips):
                self.remove_CUT(dev)
                self.G.get_edge_data(*pip)['weight'] += 30
                self.add_edges(('out_node', path_out[0].name), weight=0)
                print('No new pip', pip)
                continue

            not_LUT_ins = dev.get_nodes(is_i6=False, clb_node_type='LUT_in', bel=path_in[0].bel, tile=path_in[0].tile)
            for LUT_in in not_LUT_ins:
                #self.G.add_edge(LUT_in.name, 't2', weight=0)
                self.add_edges((LUT_in.name, 't2'), weight=0)

            for node in main_path:
                self.G.add_edge('s2', node.name, weight=0)
                #self.add_edges(('s2', node.name), weight=0)

            block_nodes = dev.blocking_nodes(f'INT_{path_in[0].coordinate}').union(self.block_nodes)
            block_nodes = block_nodes - set(main_path.str_nodes())
            not_path = self.get_path(dev, 's2', 't2', dev.weight, block_nodes, 'not')
            if not not_path:
                self.G.remove_nodes_from(['s2', 't2'])
                continue

            '''try:
                blocked_nodes = dev.blocking_nodes(f'INT_{path_in[0].coordinate}').union(self.block_nodes)
                blocked_nodes = blocked_nodes - set(main_path.str_nodes())
                not_path = path_finder(self.G, 's2', 't2', weight=dev.weight, dummy_nodes=['s2', 't2'], blocked_nodes=blocked_nodes)
                not_path = Path(dev, self, not_path, 'not')
                self.add_path(dev, not_path)
            except:
                self.remove_CUT(dev)
                self.G.remove_nodes_from(['s2', 't2'])
                print('No not-path')
                continue'''

            #self.inc_cost(dev, not_path, 1)
            self.G.remove_nodes_from(['s2', 't2'])
            self.finalize_CUT(dev, int_tile)
            l1 = len(queue)
            queue = [pip for pip in queue if pip not in self.CUTs[-1].covered_pips]
            l2 = len(queue)
            if l1 == l2:
                c += 1

            print(f'TC{TC_idx}- Found Paths: {len(self.CUTs)}')
            print(f'Remaining PIPs: {len(queue)}')

        self.G.remove_node('out_node')

        return queue

    def fill_3(self, dev, queue, coord, pbar, TC_idx, c):
        if not self.CUTs and self.block_nodes and coord == 'X46Y90':
            breakpoint()

        int_tile = f'INT_{coord}'
        out_nodes = {edge[1] for edge in queue}
        '''invalid_out_nodes = set()
        for node in out_nodes:
            in_edges = set(dev.G.in_edges(node))
            if not in_edges & set(queue):
                invalid_out_nodes.add(node)

        out_nodes = out_nodes - invalid_out_nodes'''
        for node in out_nodes:
            self.G.add_edge('out_node', node, weight=0)

        #CUT_pbar = trange(16)
        #CUT_pbar.set_description(f'TC{TC_idx}')
        while not self.finish_TC(queue, pbar, free_cap=16):
            out_nodes = {edge[1] for edge in queue}
            excess_out_nodes = set(self.G.neighbors('out_node')) - out_nodes
            excess_out_node_edges = set(product({'out_node'}, excess_out_nodes))
            self.G.remove_edges_from(excess_out_node_edges)
            self.create_CUT(coord, None)
            #main_path, pip = self.negotiate(dev, queue)
            pip = self.get_main_path(dev, queue)
            '''if main_path:
                main_path = Path(dev, self, main_path, 'main_path')
                self.add_path(dev, main_path)
            else:
                self.remove_CUT(dev)
                continue'''
            if not pip:
                continue

            self.CUTs[-1].pip = dev.get_edges(u=pip[0], v=pip[1]).pop()
            main_path = self.CUTs[-1].main_path
            if len(main_path) > (GM.pips_length_dict[pip] + 10):
                self.remove_CUT(dev)
                for edge in main_path.edges:
                    self.G.get_edge_data(*edge)['weight'] += 1 / len(main_path)
                self.add_edges(('out_node', pip[1]), weight=1)
                #print(f'long path => {pip} : {len(main_path) - GM.pips_length_dict[pip]}')
                continue

            if not (set(queue) & self.CUTs[-1].covered_pips):
                self.remove_CUT(dev)
                self.G.get_edge_data(*pip)['weight'] += 30
                self.add_edges(('out_node', pip[1]), weight=0)
                #print('No new pip', pip)
                continue

            not_LUT_ins = dev.get_nodes(is_i6=False, clb_node_type='LUT_in', bel=main_path[0].bel, tile=main_path[0].tile)
            for LUT_in in not_LUT_ins:
                #self.G.add_edge(LUT_in.name, 't2', weight=0)
                self.add_edges((LUT_in.name, 't2'), weight=0)

            for node in main_path:
                if node.clb_node_type == 'LUT_in':
                    continue

                self.G.add_edge('s2', node.name, weight=0)
                #self.add_edges(('s2', node.name), weight=0)

            block_nodes = dev.blocking_nodes(self.CD, f'INT_{main_path[0].coordinate}').union(self.block_nodes) - set(main_path.str_nodes())
            #block_nodes = block_nodes - set(main_path.str_nodes())
            not_path = self.get_path(dev, 's2', 't2', dev.weight, block_nodes, 'not')
            if not not_path:
                self.G.remove_nodes_from(['s2', 't2'])
                continue

            '''try:
                blocked_nodes = dev.blocking_nodes(f'INT_{path_in[0].coordinate}').union(self.block_nodes)
                blocked_nodes = blocked_nodes - set(main_path.str_nodes())
                not_path = path_finder(self.G, 's2', 't2', weight=dev.weight, dummy_nodes=['s2', 't2'], blocked_nodes=blocked_nodes)
                not_path = Path(dev, self, not_path, 'not')
                self.add_path(dev, not_path)
            except:
                self.remove_CUT(dev)
                self.G.remove_nodes_from(['s2', 't2'])
                print('No not-path')
                continue'''

            #self.inc_cost(dev, not_path, 1)
            self.G.remove_nodes_from(['s2', 't2'])
            self.finalize_CUT(dev, int_tile)
            l1 = len(queue)
            queue = [pip for pip in queue if pip not in self.CUTs[-1].covered_pips]
            l2 = len(queue)
            pbar.set_description(f'TC{TC_idx} >> CUT{len(self.CUTs)} >> Remaining PIPs')
            pbar.set_postfix_str('')
            pbar.update(l1 - l2)
            #CUT_pbar.update(16 - len(self.CUTs))
            if l1 == l2:
                c += 1

            #print(f'TC{TC_idx}- Found Paths: {len(self.CUTs)}')
            #print(f'Remaining PIPs: {len(queue)}')

        self.G.remove_node('out_node')

        return queue

    def get_path_cost(self, path):
        weights = {self.G.get_edge_data(*edge)['weight'] for edge in zip(path, path[1:])}

        return sum(weights)

    def get_path(self, dev, source, sink, weight, blocked_nodes, path_type):
        result = True
        try:
            path = path_finder(self.G, source, sink, weight=weight, dummy_nodes=['s', 't', 'out_node', 's2', 't2'],
                               blocked_nodes=blocked_nodes, conflict_free=True)
            path = Path(dev, self, path, path_type)
        except:
            if len(self.CUTs) == 1:
                try:
                    path = path_finder(self.G, source, sink, weight=weight,
                                       dummy_nodes=['s', 't', 'out_node', 's2', 't2'], blocked_nodes=blocked_nodes,
                                       conflict_free=False)
                    path = Path(dev, self, path, path_type)
                    if GM.print_message:
                        print(f'{path_type} Found in Second Run!!!')
                except:
                    self.remove_CUT(dev)
                    result = False
                    path = []
                    if GM.print_message:
                        print(f'No {path_type}!!!')
            else:
                self.remove_CUT(dev)
                result = False
                path = []
                if GM.print_message:
                    print(f'No {path_type}!!!')

        if result and path_type in {'path_out', 'path_in', 'not'}:
            self.add_path(dev, path)

        return path

    def negotiate(self, device, queue):
        G = self.G.copy()
        c = 0
        while 1:
            if c>50:
                return None, None

            c +=1
            p1 = path_finder(G, 'out_node', 't', weight='weight', dummy_nodes=['s', 't', 'out_node', 's2', 't2'],
                             blocked_nodes=self.block_nodes, conflict_free=True)

            node = p1[1]
            visited_preds = {pip[0] for pip in self.G.in_edges(p1[0]) if pip not in queue}
            block_nodes = self.func(device, p1).union(visited_preds) - {node}

            #self.decide_long_pips(dev, pip)
            try:
                p2 = path_finder(G, 's', node, weight='weight', dummy_nodes=['s', 't', 'out_node', 's2', 't2'],
                             blocked_nodes=self.block_nodes.union(block_nodes), conflict_free=True)
                path = p2[1:] + p1[:-1]
                print('**path_found')
                break
            except:
                print('**conflict')
                for edge in zip(p1, p1[1:]):
                    G.get_edge_data(*edge)['weight'] += 1 / len(p1)

        self.G.remove_edge('out_node', node)
        return path, (p2[-2], p1[1])

    def get_global_nodes(self, device, path):
        global_nodes = set()
        for node in path:
            if node.startswith('INT'):
                global_nodes.update(device.get_nodes(port=Node(node).port))
            else:
                global_nodes.update(device.get_nodes(bel_group=Node(node).bel_group, port_suffix=Node(node).port_suffix))

        return {node.name for node in global_nodes}

    def get_main_path(self, device, queue):
        try:
            path_out1 = path_finder(self.G, 'out_node', 't', weight='weight', dummy_nodes=['s', 't', 'out_node', 's2', 't2'],
                        blocked_nodes=self.block_nodes, conflict_free=False)[1:-1]
        except:
            self.remove_CUT(device)
            return  None

        visited_preds = {pip[0] for pip in self.G.in_edges(path_out1[0]) if pip not in queue}
        try:
            #bidirectional pips could be problematic, so add set(self.G.neighbors(path_out1[0])) to block_nodes
            block_nodes = self.block_nodes.union(visited_preds).union(set(self.G.neighbors(path_out1[0])))
            path_in1 = path_finder(self.G, 's', path_out1[0], weight='weight', dummy_nodes=['s', 't', 'out_node', 's2', 't2'],
                               blocked_nodes=block_nodes, conflict_free=False)[1:]
        except:
            self.G.remove_edge('out_node', path_out1[0])
            self.remove_CUT(device)
            return  None

        pip = tuple(path_in1[-2:])
        neigh_pip_v = list(self.G.neighbors(pip[1]))[0]
        pred_pip_u = list(self.G.predecessors(pip[0]))[0]
        route_thru_flag = bool(re.match(GM.Unregistered_CLB_out_pattern, pred_pip_u)) or bool(re.match(GM.LUT_in_pattern, neigh_pip_v))
        self.G.remove_edge('out_node', pip[1])

        if len(path_out1) < len(path_in1):
            path_out = self.get_path(device, pip[1], 't', 'weight', self.block_nodes, 'path_out')
            if not path_out:
                return  None

            self.decide_long_pips(device, pip)
            if re.match(GM.LUT_in6_pattern, neigh_pip_v):
                src = {node.name for node in device.get_nodes(clb_node_type='FF_out', bel_group=Node(neigh_pip_v).bel_group, bel=neigh_pip_v[-2])}
                block_nodes = self.block_nodes.union(src)
            else:
                block_nodes = self.block_nodes
                if route_thru_flag:
                    clb_node = Node(neigh_pip_v) if neigh_pip_v.startswith('CLE') else Node(pred_pip_u)
                    forbiden_srcs = {node for node in self.G.neighbors('s')
                                     if get_tile(node) == clb_node.tile and Node(node).bel == clb_node.bel}
                    block_nodes = block_nodes.union(forbiden_srcs)

            path_in = self.get_path(device, 's', pip[0], 'weight', block_nodes, 'path_in')
            if not path_in:
                unblock_nodes = set(path_in1[:-1]) & self.get_global_nodes(device, path_out.str_nodes())
                if not unblock_nodes & set(path_out.str_nodes()):
                    coord = get_tile(pip[0]).split('_X')[-1]
                    self.create_CUT(coord, None)
                    self.add_path(device, path_out)
                    path_in = self.get_path(device, 's', pip[0], 'weight', block_nodes - unblock_nodes, 'path_in')
                    if not path_in:
                        return  None
                else:
                    return  None
        else:
            if re.match(GM.LUT_in6_pattern, neigh_pip_v):
                src = {node.name for node in device.get_nodes(clb_node_type='FF_out', bel_group=Node(neigh_pip_v).bel_group, bel=neigh_pip_v[-2])}
                block_nodes = self.block_nodes.union(src)
            else:
                block_nodes = self.block_nodes

            if route_thru_flag:
                clb_node = Node(neigh_pip_v) if neigh_pip_v.startswith('CLE') else Node(pred_pip_u)
                forbiden_srcs = {node for node in self.G.neighbors('s')
                                 if get_tile(node) == clb_node.tile and Node(node).bel == clb_node.bel}
                block_nodes = block_nodes.union(forbiden_srcs)

            path_in = self.get_path(device, 's', pip[0], 'weight', block_nodes, 'path_in')
            if not path_in:
                return  None

            self.decide_long_pips(device, pip)
            path_out = self.get_path(device, pip[1], 't', 'weight', self.block_nodes, 'path_out')
            if not path_out:
                unblock_nodes = set(path_out1) & self.get_global_nodes(device, path_in.str_nodes())
                if not unblock_nodes & set(path_in.str_nodes()):
                    coord = get_tile(pip[0]).split('_X')[-1]
                    self.create_CUT(coord, None)
                    self.add_path(device, path_in)
                    path_out = self.get_path(device, pip[1], 't', 'weight', self.block_nodes - unblock_nodes, 'path_out')
                    if not path_out:
                        return  None
                else:
                    return  None


        return pip