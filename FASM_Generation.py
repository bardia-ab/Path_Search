import os, re, time
import networkx as nx
import Global_Module as GM
from Functions import load_data, store_data, extend_dict, get_tile ,get_port, get_occupied_pips2
from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC
import resources.constraint as const
from resources.edge import Edge
from tqdm import tqdm

start_time = time.time()

GM.DLOC_path = os.path.join(GM.DLOC_path, 'iter1')
device = Arch('ZCU9')

pips_file = os.path.join(GM.load_path, 'used_pips.txt')
device.used_pips = get_occupied_pips2(pips_file)
device.used_nodes = {}
for key in device.used_pips:
    device.used_nodes[key] = {node for pip in device.used_pips[key] for node in pip}

files = [file for file in os.listdir(GM.DLOC_path) if file.startswith('TC')]
files = sorted(files, key= lambda x: int(re.findall('\d+', x).pop()), reverse=False)
pbar = tqdm(total=len(files))

for TC_idx, file in enumerate(files):
    configurations = set()
    TC = load_data(GM.DLOC_path, file)
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