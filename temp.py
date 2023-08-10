import time, re, os, pickle

import Global_Module
from Functions import *
import networkx as nx
from resources.node import *
from resources.tile import *
from resources.edge import *
from resources.path import *
from resources.cut import *
from resources.primitive import *
from resources.configuration import *
from resources.arch_graph import Arch
import resources.validation as vd
from itertools import product
from tqdm import tqdm, trange

start_time = time.time()
coord = 'X46Y90'
if coord == 'X46Y90':
    GM.store_path = os.path.join(GM.store_path, 'iter1')
    create_folder(GM.store_path)
else:
    l = len(os.listdir(GM.store_path))
    GM.store_path = os.path.join(GM.store_path, f'iter{l}')
    create_folder(GM.store_path)
#################################################
graph_path = os.path.join(GM.graph_path, f'G_ZU9_INT_{coord}.data')
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')

dev = Arch(G)
dev.get_pips_length(coord)
queue = list(GM.pips_length_dict)
del G
#queue = load_data(GM.Data_path, 'remaining_pips.data')
#spare_pips = load_data(GM.Data_path, 'spare_pips.data')
#long_pips = queue - spare_pips
#################################################
#create_folder(GM.store_path)
int_tile = dev.get_tiles(type='INT', coordinate=coord).pop()
l_queue = len(queue)
#GM.nodes_dict = get_nodes_dict(dev.G, coord)
#queue = list(int_tile.pips)
#queue = remove_no_path_pips(dev.G, queue, coord)

TC_idx = 0
#TC_idx=119
c = 0
pbar = trange(l_queue)

while queue:
    TC = Configuration(dev)
    TC.remove_route_thrus(coord)
    queue = TC.sort_pips(queue)
    #queue = TC.fill_1(dev, queue, coord, TC_idx)
    '''if TC_idx == 163:
        TC = load_data(os.path.join(GM.store_path, 'iter1'), f'TC{TC_idx}.data')
        TC.start_TC_time = time.time()
        #TC.CD = {'W_T': None, 'W_B': None, 'E_T': None, 'E_B': None}
        dev.G = TC.G_dev.copy()
        queue = TC.queue
        edges = {edge for edge in dev.G.edges() if get_tile(edge[0]) == get_tile(edge[1]) == 'INT_X46Y90'}
        other_edges = set(dev.G.edges()) - edges
        for edge in other_edges:
            dev.G.get_edge_data(*edge)['weight'] = 1'''

    queue = TC.fill_3(dev, queue, coord, pbar, TC_idx, c)

    if (l_queue - len(queue)) > 1500:
        l_queue = len(queue)
        for edge in dev.G.edges():
            dev.G.get_edge_data(*edge)['weight'] = 1

    TC.queue = queue.copy()
    TC.G_dev = dev.G
    store_data(GM.store_path, f'TC{TC_idx}.data', TC)

    if TC.CUTs:
        vd.check_LUT_utel(TC)
        TC_idx += 1
    else:
        break

print('Paths with no new PIPs: ', c)
store_data(GM.Data_path, 'remaining_pips.data', queue)
print('--- %s seconds ---' %(time.time() - start_time))