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
'''VHDL_file = VHDL('CUTs', 'behavioral')
VHDL_file.add_package('ieee', 'std_logic_1164')
VHDL_file.add_package('work', 'my_package')
VHDL_file.add_generic('g_N_Segments', 'integer')
VHDL_file.add_generic('g_N_Parallel', 'integer')
VHDL_file.add_port('i_Clk_Launch', 'in', 'std_logic')
VHDL_file.add_port('i_Clk_Sample', 'in', 'std_logic')
VHDL_file.add_port('i_CE', 'in', 'std_logic')
VHDL_file.add_port('i_CLR', 'in', 'std_logic')
VHDL_file.add_port('o_Error', 'out', 'my_array')
VHDL_file.add_signal('w_Error', 'my_array(0 to g_N_Segments - 1)(g_N_Parallel - 1 downto 0)', "(others => (others => '0'))")
VHDL_file.add_assignment('o_Error', 'w_Error')'''


TCs_path = os.path.join(GM.DLOC_path, 'iter52')
TC_files = [file for file in os.listdir(TCs_path) if file.startswith('TC')]
#create_folder(os.path.join(GM.Data_path, 'Vivado_Sources'))
#########################
invalid_TCs = []
for TC_file in TC_files:
    TC = load_data(TCs_path, TC_file)
    if not vd.check_DCUT_LUT_utel(TC):
        invalid_TCs.append(TC_file)

'''D_CUTs = [D_CUT for R_CUT in Init_TC.CUTs for D_CUT in R_CUT.D_CUTs]
D_CUTs.sort(key=lambda x: x.index * 10000 + DLOC.get_x_coord(x.origin) * 1000 + DLOC.get_y_coord(x.origin))
N_Segments = math.ceil(len(D_CUTs) / N_Parallel)
N_Partial = len(D_CUTs) % N_Parallel

routing_constraints = []
cell_constraints = []

pbar = tqdm(total=len(D_CUTs))
for idx, D_CUT in enumerate(D_CUTs):
    CUT_idx = idx % N_Parallel
    Seg_idx = idx // N_Parallel
    w_Error_Mux_In = f'w_Error({Seg_idx})({CUT_idx})'
    LUT_ins = list(filter(lambda x: re.match(GM.LUT_in_pattern, x), D_CUT.G))

    launch_FF_cell_name = name_prefix.format(idx, 'launch_FF')
    sample_FF_cell_name = name_prefix.format(idx, 'sample_FF')
    not_LUT_cell_name = name_prefix.format(idx, 'not_LUT')
    launch_net = name_prefix.format(idx, 'Q_launch_int')

    D_CUT_cells = Cell.get_D_CUT_cells(Init_TC, slices_dict, D_CUT, True)
    launch_FF = Cell('FF', D_CUT_cells['launch_FF'][0], D_CUT_cells['launch_FF'][1], launch_FF_cell_name)
    sample_FF = Cell('FF', D_CUT_cells['sample_FF'][0], D_CUT_cells['sample_FF'][1], sample_FF_cell_name)
    not_LUT = Cell('LUT', D_CUT_cells['not_LUT'][0], D_CUT_cells['not_LUT'][1], not_LUT_cell_name)
    not_LUT.inputs = D_CUT_cells['not_LUT'][2]

    g_Buffer = D_CUT.get_g_buffer()
    if g_Buffer[0] == '1':
        buff_LUT_cell_name = name_prefix.format(idx, 'Buff_Gen.buffer_LUT')
        buffer_LUT = Cell('LUT', D_CUT_cells['buff_LUT'][0][0], D_CUT_cells['buff_LUT'][0][1], buff_LUT_cell_name)
        buffer_LUT.inputs = D_CUT_cells['buff_LUT'][0][2]
        route_thru_net = name_prefix.format(idx, 'Route_Thru')
    else:
        route_thru_net = None


    VHDL_file.add_components(''.join(get_instantiation(idx, 'i_Clk_Launch', 'i_Clk_Sample', 'i_CE', 'i_CLR', w_Error_Mux_In, g_Buffer)))
    routing_constraints.extend(D_CUT.get_routing_constraint(launch_net, route_thru_net))
    pbar.update(1)



cell_constraints = Cell.get_cell_constraints()

with open(os.path.join(GM.Data_path, 'XDC/TC0.xdc'), 'w+') as file:
    file.writelines(cell_constraints)
    file.writelines(routing_constraints)

VHDL_file.print(os.path.join(GM.Data_path, 'XDC/CUTs.vhd'))
#with open(os.path.join(GM.Data_path, 'XDC/CUTs.txt'), 'w+') as file:
    #file.writelines(components)'''
#const.gen_rtl('TC187.data', TCs_path, N_Parallel, name_prefix, slices_dict)
#Parallel(n_jobs=-1)(delayed(const.gen_rtl)(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict) for TC_file in TC_files)
'''pbar = tqdm(total=len(TC_files))
for TC_file in TC_files:
    pbar.set_description(f'{TC_file}')
    const.gen_rtl(TC_file, TCs_path, N_Parallel, name_prefix, slices_dict)
    pbar.update(1)'''

#print(f'N_segments: {N_Segments - 1}')
#print(f'N_Partial: {N_Partial}')
print('--- %s seconds ---' %(time.time() - start_time))