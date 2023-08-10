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
from joblib import Parallel, delayed

start_time = time.time()
coord = 'X45Y90'
tile = f'INT_{coord}'
l = 1 if coord == 'X46Y90' else len(os.listdir(GM.store_path)) + 1
store_path = os.path.join(GM.store_path, f'iter{l}')
#create_folder(GM.store_path)
#################################################
graph_path = os.path.join(GM.graph_path, f'G_ZU9_INT_{coord}.data')
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')

dev = Arch(G)
dev.get_pips_length(coord)
del G
queue = dev.reconstruct_device(l, coord)
a = list(filter(lambda x: re.match(GM.FF_in_pattern, x), dev.G))
a = [Node(f) for f in a]
FFs = set()
FFs.update(Parallel(n_jobs=-1)(delayed(dev.get_nodes)(bel_group=ff.bel_group, bel=ff.bel) for ff in a))

print(len(FFs))
print('--- %s seconds ---' %(time.time() - start_time))
start_time = time.time()
FFs2 = set()
for ff in a:
    FFs2.update(dev.get_nodes(bel_group=ff.bel_group, bel=ff.bel))

print(len(FFs))
print('--- %s seconds ---' %(time.time() - start_time))