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
import resources.reconstruction as recon
from tqdm import tqdm, trange

start_time = time.time()
coord = sys.argv[1]
#coord = 'X22Y310'
tile = f'INT_{coord}'
l = 1 if coord == 'X28Y329' else len(os.listdir(GM.store_path)) + 1
store_path = os.path.join(GM.store_path, f'iter{l}')
create_folder(store_path)
#################################################
graph_path = os.path.join(GM.graph_path, f'G_ZU9_INT_{coord}.data')
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')

dev = Arch(G)
dev.get_pips_length(coord)
del G
queue = dev.reconstruct_device(l, coord)
#################################################
l_queue = len(queue)
c = 0
N_TC = 0
pbar = tqdm(total=l_queue)
if l > 1:
    files, last_TC = recon.sort_TCs(l, coord)

    for file in files:
        if not queue:
            break

        TC_idx = int(re.search('\d+', file)[0])
        TC_total = load_data(os.path.join(GM.DLOC_path, f'iter{l - 1}'), f'TC{TC_idx}.data')
        TC = Configuration(dev, TC_total)

        TC.remove_route_thrus(coord)

        queue = TC.fill_3(dev, queue, coord, pbar, N_TC, c)

        TC.queue = queue.copy()
        TC.G_dev = dev.G.copy()
        #store_data(store_path, f'TC{TC_idx}.data', TC)
        N_TC += 1
        if TC.CUTs:
            vd.check_LUT_utel(TC)
            store_data(store_path, f'TC{TC_idx}.data', TC)

    TC_idx = len(files)
else:
    TC_idx = 0

while queue:
    TC = Configuration(dev)
    TC.remove_route_thrus(coord)

    '''if TC_idx == 0:
        TC = load_data(os.path.join(GM.store_path, 'iter1'), f'TC{TC_idx}.data')
        #TC.CD = {'W_T': None, 'W_B': None, 'E_T': None, 'E_B': None}
        dev.G = TC.G_dev.copy()
        queue = TC.queue
        TC._block_nodes = set()
        TC.start_TC_time = time.time()
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
    TC.G_dev = dev.G.copy()
    #store_data(store_path, f'TC{TC_idx}.data', TC)

    if TC.CUTs:
        vd.check_LUT_utel(TC)
        store_data(store_path, f'TC{TC_idx}.data', TC)
        TC_idx += 1
    else:
        break

print('Paths with no new PIPs: ', c)
store_data(GM.Data_path, 'remaining_pips.data', queue)
print('\n--- %s seconds ---' %(time.time() - start_time))