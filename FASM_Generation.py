import os, re, time
import networkx as nx
import Global_Module as GM
from Functions import load_data, store_data, extend_dict
from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC
import resources.constraint as const
from resources.edge import Edge

start_time = time.time()

GM.DLOC_path = os.path.join(GM.DLOC_path, 'iter1')
device = Arch('ZCU9')

files = sorted(os.listdir(GM.DLOC_path), key= lambda x: int(re.findall('\d+', x).pop()), reverse=False)
for TC_idx, file in enumerate(files):
    configurations = []
    TC = load_data(GM.DLOC_path, file)
    for R_CUT in TC.CUTs:
        for D_CUT in R_CUT.D_CUTs:
            pips = {Edge(edge) for edge in D_CUT.G.edges() if RLOC.is_pip(edge)}
            configurations.extend(const.get_pip_FASM(*pips))

print(configurations[0])
print(len(configurations))
print('--- %s seconds ---' %(time.time() - start_time))