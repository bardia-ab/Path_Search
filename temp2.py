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
import concurrent.futures

start_time = time.time()
#coord = sys.argv[1]
coord = 'X46Y90'
tile = f'INT_{coord}'
l = 1 if coord == 'X46Y90' else len(os.listdir(GM.store_path)) + 1
################
graph_path = os.path.join(GM.graph_path, f'G_ZU9_INT_{coord}.data')
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')



dev = Arch(G)
dev.get_pips_length(coord)
del G
queue = dev.reconstruct_device(l, coord)
print('\n--- %s seconds ---' %(time.time() - start_time))