import networkx as nx

from resources.cut import CUT
from resources.node import Node
from resources.path import Path
from Functions import *
from itertools import product
import Global_Module as GM
import copy, time

class Configuration():

    def __init__(self, device):
        self.G                      = copy.deepcopy(device.G)
        self.G_TC                   = nx.DiGraph()
        self.FFs                    = device.gen_FFs()
        self.LUTs                   = device.gen_LUTs()
        self._block_nodes           = set()
        self.CD                     = {'W_T': None, 'W_B': None, 'E_T': None, 'E_B': None}
        self.CUTs                   = []
        self.tried_pips             = set()
        self.route_thrus            = {}
        self.start_TC_time          = time.time()
        self.long_TC_process_time   = 120
        self.assign_source_sink()

    @property
    def block_nodes(self):
        return self._block_nodes

    @block_nodes.setter
    def block_nodes(self, nodes):
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

    def block_path(self, device, path):
        #nodes = [node for node in path if node.primitive != 'LUT']
        self.block_nodes = path
        global_nodes = set()
        for node in path:
            if node.tile_type == 'INT':
                global_nodes.update(device.get_nodes(port=node.port))
            else:
                global_nodes.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))

        global_nodes = global_nodes - set(path)
        if GM.block_mode == 'global':
            self.block_nodes = global_nodes
        else:
            self.penalize_nodes(global_nodes)

    def unblock_nodes(self, device, nodes):
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
        FFs = set()
        for FF in self.FFs:
            for attr in attributes:
                if getattr(FF, attr) != attributes[attr]:
                    break
            else:
                FFs.add(FF)

        return FFs

    def get_LUTs(self, **attributes):
        LUTs = set()
        for LUT in self.LUTs:
            for attr in attributes:
                if getattr(LUT, attr) != attributes[attr]:
                    break
            else:
                LUTs.add(LUT)

        return LUTs

    def create_CUT(self, coord, pip):
        cut = CUT(coord, pip=pip)
        self.CUTs.append(cut)
        self.block_nodes = pip

    def add_path(self, device, path):
        cut = self.CUTs[-1]
        cut.paths.add(path)
        #for edge in path.edges:
            #self.add_edge_CUT(device, edge)
        self.block_path(device, path)

        #extract FFs & LUTs in G
        FFs_set         = path.FFs().copy()
        LUTs_func_dict  = path.LUTs_dict().copy()
        cut.FFs_set.update(FFs_set)
        cut.LUTs_func_dict.update(LUTs_func_dict)
        # set their usage
        if GM.block_mode == 'global':
           FFs_set = self.get_global_FFs(device, FFs_set)
           LUTs_func_dict = self.get_global_LUTs(device, LUTs_func_dict)

        self.update_FFs('used', FFs_set)
        self.set_LUTs(device, 'used', LUTs_func_dict)
        self.set_CDs(device, path)
        self.block_source_sink(device, path)

    def remove_CUT(self, device):
        cut = self.CUTs[-1]
        #self.unblock_nodes(device, cut.nodes)

#        global_nodes = set()
        for path in cut.paths:
            global_nodes = set()
            self.unblock_nodes(device, path.nodes)
            self.reset_CDs(device, path)
            for node in path:
                if node.tile_type == 'INT':
                    global_nodes.update(device.get_nodes(port=node.port))
                else:
                    global_nodes.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))

            global_nodes = global_nodes - set(path)
            if GM.block_mode == 'global':
                self.unblock_nodes(device, global_nodes)
            else:
                self.relax_nodes(global_nodes)

            self.unblock_source_sink(device, path)


        #reset primitive usage
        if GM.block_mode == 'global':
            FFs_set = self.get_global_FFs(device, cut.FFs_set)
            LUTs_func_dict = self.get_global_LUTs(device, cut.LUTs_func_dict)
        else:
            FFs_set = cut.FFs_set.copy()
            LUTs_func_dict = cut.LUTs_func_dict.copy()

        self.update_FFs('free', FFs_set)
        self.reset_LUTs(device, LUTs_func_dict)

        self.CUTs.remove(cut)

    def finalize_CUT(self, device):
        cut = self.CUTs[-1]
        self.G_TC = nx.compose(self.G_TC, cut.G)
        if not nx.is_forest(self.G_TC):
            breakpoint()

        self.update_FFs('blocked', cut.FFs_set)
        self.set_LUTs(device, 'blocked', cut.LUTs_func_dict)
        #increase cost
        self.inc_cost(device)
        self.remove_LUT_occupied_sources(device)

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
        for node in LUTs_func_dict:
            LUT_primitives = self.get_subLUT(usage, node, next_iter_initalization)
            if not LUT_primitives:
                continue

            for LUT_primitive in LUT_primitives:
                LUT_primitive.inputs = node.name
                LUT_primitive.func   = LUTs_func_dict[node]
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
        for node in LUTs_func_dict:
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
                if i6_node != freed_LUT_ins:    #both subLUTs are used and i5 for 5LUT is added as the input
                    self.unblock_nodes(device, i6_node)

                ###unblock freed LUTs
                #freed_LUT_ins = {node for LUT_in in freed_LUT_ins for node in device.get_nodes(name=LUT_in)}
                #self.unblock_nodes(device, freed_LUT_ins)

            if full_LUT:
                ### unblock the other LUT's inputs
                used_LUT_in = {inp for prim in LUT_primitives if prim.inputs for inp in prim.inputs}
                free_LUT_in = device.get_nodes(is_i6=False, bel=node.bel, tile=node.tile, primitive=node.primitive) - used_LUT_in
                free_LUT_in = free_LUT_in - freed_LUT_ins
                self.unblock_nodes(device, free_LUT_in)

    def get_subLUT(self, usage, node, next_iter_initalization=False):
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
        elif not GM.LUT_Dual:
            return LUT_primitives
        elif LUT_primitives:
            return LUT_primitives[:1]
        else:
            return []

    def is_LUT_full(self, LUT_primitive):
        full = True
        LUTs = self.get_LUTs(tile=LUT_primitive.tile, letter=LUT_primitive.letter)
        for lut in LUTs:
            if lut.usage == 'free':
                full = False
                break

        return full

    def is_LUT_free(self, LUT_primitive):
        free = True
        LUTs = self.get_LUTs(tile=LUT_primitive.tile, letter=LUT_primitive.letter)
        for lut in LUTs:
            if lut.usage != 'free':
                free = False
                break

        return free

    def get_global_FFs(self, device, FFs_set):
        global_FFs = set()
        for node in FFs_set:
            global_FFs.update(device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix))

        return global_FFs

    def get_global_LUTs(self, device, LUTs_func_dict):
        global_LUTs_func_dict = {}
        for node in LUTs_func_dict:
            global_LUTs = device.get_nodes(bel_group=node.bel_group, port_suffix=node.port_suffix)
            for LUT_in in global_LUTs:
                global_LUTs_func_dict[LUT_in] = LUTs_func_dict[node]

        return global_LUTs_func_dict

    def inc_cost(self, device):
        cut = self.CUTs[-1]
        paths = {path for path in cut.paths if path.path_type in {'path_in', 'path_out', 'main_path'}}
        for path in paths:
            for pip in path.pips:
                device.G.get_edge_data(*pip)['weight'] += 3

    def pick_PIP(self, queue):
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

            if re.match(GM.LUT_in_pattern, pip[1]):
                if self.route_thrus:
                    self.restore_route_thrus()
            else:
                if not self.route_thrus:
                    self.remove_route_thrus()

            break
        else:
            pip = None

        return pip

    def sort_pips2(self, pips):
        pips_dict = get_pips_dict(GM.nodes_dict, pips)

        return sorted(pips, key=pips_dict.get, reverse=True)

    def sort_pips(self, pips):
        return sorted(pips, key=lambda x: GM.pips_length_dict[x], reverse=True)

    def finish_TC(self, queue, free_cap=8):
        #capacity = free_cap - len(self.CUTs)
        cond2 = time.time() - self.start_TC_time > self.long_TC_process_time
        cond3 = not queue
        try:
            cond4 = nx.has_path(self.G, 's', 't')
        except nx.exception.NodeNotFound:
            cond4 = False

        if cond2:
            #print('Long TC Process Time!!!')
            return True
        elif cond3:
            #print('Queue is empty!!!')
            return True
        elif not cond4:
            #print('No path between sourse and sink!!!')
            return True
        else:
            return False

    def assign_source_sink(self):
        self.G.remove_nodes_from(['s', 't'])
        Sources = list(filter(GM.Source_pattern.match, self.G))
        Sinks = list(filter(GM.Sink_pattern.match, self.G))

        edges = set(product({'s'}, Sources))
        self.G.add_edges_from(edges, weight=0)
        edges = set(product(Sinks, {'t'}))
        self.G.add_edges_from(edges, weight=0)

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
                self.G.add_edges_from(edges, weight=0)

            if node_type == 'sink':
                sink = [node for node in path if node.clb_node_type == 'FF_in']
                if GM.block_mode == 'global':
                    sinks = device.get_nodes(bel_group=sink[0].bel_group, port_suffix=sink[0].port_suffix)
                    # sinks.update(device.get_nodes(bel_group=sink[0].bel_group, bel=sink[0], clb_node_type='LUT_in'))
                else:
                    sinks = sink

                sinks = {node.name for node in sinks}
                edges = set(product(sinks, {'t'}))
                self.G.add_edges_from(edges, weight=0)

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
            other_group = other_group_dict[group]
            function = clock_groups[path.path_type][0]
            other_function = other_function_dict[function]
            if self.CD[group] is None:
                self.CD[group] = function
                self.CD[other_group] = other_function
                self.remove_source_sink(device, group, function)
                self.remove_source_sink(device, other_group, other_function)

            else:
                if self.CD[group] != clock_groups[path.path_type][0]:
                    breakpoint()
                    raise ValueError (f"Conflict in Clock Group {group}: {clock_groups[path.path_type][0]} group")

        if clock_groups[path.path_type][1]:
            group = path[-1].bel_group
            other_group = other_group_dict[group]
            function = clock_groups[path.path_type][1]
            other_function = other_function_dict[function]
            if not self.CD[group]:
                self.CD[group] = function
                self.CD[other_group] = other_function
                self.remove_source_sink(device, group, function)
                self.remove_source_sink(device, other_group, other_function)

            else:
                if self.CD[group] != clock_groups[path.path_type][1]:
                    breakpoint()
                    raise f"Conflict in Clock Group {group}: {clock_groups[path.path_type][1]} group"

    def remove_source_sink(self, device, group, function):
        if function == 'launch':
            FFs_in = set()
            LUTs_in = set()
            FFs_in.update(device.get_nodes(bel_group=group, clb_node_type='FF_in'))
            FFs_in = {FF_in.name for FF_in in FFs_in}
            LUTs_in.update(device.get_nodes(bel_group=group, clb_node_type='LUT_in'))
            LUTs_in = {LUT_in.name for LUT_in in LUTs_in}

            removed_edges = set(product(FFs_in, {'t'}))
            removed_edges.update(set(product(LUTs_in, {'t'})))
            added_edges = set(product(FFs_in, {f't_{group}'}))
            added_edges.update(set(product(LUTs_in, {f't_{group}'})))
        elif function == 'sample':
            FFs_out = set()
            FFs_out.update(device.get_nodes(bel_group=group, clb_node_type='FF_out'))
            FFs_out = {FF_out.name for FF_out in FFs_out}

            removed_edges = set(product({'s'}, FFs_out))
            added_edges = set(product({f's_{group}'}, FFs_out))
        else:
            removed_edges = []
            added_edges = []

        self.G.remove_edges_from(removed_edges)
        self.G.add_edges_from(added_edges, weight=0)

    def remove_LUT_occupied_sources(self, device):
        launch_groups = {group for group in self.CD if self.CD[group] == 'launch'}
        occupied_LUTs = set()
        for group in launch_groups:
            occupied_LUTs.update((LUT_primitive.tile, LUT_primitive.letter) for LUT_primitive in self.get_LUTs(usage='used', bel_group=group))

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
        #self.add_edges(*added_edges)
        self.G.add_edges_from(added_edges, weight=0)

    def remove_route_thrus(self):
        LUT_ins = list(filter(lambda x: re.match(GM.LUT_in_pattern, x), self.G))
        removed_edges = set()
        for LUT_in in LUT_ins:
            for edge in self.G.out_edges(LUT_in):
                self.route_thrus[edge] = self.G.get_edge_data(*edge)['weight']
                removed_edges.add(edge)

        self.G.remove_edges_from(removed_edges)

    def restore_route_thrus(self):
        for edge in self.route_thrus:
            if not set(edge) & self._block_nodes:
                self.G.add_edge(*edge, weight=self.route_thrus[edge])

    def fill_1(self, dev, queue, coord, TC_idx):
        while not self.finish_TC(queue, free_cap=16):
            pip = self.pick_PIP(queue)
            if not pip:
                continue

            self.create_CUT(coord, pip)
            try:
                path = path_finder(self.G, pip[1], 't', weight="weight", dummy_nodes=['t'])
                path1 = Path(dev, self, path, 'path_out')
                self.add_path(dev, path1)
            except:
                self.remove_CUT(dev)
                queue.append(queue.pop(0))
                continue

            self.unblock_nodes(dev, pip[0])
            try:
                path = path_finder(self.G, 's', pip[0], weight="weight", dummy_nodes=['s'])
                path1 = Path(dev, self, path, 'path_in')
                self.add_path(dev, path1)
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

            not_LUT_ins = dev.get_nodes(is_i6=False, clb_node_type='LUT_in', bel=path1[0].bel, tile=path1[0].tile)
            for LUT_in in not_LUT_ins:
                self.G.add_edge(LUT_in.name, 't2', weight=0)

            for node in main_path:
                self.G.add_edge('s2', node, weight=0)

            try:
                path = path_finder(self.G, 's2', 't2', weight="weight", dummy_nodes=['s2', 't2'])
                path1 = Path(dev, self, path, 'not')
                self.add_path(dev, path1)
            except:
                self.remove_CUT(dev)
                self.G.remove_nodes_from(['s2', 't2'])
                queue.append(queue.pop(0))
                continue

            self.G.remove_nodes_from(['s2', 't2'])
            self.finalize_CUT(dev)
            queue = [pip for pip in queue if pip not in self.CUTs[-1].covered_pips]
            print(f'TC{TC_idx}- Found Paths: {len(self.CUTs)}')
            print(f'Remaining PIPs: {len(queue)}')