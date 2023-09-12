import time, re, os, pickle

import Global_Module
from Functions import *
import networkx as nx
from resources.node import *
from resources.configuration import *
from resources.arch_graph import Arch
from resources.lut import LUT
import concurrent.futures
from pympler import asizeof

start_time = time.time()
#coord = sys.argv[1]
coord = 'X46Y90'
tile = f'INT_{coord}'
l = 1 if coord == 'X46Y90' else len(os.listdir(GM.store_path)) + 1
################
graph_path = os.path.join(GM.graph_path, f'G_ZU9_INT_{coord}.data')
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')

'''dev = Arch(G)
dev.get_pips_length(coord)
del G
queue = dev.reconstruct_device(l, coord)'''

'''lut1 = LUT('CLEM_X46Y90/A6LUT')
lut1.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A1')
lut1.func = 'buffer'
lut2 = LUT('CLEM_X46Y90/A5LUT')
lut2.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A2')
lut2.func = 'not'
lut2.cal_init()

a = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_AMUX')
lut2.output = a

lut3 = LUT('CLEM_X46Y90/A6LUT')
lut3.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A1')
lut3.func = 'buffer'
lut4 = LUT('CLEM_X46Y90/A5LUT')
lut4.inputs = Node('CLEM_X46Y90/CLE_CLE_M_SITE_0_A2')
lut4.func = 'not'
'''

G1 = nx.DiGraph()
for edge in G.edges:
    weight = G.get_edge_data(*edge)['weight']
    G1.add_edge(Node(edge[0]), Node(edge[1]), weight=weight)

print(asizeof.asizeof(G))
print(asizeof.asizeof(G1))

t1 = time.time()
srcs = set(filter(lambda x: re.match(GM.FF_out_pattern, x), G))
sinks = set(filter(lambda x: re.match(GM.FF_in_pattern, x), G))
for src in srcs:
    G.add_edge('s', src, weight=0)

for sink in sinks:
    G.add_edge(sink, 't', weight=0)

int_nodes = filter(lambda x: x.startswith('INT_X46Y90'), G)


paths = []
for idx, node in enumerate(int_nodes):
    #print(f'{idx}- {node}')
    try:
        paths.append(nx.shortest_path(G, 's', node, weight='weight'))
    except:
        pass

    try:
        paths.append(nx.shortest_path(G, node, 't', weight='weight'))
    except:
        pass

t2 = time.time()
print(t2 - t1)
#############################################
t1 = time.time()
srcs = set(filter(lambda x: x.clb_node_type == 'FF_out', G1))
sinks = set(filter(lambda x: x.clb_node_type == 'FF_in', G1))
s = Node('s')
t = Node('t')
for src in srcs:
    G1.add_edge(s, src, weight=0)

for sink in sinks:
    G1.add_edge(sink, t, weight=0)

int_nodes = filter(lambda x: x.tile == 'INT_X46Y90', G1)

paths1 = []
for idx, node in enumerate(int_nodes):
   #print(f'{idx}- {node}')
    try:
        paths1.append(nx.shortest_path(G1, s, node, weight='weight'))
    except:
        pass

    try:
        paths1.append(nx.shortest_path(G1, node, t, weight='weight'))
    except:
        pass

t2 = time.time()
print(t2 - t1)

print(asizeof.asizeof(paths))
print(asizeof.asizeof(paths1))

print('\n--- %s seconds ---' %(time.time() - start_time))