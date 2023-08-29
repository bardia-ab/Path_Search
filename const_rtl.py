import copy
import os, re, time, math
import networkx as nx
import Global_Module as GM
from Functions import load_data, store_data, extend_dict, create_folder
from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import resources.constraint as const
from resources.constraint import Cell
from resources.edge import Edge
from tqdm import tqdm
from joblib import Parallel, delayed
from resources.rtl import *
import resources.validation as vd

start_time = time.time()

N_Parallel = 50
name_prefix = 'design_1_i/top_0/U0/Inst/CUTs_Inst/CUT_{}/{}'
slices_dict = load_data(GM.load_path, 'clb_site_dict2.data')
##############################################################
TCs_path = os.path.join(GM.DLOC_path, 'iter45')
TC_files = [file for file in os.listdir(TCs_path) if file.startswith('TC')]
create_folder(os.path.join(GM.Data_path, 'Vivado_Sources'))
#########################

#const.gen_rtl('TC187.data', TCs_path, N_Parallel, name_prefix, slices_dict)
Parallel(n_jobs=-1)(delayed(const.gen_rtl)(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict) for TC_file in TC_files)
'''pbar = tqdm(total=len(TC_files))
for TC_file in TC_files:
    pbar.set_description(f'{TC_file}')
    const.gen_rtl(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict)
    pbar.update(1)'''

#print(f'N_segments: {N_Segments - 1}')
#print(f'N_Partial: {N_Partial}')
print('--- %s seconds ---' %(time.time() - start_time))