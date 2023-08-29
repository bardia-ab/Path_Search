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
from resources.node import Node

#TCs_path = os.path.join(GM.DLOC_path, 'iter45')
TCs_path = os.path.join(GM.Data_path, 'iter53')
TC_files = [file for file in os.listdir(TCs_path) if file.startswith('TC')]
#########################
invalid_TCs = []
for idx, TC_file in enumerate(TC_files):
    print(idx)
    TC = load_data(TCs_path, TC_file)
    result, invalid_keys = vd.check_DCUT_LUT_utel(TC)
    if result:
        invalid_TCs.append(TC_file)

#store_data(GM.Data_path, 'invalid_TCs.data', invalid_TCs)

#invalid_TCs = load_data(GM.Data_path, 'invalid_TCs.data')
removed_DCUTs = {}
for idx, TC_file in enumerate(invalid_TCs):
    removed_DCUTs[TC_file] = []
    TC = load_data(TCs_path, TC_file)
    D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs]
    LUTs_dict = {}
    for key, subLUTs in TC.LUTs.items():
        LUTs_dict[key] = 0
        for subLUT in subLUTs:
            usage = 2 if re.match(GM.LUT_in6_pattern, subLUT[0]) else 1
            LUTs_dict[key] += usage

    invalid_keys = {k: TC.LUTs[k] for k, v in LUTs_dict.items() if v > 2}
    for key in invalid_keys:
        subluts = TC.LUTs[key]
        inputs = [sublut[0] for sublut in subluts]
        newer_D_CUT_idx = -1
        newer_D_CUT = None
        for input in inputs:
            corsp_DCUT = {DCUT for DCUT in D_CUTs if input in DCUT.G}.pop()
            if corsp_DCUT.index >= newer_D_CUT_idx:
                newer_D_CUT_idx = corsp_DCUT.index
                newer_D_CUT = copy.deepcopy((corsp_DCUT))


        R_CUT_idx = {TC.CUTs.index(RCUT) for RCUT in TC.CUTs if RCUT.index == newer_D_CUT_idx}.pop()
        D_CUT = {DCUT for DCUT in TC.CUTs[R_CUT_idx].D_CUTs if DCUT.origin == newer_D_CUT.origin and DCUT.index == newer_D_CUT.index}.pop()
        TC.CUTs[R_CUT_idx].D_CUTs.remove(D_CUT)

        for function, LUT_ins in D_CUT.LUTs_func_dict.items():
            for LUT_in in LUT_ins:
                lut_key = LUT_in.bel_key
                s_lut ={lut for lut in TC.LUTs[lut_key] if LUT_in.name == lut[0]}.pop()
                TC.LUTs[lut_key].remove(s_lut)

        for ff in D_CUT.FFs_set:
            del TC.FFs[ff]

    print(idx)
    store_data(TCs_path, TC_file, TC)

#store_data(GM.Data_path, 'removed_DCUTs.data', removed_DCUTs)

'''pips = set()
pbar = tqdm(total=len(TC_files))
for idx, TC_file in enumerate(TC_files):
    pbar.set_description(f'{TC_file}')
    TC = load_data(TCs_path, TC_file)
    for R_CUT in TC.CUTs:
        for D_CUT in R_CUT.D_CUTs:
            pips.update(edge for edge in D_CUT.G.edges() if D_CUT.G.get_edge_data(*edge)['path_type'] == 'main_path' and D_CUT.is_pip(edge))

    pbar.update(1)

pips = set(filter(lambda x: x[0].startswith('INT') and 38 <= D_CUT.get_x_coord(x[0]) <= 51 and 60 <= D_CUT.get_y_coord(x[0]) <= 119, pips))
print(len(pips))'''

'''pbar = tqdm(total=len(TC_files))

for idx, TC_file in enumerate(TC_files):
    LUTs = {}
    pbar.set_description(f'{TC_file}')
    TC = load_data(TCs_path, TC_file)
    for R_CUT in TC.CUTs:
        for D_CUT in R_CUT.D_CUTs:
            LUT_ins = set(filter(lambda x: re.match(GM.LUT_in_pattern, x), D_CUT.G))
            for LUT_in in LUT_ins:
                key = Node(LUT_in).bel_key
                usage = 2 if re.match(GM.LUT_in6_pattern, LUT_in) else 1

                if key not in LUTs:
                    LUTs[key] = usage
                else:
                    LUTs[key] += usage

    if {key for key, usage in LUTs.items() if usage > 2}:
        breakpoint()

    pbar.update(1)'''

#removed_DCUTs = load_data(GM.Data_path, 'removed_DCUTs.data')
#print(len({v for k,vs in removed_DCUTs.items() for v in vs}))
