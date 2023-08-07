import time, re, os, pickle
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
################################
G = load_data(GM.graph_path, f'G_ZU9_INT_{coord}.data')
dev = Arch(G)
dev.get_pips_length(coord)
queue = list(GM.pips_length_dict)
################################
if coord == 'X46Y90':
    GM.store_path = os.path.join(GM.store_path, 'iter1')
else:
    l = len(os.listdir(GM.store_path))
    GM.store_path = os.path.join(GM.store_path, f'iter{l}')

covered_pips = set()
errors = []
path_length = []
max_length_pip = (0, None, None)
spare_pips = set()
files = sorted(os.listdir(GM.store_path), key= lambda x: int(re.findall('\d+', x).pop()), reverse=False)
for TC_idx, file in enumerate(files):
    print(f'TC{TC_idx}')
    TC = load_data(GM.store_path, file)
    vd.check_LUT_utel(TC)
    #if not vd.check_collision(TC):
        #errors.append(f'TC{TC_idx}')

    for cut in TC.CUTs:
        if TC_idx >= 150:
            spare_pips.update(cut.covered_pips)
            continue

        covered_pips.update(cut.covered_pips)
        path_length.append(len(cut.main_path))
        if len(cut.main_path) > max_length_pip[0]:
            max_length_pip = (len(cut.main_path), cut.pip.name, cut.main_path)
#covered_pips = {pip.name for pip in covered_pips}
remaining_pips = set(queue) - covered_pips
store_data(GM.Data_path, 'remaining_pips.data', remaining_pips - spare_pips)
store_data(GM.Data_path, 'spare_pips.data')
print(len(covered_pips))
print(max(path_length))
print(min(path_length))
print('--- %s seconds ---' %(time.time() - start_time))