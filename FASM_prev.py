from resources.cut import CUT
from resources.path import Path
from resources.primitive import *
from resources.arch_graph import Arch
from resources.edge import Edge
from resources.node import Node
from resources.tile import Tile
from resources.configuration import *
import resources.constraint as const
from Functions import load_data, store_data
import Global_Module as GM
import os, time, re, pickle

start_time = time.time()
#################################################
with open(r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\Compressed Graphs\G_ZU9_INT_X46Y90.data', 'rb') as data:
    G = pickle.load(data)
G = Arch.remove_FF_PIPs(G)
dev = Arch(G)
coord = 'X46Y90'
########### Make CUTs #############
load_path = r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\Store'
store_path = r'C:\Users\t26607bb\Desktop\CPS_Project\New Path Search\Data\FASM'

main_paths = load_data(load_path, 'main_TC.data')
not_paths = load_data(load_path, 'not_TC.data')

prev_block_mode = GM.block_mode
prev_LUT_mode = GM.LUT_Dual
GM.block_mode = 'local'
GM.LUT_Dual = True

used_LUTs = []
TCs = []
for config in zip(main_paths[:3], not_paths[:3]):
    TC = Configuration(dev)
    for idx in range(len(config[0])):
        cut = CUT(coord)
        TC.CUTs.append(cut)
        main_path = Path(dev, config[0][idx], 'main-path', )
        LUTs_func_dict = main_path.LUTs_dict()
        TC.set_LUTs(dev, 'used', LUTs_func_dict)
        cut.paths.add(main_path)

        not_path = Path(dev, config[1][idx], 'not', )
        LUTs_func_dict = not_path.LUTs_dict()
        TC.set_LUTs(dev, 'used', LUTs_func_dict)
        cut.paths.add(not_path)

    used_LUTs.append(LUT.integrate(*TC.get_LUTs(usage='used')))
    TCs.append(TC)

GM.block_mode = prev_block_mode
GM.LUT_Dual = prev_LUT_mode

########### Gen FASM #############
curr_pips = set()
prev_pips = set()
for idx, TC in enumerate(TCs):
    for cut in TC.CUTs:
        for path in cut.paths:
            curr_pips.update(path.pips)

    #reset FASM pips
    prev_FASM_pips = []
    if prev_pips:
        prev_FASM_pips = const.get_pip_FASM(*prev_pips, mode='clear')
    #set FASM pips
    curr_pips_FASM = const.get_pip_FASM(*curr_pips, mode='set')
    #FASM LUTs
    LUTs_FASM = [f'{LUT.tile}.{LUT.bel}.INIT[63:0] = {LUT.init}\n' for LUT in used_LUTs[idx]]

    #write
    file = open(os.path.join(store_path, 'TC{}.fasm'.format(idx)), 'w+')
    file.writelines(prev_FASM_pips + curr_pips_FASM + LUTs_FASM)
    file.close()

    prev_pips = curr_pips.copy()

print('--- %s seconds ---' %(time.time() - start_time))