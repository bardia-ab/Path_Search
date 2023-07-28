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
covered_pips = set()
errors = []
path_length = []
max_length_pip = (0, None, None)
for TC_idx, file in enumerate(os.listdir(GM.store_path)):
    TC = load_data(GM.store_path, file)
    vd.check_LUT_utel(TC)
    #if not vd.check_collision(TC):
        #errors.append(f'TC{TC_idx}')

    for cut in TC.CUTs:
        covered_pips.update(cut.covered_pips)
        path_in = {path for path in cut.paths if path.path_type=='path_in'}.pop()
        path_out = {path for path in cut.paths if path.path_type == 'path_out'}.pop()
        path_length.append(len(path_in + path_out))
        if len(path_in+path_out) > max_length_pip[0]:
            max_length_pip = (len(path_in+path_out), cut.pip, path_in+path_out)
#covered_pips = {pip.name for pip in covered_pips}
print(len(covered_pips))
print(max(path_length))
print(min(path_length))
print('--- %s seconds ---' %(time.time() - start_time))