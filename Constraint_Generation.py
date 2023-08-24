import os, re, time, math
import networkx as nx
import Global_Module as GM
from Functions import load_data, store_data, extend_dict
from relocation.arch_graph import Arch
from relocation.configuration import Configuration
from relocation.relative_location import RLOC, DLOC
import resources.constraint as const
from resources.constraint import Cell
from resources.edge import Edge
from tqdm import tqdm

start_time = time.time()

N_Parallel = 50
name_prefix = 'design_1_i/top_0/U0/Inst/Multiple_Segments[{}].{}.Multiple_CUT[{}].CUT/{}'
slices_dict = load_data(GM.load_path, 'clb_site_dict2.data')

TCs_path = os.path.join(GM.DLOC_path, 'iter24')
files, Init_TC_file = const.get_Init_TC(TCs_path)
Init_TC = load_data(TCs_path, Init_TC_file)
#########################
'''lut_2 = list(filter(lambda x: len(Init_TC.LUTs[x]) == 2, Init_TC.LUTs))
buff_2 = list(filter(lambda x: Init_TC.LUTs[x][0][1]=='buffer' and Init_TC.LUTs[x][1][1]=='buffer', lut_2))
if buff_2:
    breakpoint()

for key, subLUTs in Init_TC.LUTs.items():
    subLUTs.sort(key=lambda x: 0 if x[1]=='buffer' else 1)
    Init_TC.LUTs[key] = subLUTs'''
########################
a = {lut:Init_TC.LUTs[lut] for lut in Init_TC.LUTs if len(Init_TC.LUTs[lut])>2}
#b = {ff:Init_TC.FFs[ff] for ff in Init_TC.FFs if len(Init_TC.FFs[ff])>2}

D_CUTs = [D_CUT for R_CUT in Init_TC.CUTs for D_CUT in R_CUT.D_CUTs]
D_CUTs.sort(key=lambda x: x.index)
N_Segments = math.ceil(len(D_CUTs) / N_Parallel)
N_Partial = len(D_CUTs) % N_Parallel

routing_constraints = []
cell_constraints = []

for idx, D_CUT in enumerate(D_CUTs):
    if (idx // N_Parallel == N_Segments - 1) and N_Partial > 0:
        segment_type = 'Partial'
    else:
        segment_type = 'Regular'

    CUT_idx = idx % N_Parallel
    Seg_idx = idx // N_Parallel

    launch_FF_cell_name = name_prefix.format(Seg_idx, segment_type, CUT_idx, 'launch_FF')
    sample_FF_cell_name = name_prefix.format(Seg_idx, segment_type, CUT_idx, 'sample_FF')
    not_LUT_cell_name = name_prefix.format(Seg_idx, segment_type, CUT_idx, 'not_LUT')
    launch_net = name_prefix.format(Seg_idx, segment_type, CUT_idx, 'Q_launch_int')


    D_CUT_cells = Cell.get_D_CUT_cells(Init_TC, slices_dict, D_CUT)
    launch_FF = Cell('FF', D_CUT_cells['launch_FF'][0], D_CUT_cells['launch_FF'][1], launch_FF_cell_name)
    sample_FF = Cell('FF', D_CUT_cells['sample_FF'][0], D_CUT_cells['sample_FF'][1], sample_FF_cell_name)
    not_LUT   = Cell('LUT', D_CUT_cells['not_LUT'][0], D_CUT_cells['not_LUT'][1], not_LUT_cell_name)
    not_LUT.inputs = D_CUT_cells['not_LUT'][2]

    routing_constraints.append(f'set_property ROUTE {D_CUT.routing_constraint} [get_nets {launch_net}]\n')

#s_FFs = list(filter(lambda x: x.cell_name.endswith('sample_FF'), Cell.cells))
#s_FFs_tuple = {(c.bel, c.slice) for c in s_FFs}
#l_FFs = list(filter(lambda x: x.cell_name.endswith('launch_FF'), Cell.cells))
#l_FFs_tuple = {(c.bel, c.slice) for c in l_FFs}
cell_constraints = Cell.get_cell_constraints()

with open(os.path.join(GM.Data_path, 'XDC/TC0.xdc'), 'w+') as file:
    file.writelines(cell_constraints)
    file.writelines(routing_constraints)

print(f'N_segments: {N_Segments - 1}')
print(f'N_Partial: {N_Partial}')
print('--- %s seconds ---' %(time.time() - start_time))