import time, re, os, pickle
from Functions import *
import networkx as nx
from resources.node import *
from resources.tile import *
from resources.arch_graph import Arch
from itertools import product

start_time = time.time()
coord = 'X46Y90'
#################################################
with open(r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\Compressed Graphs\G_ZU9_INT_X46Y90.data', 'rb') as data:
    G = pickle.load(data)
dev = Arch(G)
#dev.set_wires_dict(G, coord)
#################################################
int_tile = dev.get_tiles(type='INT', coordinate=coord).pop()
pip_paths_dict = {}
pip_mid_dict = {}
FF_outs = dev.get_clb_nodes('FF_out')
FF_ins = dev.get_clb_nodes('FF_in')
configurations = {('W_B', 'E_T'), ('W_B', 'E_B'), ('W_T', 'E_T'), ('W_T', 'E_B')}
for conf_idx, configuration in enumerate(configurations):
    sources = set(filter(lambda x: x.bel_group in configuration, FF_outs))
    sinks = set(filter(lambda x: x.bel_group not in configuration, FF_ins))

    for source in sources:
        G.add_edge('s', source.name, weight=0)

    for sink in sinks:
        G.add_edge(sink.name, 't', weight=0)

    for idx, pip in enumerate(int_tile.pips):
        print(f'{conf_idx + 1}- {idx}')
        if not nx.has_path(G, 's', pip[0]) or not nx.has_path(G, pip[1], 't'):
            continue

        s_paths = list(nx.all_shortest_paths(G, 's', pip[0], weight='weight'))
        t_paths = list(nx.all_shortest_paths(G, pip[1], 't', weight='weight'))
        s_paths = [path[1:] for path in s_paths]
        t_paths = [path[:-1] for path in t_paths]
        paths = list(product(s_paths, t_paths))
        paths = [path[0] + path[1] for path in paths]
        pip_paths_dict[pip] = paths
        extend_dict(pip_paths_dict, pip, paths, extend=True)

    G.remove_nodes_from(['s', 't'])


G1 = nx.DiGraph()
for pip in pip_paths_dict:
    for path in pip_paths_dict[pip]:
        G1.add_edges_from(zip(path, path[1:]))

with open('G1.data', 'wb') as data:
    pickle.dump(G1, data)

print('--- %s seconds ---' %(time.time() - start_time))