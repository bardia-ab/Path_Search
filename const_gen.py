import re, os, sys, getopt
from math import ceil
import Global_Module as GM
from relocation.relative_location import DLOC
from resources.constraint import VHDL, Cell, load_data, create_folder, get_instantiation, split_D_CUTs

#Usage: python3 const_gen.py TCs_path TC_file store_path N_Parallel name_prefix [-e] [-o]
################## User Inputs ###################
TCs_path    = sys.argv[1]
TC_file     = sys.argv[2]
store_path  = sys.argv[3]
N_Parallel  = int(sys.argv[4])
name_prefix = sys.argv[5]
#even_odd    = sys.argv[6]
opts, args = getopt.getopt(sys.argv[6:7], "eo")
##################################################
slices_dict = load_data(GM.load_path, 'clb_site_dict2.data')
Cell.cells = []
VHDL_file = VHDL('CUTs', 'behavioral')
VHDL_file.add_package('ieee', 'std_logic_1164')
VHDL_file.add_package('work', 'my_package')
VHDL_file.add_generic('g_N_Segments', 'integer')
VHDL_file.add_generic('g_N_Parallel', 'integer')
VHDL_file.add_port('i_Clk_Launch', 'in', 'std_logic')
VHDL_file.add_port('i_Clk_Sample', 'in', 'std_logic')
VHDL_file.add_port('i_CE', 'in', 'std_logic')
VHDL_file.add_port('i_CLR', 'in', 'std_logic')
VHDL_file.add_port('o_Error', 'out', 'my_array')
VHDL_file.add_signal('w_Error', 'my_array(0 to g_N_Segments - 1)(g_N_Parallel - 1 downto 0)',
                     "(others => (others => '0'))")
VHDL_file.add_assignment('o_Error', 'w_Error')
########################################################
TC = load_data(TCs_path, TC_file)
TC_file = TC_file.split('.')[0]

if not opts:
    D_CUTs = [D_CUT for R_CUT in TC.CUTs for D_CUT in R_CUT.D_CUTs]
elif opts[0][0] == '-e':
    TC_file = f'{TC_file}_even'
    D_CUTs, _ = split_D_CUTs(TC, 'FF_in_index')
elif opts[0][0] == '-o':
    TC_file = f'{TC_file}_odd'
    _, D_CUTs = split_D_CUTs(TC, 'FF_in_index')
else:
    exit()

src_path = os.path.join(store_path, TC_file)
create_folder(src_path)
D_CUTs.sort(key=lambda x: x.index * 10000 + DLOC.get_x_coord(x.origin) * 1000 + DLOC.get_y_coord(x.origin))
########################################################
N_Segments = ceil(len(D_CUTs) / N_Parallel)
N_Partial = len(D_CUTs) % N_Parallel
routing_constraints = []
for idx, D_CUT in enumerate(D_CUTs):
    CUT_idx = idx % N_Parallel
    Seg_idx = idx // N_Parallel
    w_Error_Mux_In = f'w_Error({Seg_idx})({CUT_idx})'

    launch_FF_cell_name = name_prefix.format(idx, 'launch_FF')
    sample_FF_cell_name = name_prefix.format(idx, 'sample_FF')
    not_LUT_cell_name = name_prefix.format(idx, 'not_LUT')
    launch_net = name_prefix.format(idx, 'Q_launch_int')

    D_CUT_cells = Cell.get_D_CUT_cells(TC, slices_dict, D_CUT, True)
    launch_FF = Cell('FF', D_CUT_cells['launch_FF'][0], D_CUT_cells['launch_FF'][1], launch_FF_cell_name)
    sample_FF = Cell('FF', D_CUT_cells['sample_FF'][0], D_CUT_cells['sample_FF'][1], sample_FF_cell_name)
    not_LUT = Cell('LUT', D_CUT_cells['not_LUT'][0], D_CUT_cells['not_LUT'][1], not_LUT_cell_name)
    not_LUT.inputs = D_CUT_cells['not_LUT'][2]

    g_Buffer = D_CUT.get_g_buffer()
    if g_Buffer == "00":
        route_thru_net = None
    else:
        buff_LUT_cell_name = name_prefix.format(idx, 'Buff_Gen.buffer_LUT')
        buffer_LUT = Cell('LUT', D_CUT_cells['buff_LUT'][0][0], D_CUT_cells['buff_LUT'][0][1], buff_LUT_cell_name)
        buffer_LUT.inputs = D_CUT_cells['buff_LUT'][0][2]
        route_thru_net = name_prefix.format(idx, 'Route_Thru')

    VHDL_file.add_components(
        ''.join(get_instantiation(idx, 'i_Clk_Launch', 'i_Clk_Sample', 'i_CE', 'i_CLR', w_Error_Mux_In, g_Buffer)))
    routing_constraints.extend(D_CUT.get_routing_constraint(launch_net, route_thru_net))

cell_constraints = Cell.get_cell_constraints()

with open(os.path.join(src_path, 'stats.txt'), 'w+') as file:
    if N_Partial > 0:
        file.write(f'N_Segments = {N_Segments - 1}\n')
    else:
        file.write(f'N_Segments = {N_Segments}\n')

    file.write(f'N_Partial = {N_Partial}')

with open(os.path.join(src_path, 'physical_constraints.xdc'), 'w+') as file:
    file.writelines(cell_constraints)
    file.write('\n')
    file.writelines(routing_constraints)

VHDL_file.print(os.path.join(src_path, 'CUTs.vhd'))
print(f'{TC_file} is done.')