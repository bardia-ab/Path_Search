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
#################################################
#graph_parh = r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\Compressed Graphs\G_ZU9_INT_X46Y90.data'
graph_path = '/home/bardia/Desktop/bardia/Timing_Characterization/Data/Compressed Graphs/G_ZU9_INT_X46Y90.data'
with open(graph_path, 'rb') as data:
    G = pickle.load(data)
G = Arch.remove_FF_PIPs(G)
dev = Arch(G)
#################################################
#store_path = r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\Store2'
store_path = '/home/bardia/Desktop/bardia/Timing_Characterization/Data/Store2'
create_folder(store_path)
int_tile = dev.get_tiles(type='INT', coordinate=coord).pop()

GM.nodes_dict = get_nodes_dict(dev.G, coord)
queue = list(int_tile.pips)
queue = remove_no_path_pips(dev.G, queue, coord)
TC_idx = 0
while queue:
    TC = Configuration(dev)
    TC.sort_pips(queue)

    while not TC.finish_TC(queue, free_cap=16):
        pip = TC.pick_PIP(queue)
        if not pip:
            continue

        TC.create_CUT(coord, pip)
        try:
            path = path_finder(TC.G, pip[1], 't', weight="weight", dummy_nodes=['t'])
            path1 = Path(dev, TC, path, 'path_out')
            TC.add_path(dev, path1)
        except:
            TC.remove_CUT(dev)
            queue.append(queue.pop(0))
            continue

        TC.unblock_nodes(dev, pip[0])
        try:
            path = path_finder(TC.G, 's', pip[0], weight="weight", dummy_nodes=['s'])
            path1 = Path(dev, TC, path, 'path_in')
            TC.add_path(dev, path1)
        except:
            TC.block_nodes = pip[0]
            TC.remove_CUT(dev)
            queue.append(queue.pop(0))
            continue

        main_path = TC.CUTs[-1].main_path.str_nodes()
        if len(main_path) > 15:
            TC.remove_CUT(dev)
            TC.G.remove_nodes_from(['s2', 't2'])
            queue.append(queue.pop(0))
            continue

        not_LUT_ins = dev.get_nodes(is_i6=False, clb_node_type='LUT_in', bel=path1[0].bel, tile=path1[0].tile)
        for LUT_in in not_LUT_ins:
            TC.G.add_edge(LUT_in.name, 't2', weight=0)

        for node in main_path:
            TC.G.add_edge('s2', node, weight=0)

        try:
            path = path_finder(TC.G, 's2', 't2', weight="weight", dummy_nodes=['s2', 't2'])
            path1 = Path(dev, TC, path, 'not')
            TC.add_path(dev, path1)
        except:
            TC.remove_CUT(dev)
            TC.G.remove_nodes_from(['s2', 't2'])
            queue.append(queue.pop(0))
            continue

        TC.G.remove_nodes_from(['s2', 't2'])
        TC.finalize_CUT(dev)
        queue = [pip for pip in queue if pip not in TC.CUTs[-1].covered_pips]
        print(f'TC{TC_idx}- Found Paths: {len(TC.CUTs)}')
        print(f'Remaining PIPs: {len(queue)}')

    if TC.CUTs:
        vd.check_LUT_utel(TC)
        store_data(store_path, f'TC{TC_idx}.data', TC)
        TC_idx += 1
    else:
        break

print('--- %s seconds ---' %(time.time() - start_time))