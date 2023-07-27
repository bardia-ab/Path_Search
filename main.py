import time, re, os
from Functions import *
import networkx as nx
from resources.node import *
from resources.tile import *
from resources.arch_graph import Arch

start_time = time.time()
coord = 'X46Y90'
#################################################
G = get_coord_graph(coord)
dev = Arch(G)
dev.set_wires_dict(G, coord)
G = rmv_off_wires(G, coord)
#################################################
int_tile = dev.get_tiles(type='INT', coordinate=coord).pop()
mid_back = dev.set_level(G, coord)

'''mid_nodes = int_tile.get_nodes(G, 'mid')
mid_nodes_hirch = {}
level = 0
covered_inputs = set()
covered_outputs = set()
while mid_nodes:
    level += 1
    removed = set()
    for node in mid_nodes:
        neighs = set(G.neighbors(node.name))
        preds = set(G.predecessors(node.name))
        neigh_modes = {Node(neigh).get_INT_node_mode(G) for neigh in neighs}
        if 'out' in neigh_modes:
            removed.add(node)
            mid_nodes_hirch[node] = level

        for neigh in neighs:
            if Node(neigh).get_INT_node_mode(G) == 'out':
                covered_outputs.add(neigh)

        for pred in preds:
            if Node(pred).get_INT_node_mode(G) == 'in':
                covered_inputs.add(pred)

    mid_nodes = mid_nodes - removed
    break

remaining_inputs = set()
for node in int_tile.get_nodes(G, 'in'):
    if node.name not in covered_inputs:
        remaining_inputs.add(node.name)

remaining_outputs = set()
for node in int_tile.get_nodes(G, 'out'):
    if node.name not in covered_outputs:
        remaining_outputs.add(node.name)'''
'''
in_nodes_paths = {}     #in_node:[path1, path2, ...]
out_nodes_paths = {}    #out_node: [path1, path2, ...]
in_nodes_sinks = {}     #in_node: {sink1, sink2, ...}
out_nodes_sources = {}  #out_node: {source1, source2, ...}

sinks = dev.get_nodes(tile=int_tile.name, mode='out')
for sink in sinks:
    G.add_edge(sink.name, 't', weight=0)

sources = dev.get_nodes(tile=int_tile.name, mode='in')
for i, in_node in enumerate(sources):
    source = in_node.name
    for sink in sinks:
        if nx.has_path(G, source, sink.name):
            extend_dict(in_nodes_sinks, source, sink.name, value_type='set')
            extend_dict(out_nodes_sources, sink.name, source, value_type='set')

    print(f'{i + 1}: {in_node}\t{len(in_nodes_sinks[source])}')'''

'''for i, in_node in enumerate(int_tile.get_nodes(G, 'in')):
    source = in_node.name
    paths = list(nx.all_shortest_paths(G, source, 't', weight='weight'))
    #paths = list(nx.all_simple_paths(G, source, 't'))
    for path in paths:
        extend_dict(in_nodes_paths, source, path[:-1])
        extend_dict(in_nodes_sinks, source, path[-2], value_type='set')
        extend_dict(out_nodes_paths, path[-2], path[:-1])
        extend_dict(out_nodes_sources, path[-2], path[0], value_type='set')

    print(f'{i + 1}: {in_node}\t=>{len(paths)}')'''

direct_pips = set()
for pip in int_tile.pips:
    if dev.get_nodes(name=pip[0], mode='in') and dev.get_nodes(name=pip[1], mode='out'):
        direct_pips.add(pip)

l1 = dev.get_nodes(coordinate=coord, tile_type = 'INT', level=1)
l2_mid = dev.get_nodes(coordinate=coord, tile_type = 'INT', level=2, mode='mid')
l2_out = dev.get_nodes(coordinate=coord, tile_type = 'INT', level=2, mode='out')
l3_mid = dev.get_nodes(coordinate=coord, tile_type = 'INT', level=3, mode='mid')
l3_out = dev.get_nodes(coordinate=coord, tile_type = 'INT', level=3, mode='out')

pips1 = set()
pips2 = set()
pips3 = set()
for pip in int_tile.pips:
    if dev.get_nodes(name=pip[0], level=1) and dev.get_nodes(name=pip[1], level=2):
        pips1.add(pip)
    elif dev.get_nodes(name=pip[0], level=2, mode='mid') and dev.get_nodes(name=pip[1], level=3, mode='out'):
        pips1.add(pip)
    elif dev.get_nodes(name=pip[0], level=2) and dev.get_nodes(name=pip[1], level=2):
        pips2.add(pip)
    elif dev.get_nodes(name=pip[0], mode='out') and dev.get_nodes(name=pip[1], mode='out'):
        pips3.add(pip)

G1 = G.copy()
pips = int_tile.pips
G1.remove_edges_from(pips - pips1)
clb = dev.get_tiles(coordinate=coord, direction='W').pop()
sources = clb.get_clb_nodes('FF_out')
sinks = clb.get_clb_nodes('FF_in')

for source in sources:
    G1.add_edge('s', source.name, weight=0)

for sink in sinks:
    G1.add_edge(sink.name, 't', weight=0)

for source in sources:
    G.add_edge('s', source.name, weight=0)

for sink in sinks:
    G.add_edge(sink.name, 't', weight=0)

edges = set()
while 1:
    rem_edges = set()
    paths = list(nx.node_disjoint_paths(G, 's', 't'))
    for path in paths:
        path = path[1:-1]
        for edge in zip(path, path[1:]):
            if get_tile(edge[0]) == get_tile(edge[1]) == f'INT_{coord}':
                if dev.get_nodes(name=edge[0], mode='mid') and dev.get_nodes(name=edge[1], mode='out'):
                    rem_edges.add(edge)

                edges.add(edge)
                #G.get_edge_data(*edge)['weight'] += 1e6

    G.remove_edges_from(rem_edges)
    if not nx.has_path(G, 's', 't'):
        break


print('--- %s seconds ---' %(time.time() - start_time))