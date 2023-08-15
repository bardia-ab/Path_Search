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

GM.DLOC_path = os.path.join(GM.DLOC_path, 'iter1')
file = 'TC0.data'
TC = load_data(GM.DLOC_path, file)

#a = {lut:TC.LUTs[lut] for lut in TC.LUTs if len(TC.LUTs[lut])>2}
#b = {ff:TC.FFs[ff] for ff in TC.FFs if len(TC.FFs[ff])>2}

D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs]
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


    D_CUT_cells = const.get_D_CUT_cells(TC, slices_dict, D_CUT)
    launch_FF = Cell('FF', D_CUT_cells['launch_FF'][0], D_CUT_cells['launch_FF'][1], launch_FF_cell_name)
    sample_FF = Cell('FF', D_CUT_cells['sample_FF'][0], D_CUT_cells['sample_FF'][1], sample_FF_cell_name)
    not_LUT   = Cell('LUT', D_CUT_cells['not_LUT'][0], D_CUT_cells['not_LUT'][1], not_LUT_cell_name)
    not_LUT.inputs = D_CUT_cells['not_LUT'][2]

    routing_constraints.append(f'set_property ROUTE {D_CUT.routing_constraint} [get_nets {launch_net}]\n')

cell_constraints = Cell.get_cell_constraints()

with open(os.path.join(GM.Data_path, 'XDC/TC0.xdc'), 'w+') as file:
    file.writelines(cell_constraints)
    file.writelines(routing_constraints)

print(f'N_segments: {N_Segments - 1}')
print(f'N_Partial: {N_Partial}')
print('--- %s seconds ---' %(time.time() - start_time))