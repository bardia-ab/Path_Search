import os, re, time
import networkx as nx
import Global_Module as GM
from Functions import load_data, store_data, extend_dict, get_tile ,get_port
from relocation.arch_graph import Arch
from relocation.clock_region import CR
from relocation.configuration import Configuration
from relocation.relative_location import RLOC
import resources.constraint as const
from resources.edge import Edge
from tqdm import tqdm
from joblib import Parallel, delayed

start_time = time.time()

device = Arch('ZCU9')
device.dummy = {}
cr = device.get_CRs(name = 'X2Y1').pop()
INTs = device.limit(38, 51, 60, 119)

TCs_path = os.path.join(GM.DLOC_path, 'iter24')
files, Init_TC_file = const.get_Init_TC(TCs_path)
#################### Initialize occupied_pips dicts
pips_file = os.path.join(GM.load_path, 'used_pips.txt')
device.set_used_pips_nodes_dict(pips_file)
launch_clk_file = os.path.join(GM.load_path, 'launch_clk.txt')
sample_clk_file = os.path.join(GM.load_path, 'sample_clk.txt')
device.set_clk_dicts(launch_clk_file, 'launch')
device.set_clk_dicts(sample_clk_file, 'sample')
################## Init_TC_Dynamic_PIPs
Init_used_pips_dict, Init_used_nodes_dict = const.get_Init_used_pips_nodes_dict(device, TCs_path, Init_TC_file)

for key in device.used_pips_dict:
    if key in Init_used_pips_dict:
        device.used_pips_dict[key] = device.used_pips_dict[key] - Init_used_pips_dict[key]

for key in device.used_nodes_dict:
    if key in Init_used_nodes_dict:
        device.used_nodes_dict[key] = device.used_nodes_dict[key] - Init_used_nodes_dict[key]
##################################################
pbar = tqdm(total=len(files))

for TC_idx, file in enumerate(files):
    configurations = set()
    TC = load_data(TCs_path, file)
    for R_CUT in TC.CUTs:
        for D_CUT in R_CUT.D_CUTs:
            pips = {Edge(edge) for edge in D_CUT.G.edges() if RLOC.is_pip(edge)}
            configurations.update(const.get_pip_FASM(*pips))
            pbar.set_description(f'TC{TC_idx} >> CUT{D_CUT.index}')

    configurations.update(const.get_FFs_FASM(device, TC))
    configurations.update(const.get_LUTs_FASM(TC.LUTs))
    pbar.update(1)

#print(configurations[0])
print(len(configurations))
print('--- %s seconds ---' %(time.time() - start_time))