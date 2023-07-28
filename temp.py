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

start_time = time.time()
coord = 'X46Y90'
#################################################
graph_path = os.path.join(GM.graph_path, 'G_ZU9_INT_X46Y90.data')
with open(graph_path, 'rb') as data:
    G = pickle.load(data)
G = Arch.remove_FF_PIPs(G)
dev = Arch(G)
#################################################
create_folder(GM.store_path)
int_tile = dev.get_tiles(type='INT', coordinate=coord).pop()

GM.nodes_dict = get_nodes_dict(dev.G, coord)
#queue = list(int_tile.pips)
#queue = remove_no_path_pips(dev.G, queue, coord)
dev.get_pips_length(coord)
queue = list(GM.pips_length_dict)
TC_idx = 0
while queue:
    TC = Configuration(dev)
    queue = TC.sort_pips(queue)
    TC.fill_1(dev, queue, coord, TC_idx)

    if TC.CUTs:
        vd.check_LUT_utel(TC)
        store_data(GM.store_path, f'TC{TC_idx}.data', TC)
        TC_idx += 1
    else:
        break

print('--- %s seconds ---' %(time.time() - start_time))